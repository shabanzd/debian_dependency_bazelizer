from typing import ByteString, Final
from pathlib import Path

import hashlib
import os
import subprocess

from get_package_version import get_package_version
from module import get_module_name, get_module_version
from package import PackageMetadata, Package

DEPENDS_ATTR: Final = "Depends"

def _is_acceptable_error(err: ByteString):
    if (
        err == "patchelf: not an ELF executable\n"
        or err == "patchelf: missing ELF header\n"
        or err == "patchelf: open: Permission denied\n"
    ):
        return True

    return False


def _is_patchable_elf_file(file: Path) -> bool:
    "Tries to print rpath in order to tell if file is ELF or not"
    try:
        old_rpath = subprocess.run(
            ["patchelf", "--print-rpath", file.resolve()],
            check=True,
            capture_output=True,
            encoding="utf-8",
        ).stdout
        old_rpath = old_rpath.strip("\n")
        if not old_rpath:
            old_rpath = "$ORIGIN"

        _ = subprocess.run(
            ["patchelf", "--remove-rpath", file.resolve()],
            check=True,
            capture_output=True,
            encoding="utf-8",
        ).stdout
        _ = subprocess.run(
            ["patchelf", "--force-rpath", "--set-rpath", old_rpath, file.resolve()],
            check=True,
            capture_output=True,
            encoding="utf-8",
        ).stdout
        return True
    except subprocess.CalledProcessError as e:
        if _is_acceptable_error(e.stderr):
            # Non-patchable file
            return False
        raise e


def _get_deb_pinned_name(name: str, arch: str = "", version: str = ""):
    package = name
    if arch:
        package += f":{arch}"
    if version:
        package += f"={version}"

    return package


def _download_package_dot_debian(name: str, arch: str, version: str, pinned_name: str) -> Path:
    subprocess.check_call(
        ["sudo", "apt-get", "download", pinned_name], stdout=subprocess.DEVNULL
    )

    files = [file for file in os.listdir() if os.path.isfile(file)]
    for file in files:
        modified_file = file.replace("%3a", ":")
        if (
            modified_file == f"{name}_{version}_{arch}.deb"
            or modified_file == f"{name}_{version}_all.deb"
        ):
            return Path(file).resolve()
    
    current_dir = str(Path.cwd())
    raise ValueError(f"could not find the downloaded debian package for {pinned_name} in dir: {current_dir}")


def _extract_attribute(
    package_info: str, attribute: str, must_exist: bool = True
) -> str:
    "Extracts a specific attribute from the info listed using 'apt-cache' or 'dpkg-deb'."
    prefix = attribute + ": "
    lines = package_info.splitlines()

    for line in lines:
        line = line.lstrip()
        if line.startswith(attribute):
            return line[len(prefix) :]

    if not must_exist:
        return ""

    raise ValueError(
        f"{attribute} could not be extracted from package_info: {package_info}"
    )


def _get_deb_dep_names(archive_path: Path):
    deps_str = _extract_attribute(
        subprocess.check_output(["dpkg-deb", "-I", archive_path], encoding="utf-8"),
        DEPENDS_ATTR,
        False,
    )

    deps = []
    if not deps_str:
        return deps

    polluted_deps = deps_str.split(", ")

    for dep in polluted_deps:
        # imagine a case where the following is returned: debconf (>= 0.5) | debconf-2.0, 
        # we want the left hand side, since it is not a virtual dep. The way to do that, is to search for brackets
        # not too smart but works for now :)
        alternative_deps = dep.split(" | ")
        dep = alternative_deps[0]
        for alternative_dep in alternative_deps:
            if "(" in alternative_deps and ")" in alternative_deps:
                dep = alternative_dep
                break

        # with the not-so-clever check above, we may still end up with something like: dep-1.0
        # in that case, we wanna make sure it is not vitual
        if "(" not in dep:
            info = subprocess.run(
                ["apt-cache", "show", dep],
                check=True,
                capture_output=True,
                encoding="utf-8",
            ).stdout
            # if dep is virtual ignore it
            if not info:
                dep = ""
                continue

        if not dep:
            continue
        # in case it is of the pattern dep (>= 0.1), we want to get rid of the (>= 0.1)
        # TODO: here we can implement smarter version range checks.
        dep = dep.split(" ")[0]
        dep = dep.split(":")[0]
        deps.append(dep)

    return deps


def create_deb_package(metadata: PackageMetadata):
    if not metadata.name or not metadata.arch or not metadata.version:
        raise ValueError(
            f"name, arch and version must all be provided and not empty, in order to create a debian package. Provided values are: name={metadata.name}, version={metadata.version}, arch={metadata.arch}"
        )

    package = Package()
    package.name = metadata.name
    package.arch = metadata.arch
    package.version = metadata.version
    package.pinned_name = _get_deb_pinned_name(
        name=metadata.name, arch=metadata.arch, version=metadata.version
    )
    package.prefix = f"{package.name}{package.version}{package.arch}"
    package.compatibility_level = (
        int(hashlib.sha256(package.prefix.encode("utf-8")).hexdigest(), 16) % 10**8
    )
    # path to package.deb
    archive_path = _download_package_dot_debian(
        name=metadata.name,
        arch=metadata.arch,
        version=metadata.version,
        pinned_name=package.pinned_name,
    )
    package_dir = archive_path.parent / Path(package.prefix)
    package_dir.mkdir()
    package.package_dir = package_dir.resolve()
    # the following fills the files-related attributes of the deb package
    files_str = subprocess.check_output(
        ["dpkg", "-X", archive_path, package.package_dir],
        encoding="utf-8",
        stderr=subprocess.STDOUT,
    )
    rpath_prefix = f"{get_module_name(name=metadata.name, arch=metadata.arch)}~{get_module_version(metadata.version)}"

    for file in files_str.split("\n"):
        # the ":" part is a workaround some files having unacceptable names for bazel targets
        if ":" in file:
            continue

        file_path = Path(file)
        if not Path(package.package_dir / file_path).is_file():
            continue

        if not _is_patchable_elf_file(Path(package.package_dir / file_path)):
            package.nonelf_files.add(file_path)
            continue

        package.elf_files.add(file_path)
        # register the parent of the ELF file as an rpath
        package.rpaths.add(Path(rpath_prefix / file_path.parent))

    # The next check is needed since libc6 is cyclic with libcrypt1. 
    # I assume libc6 does not have deps in this case :D
    if package.name == "libc6":
        archive_path.unlink()
        return package

    # now fillup the transitive deps
    dep_names = _get_deb_dep_names(archive_path)
    for dep_name in dep_names:
        # Another workaround: tzdata accesses files from system, it needs more investigation to handle it properly.
        # TODO: find a general way to handle deps accessing files from system.
        if dep_name == "tzdata":
            continue
        dep_version = get_package_version(
            name=dep_name, arch=package.arch
        )
        package.deps.add(
            PackageMetadata(name=dep_name, arch=package.arch, version=dep_version)
        )

    archive_path.unlink()

    return package