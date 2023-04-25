from pathlib import Path
import os

from package import Package
from module import get_module_name, get_module_version


def _create_build_file_content(package: Package):
    dep_targets = []
    for dep in package.deps:
        module_name = get_module_name(name=dep.name, arch=dep.arch)
        dep_targets.append(f""""@{module_name}//:all_files",""")

    data_str = "\n      ".join(dep_targets)
    files_str = "\n      ".join(
        ['"' + os.fspath(file) + '",' for file in package.elf_files.union(package.nonelf_files)])

    file_group = f"""
filegroup(
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
])
"""

    return f"""
{file_group}

{exports_files}

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
                f"""bazel_dep(name = "{module_name}", version = "{module_version}")""")
        bazel_deps = "\n" + "\n".join(bazel_dep_list) + "\n"

    return f"""module(
    name = \"{get_module_name(name=package.name, arch=package.arch)}\",
    version = \"{get_module_version(package.version)}\",
    compatibility_level = {package.compatibility_level},
)
{bazel_deps}"""


def write_file(content: str, file: Path):
    "Writes content in a MODULE.bazel file declaring the package as a module and listing its bazel_deps"
    with open(file, "w") as file_to_write:
        file_to_write.write(content)


def write_module_file(package: Package, file: Path):
    "Writes a MODULE.bazel file declaring the package as a module and listing its bazel_deps"
    write_file(_create_module_file_content(package), file)


def write_build_file(package: Package, file: Path):
    "Writes a BUILD file exporting the list of files"
    write_file(_create_build_file_content(package), file)
