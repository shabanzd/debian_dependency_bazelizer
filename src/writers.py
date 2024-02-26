from pathlib import Path
from typing import Any, Dict, Final

import json
import os

from src.package import Package
from src.module import get_module_name, get_module_version

RPATHS_DOT_JSON: Final = "rpaths.json"

def _create_build_file_content(package: Package):
    dep_targets = []
    for dep in package.deps:
        module_name = get_module_name(name=dep.name, arch=dep.arch)
        dep_targets.append(f""""@{module_name}//:all_files",""")

    data_str = "\n      ".join(dep_targets)
    files_str = "\n      ".join(
        [
            '"' + os.fspath(file) + '",'
            for file in package.elf_files.union(package.nonelf_files)
        ]
    )

    file_group = f"""filegroup(
    name = "all_files",
    srcs = [
      {files_str}
    ],
    data = [
      {data_str}
    ],
    visibility = ["//visibility:public"],
)"""
    exports_files = f"""
exports_files([
    {files_str}
    "{RPATHS_DOT_JSON}",
])
"""

    return f"""{file_group}

{exports_files}

py_library(
    name = "{package.module_name}_paths_py",
    srcs = ["{package.module_name}_paths.py"],
    data = [":all_files"],
    visibility = ["//visibility:public"],
)

cc_library(
    name = "{package.module_name}_paths_cc",
    hdrs = ["{package.module_name}_paths.hh"],
    data = [":all_files"],
    visibility = ["//visibility:public"],
)

"""


def _create_module_file_content(package: Package):
    "Creates the module text out of a dabian package object"
    if not package.name:
        raise ValueError("can't create module for a package without a name")

    if not get_module_version(package.version):
        raise ValueError("can't create module for a package without a version")

    bazel_deps = ""

    if package.deps:
        bazel_dep_list = []
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
        s = f"{s}{{\"{item[0]}\", \"{item[1]}\"}}, "

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
