from pathlib import Path
from typing import Any, Dict, Final

import json

from src.package import Package
from src.module import get_module_name, get_module_version

LINUX_PLATFORM: Final = "@platforms//os:linux"
X86_64_CPU: Final = "@platforms//cpu:x86_64"


def _create_filegroup_content(package: Package):
    "Creates a filegroup content out of a debian package object"
    if package.arch != "amd64":
        raise ValueError("Only amd64 architecture is supported for now")

    file_group_content = """filegroup(
    name = "all_files",
    srcs = glob(["**"]),"""

    if package.deps:
        file_group_content += "\n    data = [\n"
        for dep in package.deps:
            file_group_content += f"""      "@{get_module_name(name=dep.name, arch=dep.arch)}//:all_files",\n"""
        file_group_content += "    ],"

    if package.tags:
        file_group_content += f"\n    tags = [{', '.join(package.tags)}],"

    file_group_content += '\n    visibility = ["//visibility:public"],\n)'

    return file_group_content


def _create_build_file_content(package: Package):
    "Creates the BUILD file content out of a debian package object"
    if package.arch != "amd64":
        raise ValueError("Only amd64 architecture is supported for now")

    file_group_content = _create_filegroup_content(package)
    tags_str = "[]" if not package.tags else f"[{', '.join(package.tags)}]"

    return f"""load("@rules_cc//cc:defs.bzl", "cc_library")
load("@rules_python//python:defs.bzl", "py_library")

{file_group_content}

exports_files(glob(["**"]))

py_library(
    name = "{package.module_name}_paths_py",
    srcs = ["{package.module_name}_paths.py"],
    data = [":all_files"],
    target_compatible_with = [
        "{LINUX_PLATFORM}",
        "{X86_64_CPU}",
    ],
    tags = {tags_str},
    visibility = ["//visibility:public"],
)

cc_library(
    name = "{package.module_name}_paths_cc",
    hdrs = ["{package.module_name}_paths.hh"],
    data = [":all_files"],
    target_compatible_with = [
        "{LINUX_PLATFORM}",
        "{X86_64_CPU}",
    ],
    tags = {tags_str},
    visibility = ["//visibility:public"],
)

"""


def _create_module_file_content(package: Package):
    "Creates the module text out of a dabian package object"
    if not package.name:
        raise ValueError("can't create module for a package without a name")

    if not get_module_version(package.version):
        raise ValueError("can't create module for a package without a version")

    bazel_dep_list = [
        """bazel_dep(name = "rules_cc", version = "0.0.9")""",
        """bazel_dep(name = "platforms", version = "0.0.6")""",
    ]
    for dep in package.deps:
        module_name = get_module_name(name=dep.name, arch=dep.arch)
        module_version = get_module_version(dep.version)
        bazel_dep_list.append(
            f"""bazel_dep(name = "{module_name}", version = "{module_version}")"""
        )

    bazel_deps = "\n" + "\n".join(bazel_dep_list) + "\n"

    return f"""module(
    name = \"{get_module_name(name=package.name, arch=package.arch)}\",
    version = \"{get_module_version(package.version)}\",
    compatibility_level = {package.compatibility_level},
)
{bazel_deps}"""


def _create_paths_python_file_content(rpaths: Dict[str, str]):
    rpaths_str = str(rpaths)
    return f"""def paths():
    "Returns a dict of ELF files mapped to their relative location in the runfiles."
    return {rpaths_str}

"""


def _get_cpp_map_from_python_dict(python_dict: Dict[str, str]):
    s = "{"
    for item in python_dict.items():
        s = f'{s}{{"{item[0]}", "{item[1]}"}}, '

    return s[:-2] + "}"


def _create_paths_cpp_file_content(rpaths: Dict[str, str], package_name: str):
    map_str = _get_cpp_map_from_python_dict(rpaths)
    return f"""
#pragma once

#include <map>
#include <string>

namespace {package_name}_paths
{{
/// Returns the paths of executables in {package_name}_paths.
inline std::map<std::string, std::string> paths()
{{
    return {map_str};
}}
}}

"""


def write_file(content: str, file: Path):
    "Writes a file content"
    with open(file, "w") as file_to_write:
        file_to_write.write(content)


def write_module_file(package: Package, file: Path):
    "Writes a MODULE.bazel file declaring the package as a module and listing its bazel_deps"
    write_file(_create_module_file_content(package), file)


def write_build_file(package: Package, file: Path):
    "Writes a BUILD file exporting the list of files"
    write_file(_create_build_file_content(package), file)


def write_python_path_file(rpaths: Dict[str, str], file: Path):
    "Writes a python file exposing the paths of ELF files"
    full_rpaths = {key: "../" + value + "/" + key for key, value in rpaths.items()}
    write_file(_create_paths_python_file_content(full_rpaths), file)


def write_cpp_path_file(rpaths: Dict[str, str], package_name: str, file: Path):
    "Writes a python file exposing the paths of ELF files"
    full_rpaths = {key: "../" + value + "/" + key for key, value in rpaths.items()}
    write_file(_create_paths_cpp_file_content(full_rpaths, package_name), file)


def json_dump(json_file: Path, obj: Dict[Any, Any], sort_keys=True):
    "Dumps json content into json file"
    with open(file=json_file, mode="w", encoding="utf-8") as file:
        json.dump(obj, file, indent=4, sort_keys=sort_keys)
        file.write("\n")
