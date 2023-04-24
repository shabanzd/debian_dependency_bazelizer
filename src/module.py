def get_module_name(name: str, arch: str):
    """Architecture is appended to the module name to accommodate for the case of debian packages
    having the same name and different achitectures since there is no arch attribute in module()
    """

    module_name = f"{name}_{arch}"
    # 1) valid names must only contain lowercase letters (a-z), digits (0-9), dots (.), hyphens (-),
    # and underscores (_); 2) begin with a lowercase letter; 3) end with a lowercase letter or digit.
    module_name = module_name.lower()
    module_name = module_name.replace("+", "plus")

    return module_name


def get_module_version(version: str):
    "Debian versions have all sort of characters. This gets rid of the bazel unallowed version characters."
    filtered_version = version
    filtered_version = filtered_version.split(":")[-1]
    filtered_version = filtered_version.split("+")[0]
    filtered_version = filtered_version.split("~")[0]
    return filtered_version
