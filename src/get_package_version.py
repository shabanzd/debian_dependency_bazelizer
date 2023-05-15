import logging
import subprocess
import functools
import re
from typing import Final
from pathlib import Path
from packaging import version, specifiers

from src.module import get_module_name

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# version attribute as listed in apt-cache show
VERSION_ATTRIBUTE: Final = "Version"
VERSION_DOT_TXT: Final = Path("version.txt")

class FileSystem(object):
    def path_exists(self, path: Path) -> bool:
        return path.exists()

    def get_directories(self, path: Path) -> list:
        return [version.name for version in path.iterdir() if version.is_dir()]

    def get_file_contents(self, path: Path) -> str:
        with open(path, "r", encoding='utf-8') as file:
            return file.read()


def satisfies_specification(pkg_version: str, spec: str) -> bool:
    logger.debug("Checking if package version %s satisfies specification %s", pkg_version, spec)
    v = version.parse(pkg_version)
    
    is_satisfactory = v in specifiers.SpecifierSet(spec)
    logger.debug("Checking if package version %s satisfies specification %s: %s", pkg_version, spec, is_satisfactory)
    
    return is_satisfactory

def parse_debian_version(version_string: str):
    # https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-version
    match = re.match(r"(?:(\d+):)?([^-]+)(?:-(.+))?", version_string)
    if match is None:
        raise ValueError(f"Invalid Debian version string: {version_string}")
    epoch, debian_version, _ = match.groups()
    try:
        epoch = int(epoch)
    except TypeError:
        # epoch is not a correct integer
        epoch = None

    return epoch, debian_version

def compare_debian_versions(version1: str, version2: str) -> int:
    epoch1, debian_version1 = parse_debian_version(version1)
    epoch2, debian_version2 = parse_debian_version(version2)

    # Compare epochs as integers if they are both present
    if epoch1 is not None and epoch2 is not None:
        if epoch1 < epoch2:
            return -1
        elif epoch1 > epoch2:
            return 1
    
    # The epoch is a number that can be used to ensure that all later versions of the package are considered "newer" than all earlier versions.
    #  Here is the quote from the Debian Policy Manual:
    # "It is provided to allow mistakes in the version numbers of older versions of a package, and also a package's previous version numbering schemes, to be left behind."
    # So, if the epoch is higher, it will always be considered a newer version, regardless of the rest of the version string.

    # If epochs are equal, compare the rest of the version
    v1 = version.parse(debian_version1)
    v2 = version.parse(debian_version2)

    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0

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


def _get_deb_package_version_from_aptcache(name: str, arch: str) -> str:
    if not name or not arch:
        raise ValueError("both name and arch need to be provided")

    deb_package_name = f"{name}:{arch}"
    package_info = subprocess.check_output(
        ["apt-cache", "show", deb_package_name],
        encoding="utf-8",
        stderr=subprocess.STDOUT,
    )

    return _extract_attribute(package_info=package_info, attribute=VERSION_ATTRIBUTE)


def get_version_from_registry(
    registry_path: Path, name: str, arch: str, version_spec: str = "", fs = FileSystem()
) -> str:
    module_name = get_module_name(name=name, arch=arch)
    modules_path = registry_path / "modules"
    module_path = modules_path / module_name

    if not fs.path_exists(module_path):
        logger.info(
            f"module {module_name} not found in local bazel registry, expected path: {module_path} does not exist."
        )
        return ""

    versions =  fs.get_directories(module_path)

    logger.debug("Versions found: %s", versions)

    if not versions:
        raise ValueError(
            f"package: {module_name}, exists in registry modules, but has no versions"
        )

    versions.sort(key=functools.cmp_to_key(compare_debian_versions))
    logging.debug("Sorted versions: %s", versions)

    # find the highest version that matches the version_specifier
    for v in reversed(versions):
        if satisfies_specification(parse_debian_version(v)[1], version_spec):
            logger.debug("Found version: %s", parse_debian_version(v)[1])
            version_output_path = Path(module_path, str(v), VERSION_DOT_TXT)
            version_output = fs.get_file_contents(version_output_path)
            

            return version_output

    return ""


def get_package_version(registry_path: Path, name: str, arch: str) -> str:
    dep_version = get_version_from_registry(registry_path=registry_path, name=name, arch=arch)
    if not dep_version:
        dep_version = _get_deb_package_version_from_aptcache(name, arch)

    return dep_version