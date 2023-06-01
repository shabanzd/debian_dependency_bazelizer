from typing import Dict, Final, Set
from pathlib import Path

import boto3
import os
import subprocess
import tarfile

from src.module import Module
from src.package import Package, PackageMetadata
from src.registry import add_package_to_registry
from src.writers import write_build_file, write_module_file

BUILD_FILE: Final = Path("BUILD")
MODULE_DOT_BAZEL: Final = Path("MODULE.bazel")
UPLOAD_BUCKET: Final = "upload_bucket"
UPLOAD_URL: Final = "upload_url"
PREFIX: Final = "prefix"
DOWNLOAD_URL: Final = "download_url"

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


def _upload_archive_to_s3_bucket(file: Path, s3_config: Dict[str, str]):
    client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=s3_config[UPLOAD_URL],
        verify=False,
    )

    file_str = os.fspath(file)
    upload_file_key = file_str
    
    if PREFIX in s3_config:
        upload_file_key = f"{s3_config[PREFIX]}/" + file_str

    client.upload_file(file_str, s3_config[UPLOAD_BUCKET], upload_file_key)

def _repackage_deb_package(package: Package):
    # create empty WORKSPACE file
    Path(package.package_dir / Path("WORKSPACE")).touch()
    write_build_file(package, Path(package.package_dir / BUILD_FILE))
    write_module_file(package, Path(package.package_dir / MODULE_DOT_BAZEL))
    debian_module_tar = Path(package.prefix + ".tar.gz")
    # repackage Debian Module as a tarball.
    with tarfile.open(debian_module_tar, "w:gz") as tar:
        tar.add(package.package_dir.relative_to(Path(".").resolve()))

    return debian_module_tar

def modularize_package(package: Package, modules: Dict[PackageMetadata, Module], s3_config: Dict[str, str]):
    """Turns package into a module and adds it to local registry."""
    _rpath_patch_elf_files(package=package, modules=modules)
    debian_module_tar = _repackage_deb_package(package)
    _upload_archive_to_s3_bucket(file=debian_module_tar, s3_config=s3_config)
    
    full_url = ""
    if DOWNLOAD_URL not in s3_config and PREFIX in s3_config:
        full_url =  f"{s3_config[UPLOAD_BUCKET]}/{s3_config[PREFIX]}/{debian_module_tar}"
    elif DOWNLOAD_URL not in s3_config:
        full_url =  f"{s3_config[UPLOAD_BUCKET]}/{debian_module_tar}"
    elif DOWNLOAD_URL in s3_config and PREFIX in s3_config:
        full_url =  f"{s3_config[DOWNLOAD_URL]}/{s3_config[PREFIX]}/{debian_module_tar}"
    else:
        full_url =  f"{s3_config[DOWNLOAD_URL]}/{debian_module_tar}"

    add_package_to_registry(
        package=package,
        debian_module_tar=debian_module_tar,
        full_url=full_url,
    )
    debian_module_tar.unlink()
