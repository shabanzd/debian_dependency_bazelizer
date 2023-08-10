def _dep_bazelizer_config_rule_impl(ctx):
  deb_packages_input_file_str = "deb_packages.in"
  storage_config_file_str = "storage_config_file.json"
  content = ""
  for input_file in ctx.attr.deb_packages_input_files:
    content += ("\n" + ctx.read(ctx.path(input_file)))
  
  ctx.file(deb_packages_input_file_str, content=content)
  ctx.file(storage_config_file_str, content=ctx.read(ctx.path(ctx.attr.storage_config_file)))
  ctx.file("WORKSPACE", "")
  ctx.file("BUILD.bazel", """
py_library(
    name = "dep_bazelizer_config",
    srcs = ["dep_bazelizer_config.py"],
    data = [
        ":{}",
        ":{}",
    ],
    visibility = ["//visibility:public"],
)
  """.format(deb_packages_input_file_str, storage_config_file_str))

  deb_packages_path = str(ctx.path(deb_packages_input_file_str))
  storage_config_path = str(ctx.path(storage_config_file_str))
  ctx.file("dep_bazelizer_config.py", """
def get_deb_packages_path() -> str:
    return "{}"
def get_storage_config_file_path() -> str:
    return "{}"
  """.format(deb_packages_path, storage_config_path))

dep_bazelizer_config_rule = repository_rule(
  implementation = _dep_bazelizer_config_rule_impl,
  attrs = {
      "deb_packages_input_files":  attr.label_list(mandatory = True),
      "storage_config_file": attr.label(mandatory = True),
  },
)

def _dependency_bazelizer_impl(ctx):
  deb_packages_input_files = []
  storage_config_file = None
  for mod in ctx.modules:
    for config in mod.tags.config:
        deb_packages_input_files.append(config.deb_packages_input_file)
    if mod.is_root:
        if not ctx.path(config.storage_config_file).basename.endswith(".json"):
          fail("s3 config file must be a json file")
        storage_config_file = config.storage_config_file
  
  dep_bazelizer_config_rule(
    name = "dep_bazelizer_config",
    deb_packages_input_files = deb_packages_input_files,
    storage_config_file = storage_config_file,
  )

dependency_bazelizer = module_extension(
  implementation = _dependency_bazelizer_impl,
  tag_classes = {"config": tag_class(attrs = {"deb_packages_input_file": attr.label(mandatory=True), "storage_config_file": attr.label(mandatory=True)})},
)
