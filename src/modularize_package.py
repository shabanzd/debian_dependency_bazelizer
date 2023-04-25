from typing import Final
from pathlib import Path

from package import Package
from writers import write_build_file, write_module_file

import os
import shutil


KEY_PREFIX: Final = "debian_test"
BUCKET: Final = "public"
URL: Final = "http://172.19.51.35:32198"
PATCHELF_PROGRAM: Final = (
    Path()
    .joinpath("..", "patchelf_amd64~0.10-2build1", "usr", "bin", "patchelf")
    .resolve()
)
BUILD_FILE: Final = Path("BUILD")
MODULE_DOT_BAZEL: Final = Path("MODULE.bazel")
BAZEL_WORKSPACE_DIR: Final = os.environ["BUILD_WORKSPACE_DIRECTORY"]
MODULES_DIR : Final = Path().joinpath(BAZEL_WORKSPACE_DIR, "modules")


def _repackage_deb_package(package: Package):
    # create empty WORKSPACE file
    Path(package.package_dir / Path("WORKSPACE")).touch()
    write_build_file(package, Path(package.package_dir / BUILD_FILE))
    write_module_file(
        package, Path(package.package_dir / MODULE_DOT_BAZEL)
    )

def modularize_package(package: Package):
    _repackage_deb_package(package=package)
    shutil.move(package.package_dir, MODULES_DIR)
