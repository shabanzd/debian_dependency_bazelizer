from pathlib import Path
from typing import Any, Dict, Final

import json
import base64
import hashlib

from src.package import Package
from src.module import get_module_name, get_module_version

LINUX_PLATFORM: Final = "@platforms//os:linux"
X86_64_CPU: Final = "@platforms//cpu:x86_64"
BUILD_FILE: Final = Path("BUILD")
MODULE_DOT_BAZEL: Final = Path("MODULE.bazel")
NAME_DOT_TXT: Final = "name.txt"
VERSION_DOT_TXT: Final = "version.txt"

def _get_integrity_for_file(debian_module_tar: Path):
    with debian_module_tar.open("rb") as f:
        files_content = f.read()
    hash = hashlib.sha256(files_content).digest()
    hash_base64 = base64.b64encode(hash).decode()
    return f"sha256-{hash_base64}"


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

def _create_http_archive_text(
    name: str, build_file: str, integrity: str, prefix: str, url: str 
):
    return f"""http_archive(
    name = "{name}",
    build_file = "{build_file}",
    integrity = "{integrity}",
    strip_prefix = "{prefix}",
    url = "{url}",
)
"""


def write_module_file(package: Package):
    "Writes a MODULE.bazel file declaring the package as a module and listing its bazel_deps"
    file = Path(package.package_dir / MODULE_DOT_BAZEL)
    file.write_text(_create_module_file_content(package))


def write_build_file(package: Package):
    "Writes a BUILD file exporting the list of files"
    if package.detached_mode_metadata:
        file = Path(package.detached_mode_metadata.build_files_dir / package.module_name / f"{package.module_name}.BUILD")
    else:
        file = Path(package.package_dir / BUILD_FILE)

    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(_create_build_file_content(package))


def write_python_path_file(rpaths: Dict[str, str], file: Path):
    "Writes a python file exposing the paths of ELF files"
    full_rpaths = {key: "../" + value + "/" + key for key, value in rpaths.items()}
    file.write_text(_create_paths_python_file_content(full_rpaths))



def write_cpp_path_file(rpaths: Dict[str, str], package_name: str, file: Path):
    "Writes a python file exposing the paths of ELF files"
    full_rpaths = {key: "../" + value + "/" + key for key, value in rpaths.items()}
    file.write_text(_create_paths_cpp_file_content(full_rpaths, package_name))



def json_dump(json_file: Path, obj: Dict[Any, Any], sort_keys=True):
    "Dumps json content into json file"
    json_file.write_text(json.dumps(obj, indent=4, sort_keys=sort_keys) + "\n")

def write_http_archive(package: Package, debian_module_tar: Path):
    "Writes a http_archive file for the debian module"
    if not package.detached_mode_metadata:
        return

    file = package.detached_mode_metadata.archives_file 
    file.parent.mkdir(parents=True, exist_ok=True)
    content = file.read_text() if file.exists() else ""
    if not content:
        content = '''"""This file was generated automatically by the debian dependency bazerlizer.
"""

http_archive = use_repo_rule("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

'''

    file.write_text(content + _create_http_archive_text(
        name=get_module_name(name=package.name, arch=package.arch),
        prefix=package.prefix,
        url=f"{package.detached_mode_metadata.url_prefix}/{str(debian_module_tar)}",
        integrity=_get_integrity_for_file(debian_module_tar),
        build_file=f"{str(package.detached_mode_metadata.build_file_package)}:{package.module_name}/{package.module_name}.BUILD",
    ) + "\n")

def write_name_txt_file(package: Package):
    if not package.detached_mode_metadata:
        return
    file = Path(package.detached_mode_metadata.build_files_dir / package.module_name / NAME_DOT_TXT)
    file.write_text(f"{package.name}\n")

def write_version_txt_file(package: Package):
    if not package.detached_mode_metadata:
        return
    file = Path(package.detached_mode_metadata.build_files_dir / package.module_name / VERSION_DOT_TXT)
    file.write_text(f"{package.version}\n")