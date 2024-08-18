from packaging import version as packaging_version, specifiers as packaging_specifiers
from pathlib import Path
from typing import Final, List, Optional

import dataclasses
import functools
import logging
import re
import subprocess


from src.module import get_module_name

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# version attribute as listed in apt-cache show
VERSION_ATTRIBUTE: Final = "Version"
VERSION_DOT_TXT: Final = Path("version.txt")


@dataclasses.dataclass
class DebianVersion:
    "Debian Version data class."
    raw_version: str
    epoch: Optional[int] = None
    version: str = ""
    semantic_version: str = ""

    def __post_init__(self):
        # https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-version
        match = re.match(
            r"(?:(\d+):)?((?:[^-]|-(?!\d))*)(?:-([\d].*))?", self.raw_version
        )
        if match is None:
            raise ValueError(f"Invalid Debian version string: {self.raw_version}")
        epoch, debian_version, _ = match.groups()
        try:
            self.epoch = int(epoch)
        except TypeError:
            # epoch is not a correct integer
            self.epoch = None

        # Process debian_version to make it compatible with packaging_version.parse
        debian_version = debian_version.split("~")[0]
        debian_version = debian_version.split("+")[0]
        debian_version = debian_version.split("-")[0]
        self.version = re.split("[^0-9.]", debian_version)[0].rstrip(".")

        epoch = "" if not self.epoch else str(self.epoch)
        self.semantic_version = epoch + self.version


@dataclasses.dataclass
class Spec:
    "Debian Version data class."
    version: DebianVersion
    spec: str

    def spec_str(self):
        """Returns the spec as a string."""
        return self.spec + self.version.semantic_version


def _get_versions(path: Path) -> List[DebianVersion]:
    return [
        DebianVersion(_get_file_contents(module_version_path / VERSION_DOT_TXT))
        for module_version_path in path.iterdir()
        if module_version_path.is_dir()
    ]


def _get_file_contents(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


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


def _parse_specs(version_spec: str) -> List[Spec]:
    if not version_spec:
        return [("", DebianVersion(None, ""))]

    specs: List[Spec] = []

    for one_version_spec in version_spec.split(","):
        for i, char in enumerate(one_version_spec):
            if char.isdigit():
                spec = one_version_spec[:i]
                version = one_version_spec[i:]
                specs.append(Spec(spec=spec, version=DebianVersion(version)))
                break

    return specs


def _satisfies_specifications(pkg_version: DebianVersion, version_spec: str) -> bool:
    """Returns if two versions are compatible."""
    specs: List[Spec] = _parse_specs(version_spec)
    for spec in specs:
        logger.debug(
            "Checking if package version %s satisfies specification %s",
            pkg_version,
            spec.spec_str(),
        )

        version = packaging_version.parse(pkg_version.semantic_version)
        if version not in packaging_specifiers.SpecifierSet(spec.spec_str()):
            return False

    return True


def get_compatibility_level(version_string: str) -> int:
    """Returns compatibility_level for a certain debian version."""
    deb_version = DebianVersion(version_string)
    epoch = str(deb_version.epoch) if deb_version.epoch is not None else ""

    # for two versions to have the same compatibility level, the epoch and major version need to be equal
    # this silly solution simply concatenates both =D
    return int(epoch + deb_version.version.split(".", maxsplit=1)[0])


def compare_version_strings(version_1: str, version_2: str) -> int:
    """Compares two debian versions.
    returns 1 if version1 > version2, -1 if version2 > version1 and 0 if version1 = version2.
    """
    debian_version_1 = DebianVersion(version_1)
    debian_version_2 = DebianVersion(version_2)
    return compare_debian_versions(debian_version_1, debian_version_2)


def compare_debian_versions(version_1: DebianVersion, version_2: DebianVersion) -> int:
    """Compares two debian versions.
    returns 1 if version1 > version2, -1 if version2 > version1 and 0 if version1 = version2.
    """
    # The epoch is a number that can be used to ensure that all later versions of the package are considered "newer" than all earlier versions.
    #  Here is the quote from the Debian Policy Manual:
    # "It is provided to allow mistakes in the version numbers of older versions of a package, and also a package's previous version numbering schemes, to be left behind."
    # So, if the epoch is higher, it will always be considered a newer version, regardless of the rest of the version string.
    if version_1.epoch is not None and version_2.epoch is not None:
        if version_1.epoch < version_2.epoch:
            return -1
        if version_1.epoch > version_2.epoch:
            return 1

    # If epochs are equal, compare the rest of the version
    version1 = packaging_version.parse(version_1.version)
    version2 = packaging_version.parse(version_2.version)

    if version1 < version2:
        return -1

    if version1 > version2:
        return 1

    return 0


def get_package_version(name: str, arch: str) -> str:
    "Get package version from apt-cache."

    return _get_deb_package_version_from_aptcache(name, arch)
