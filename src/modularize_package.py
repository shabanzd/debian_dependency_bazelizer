from typing import Dict, Final, Set
from pathlib import Path

import os
import shutil
import subprocess

from module import Module
from package import Package, PackageMetadata
from registry import add_package_to_registry
from writers import write_build_file, write_module_file


PATCHELF_PROGRAM: Final = (
    Path()
    .joinpath("..", "patchelf_amd64~0.10-2build1", "usr", "bin", "patchelf")
    .resolve()
)
BUILD_FILE: Final = Path("BUILD")
MODULE_DOT_BAZEL: Final = Path("MODULE.bazel")
BAZEL_WORKSPACE_DIR: Final = os.environ["BUILD_WORKSPACE_DIRECTORY"]
MODULES_DIR : Final = Path().joinpath(BAZEL_WORKSPACE_DIR, "modules")

def _get_dep_rpath_set(rpaths: Set[str], prefix: str):
    rpath_set: Set[str] = set()

    for rpath in rpaths:
        rpath_str = prefix + os.fspath(rpath)
        rpath_set.add(rpath_str)

    return rpath_set


def _concatentate_rpaths(
    package: Package, prefix: str, processed_packages: Dict[PackageMetadata, Package]
):
    rpath_set: Set[str] = set()

    _get_dep_rpath_set(package.rpaths, prefix)

    if not package.deps:
        return rpath_set

    for dep in package.deps:
        if dep not in processed_packages:
            raise ValueError(
                f"dependency: {dep.name} has not been processed. Dependencies must be processed in a topoligcal order"
            )
        rpath_set.update(_get_dep_rpath_set(processed_packages[dep].rpaths, prefix))

    return rpath_set


def _rpath_patch_elf_files(
    package: Package, modules: Dict[PackageMetadata, Module]
):
    for file in package.elf_files:
        rpath_prefix = "$ORIGIN" + "..".join(["/"] * (os.fspath(file).count("/") + 2))
        rpaths_set = _concatentate_rpaths(package, rpath_prefix, modules)
        rpaths_set.add("$ORIGIN")
        subprocess.run(
            [
                "patchelf",
                "--force-rpath",
                "--set-rpath",
                ":".join(rpaths_set),
                Path(package.package_dir / file),
            ],
            check=True,
            stderr=subprocess.STDOUT,
        )



def _repackage_deb_package(package: Package):
    # create empty WORKSPACE file
    Path(package.package_dir / Path("WORKSPACE")).touch()
    write_build_file(package, Path(package.package_dir / BUILD_FILE))
    write_module_file(
        package, Path(package.package_dir / MODULE_DOT_BAZEL)
    )

def modularize_package(package: Package, modules: Dict[PackageMetadata, Module]):
    """Turns package into a module and adds it to local registry."""
    _rpath_patch_elf_files(package=package, modules=modules)
    _repackage_deb_package(package=package)
    add_package_to_registry(package=package)
    shutil.move(str(package.package_dir), str(MODULES_DIR))
