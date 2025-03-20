from typing import Dict, Final, Set
from pathlib import Path

import os
import subprocess
import tarfile
import shutil

from src.module import Module
from src.package import Package, PackageMetadata
from src.writers import (
    write_build_file,
    write_module_file,
    write_python_path_file,
    write_cpp_path_file,
    json_dump,
    write_http_archive,
    write_name_txt_file,
    write_version_txt_file,
)

RPATHS_DOT_JSON: Final = Path("rpaths.json")
UPLOAD_BUCKET: Final = "upload_bucket"
UPLOAD_URL: Final = "upload_url"
PREFIX: Final = "prefix"
DOWNLOAD_URL: Final = "download_url"


def _get_dep_rpath_set(rpaths: Set[str], prefix: str) -> Set[str]:
    return {prefix + rpath for rpath in rpaths}


def _concatentate_rpaths(
    package: Package, prefix: str, processed_packages: Dict[PackageMetadata, Module]
):
    rpath_set: Set[str] = set()

    if not package.deps:
        return rpath_set

    for dep in package.deps:
        if dep not in processed_packages:
            raise ValueError(
                f"dependency: {dep.name} has not been processed. Dependencies must be processed in a topoligcal order"
            )
        rpath_set.update(
            _get_dep_rpath_set(set(processed_packages[dep].rpaths.values()), prefix)
        )

    return rpath_set


def _rpath_patch_elf_files(package: Package, modules: Dict[PackageMetadata, Module]):
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


def _repackage_deb_package(package: Package) -> Path:
    # create empty WORKSPACE file
    Path(package.package_dir / Path("WORKSPACE")).touch()
    write_build_file(package)
    write_module_file(package)
    write_python_path_file(
        package.rpaths, package.package_dir / Path(package.module_name + "_paths.py")
    )
    write_cpp_path_file(
        package.rpaths,
        package.name,
        package.package_dir / Path(package.module_name + "_paths.hh"),
    )
    json_dump(package.package_dir / RPATHS_DOT_JSON, package.rpaths)
    write_version_txt_file(package)
    write_name_txt_file(package)
    debian_module_tar = Path(package.prefix_version + ".tar.gz")
    # repackage Debian Module as a tarball.
    with tarfile.open(debian_module_tar, "w:gz") as tar:
        tar.add(package.package_dir.relative_to(Path(".").resolve()))
    write_http_archive(package, debian_module_tar)

    return debian_module_tar


def modularize_package(
    package: Package, modules: Dict[PackageMetadata, Module], modules_path: Path
):
    """Turns package into a module."""
    _rpath_patch_elf_files(package=package, modules=modules)
    module_tar = _repackage_deb_package(package)
    modules_path.mkdir(exist_ok=True, parents=True)
    shutil.copy(module_tar, modules_path / module_tar.name)

    module_tar.unlink()
