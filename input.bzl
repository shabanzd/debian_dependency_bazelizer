def _concat_input_files_impl(ctx):
  deb_packages_input_file_str = "deb_packages.in"
  s3_config_file_str = "s3_config_file.json"
  content = ""
  for input_file in ctx.attr.deb_packages_input_files:
    content += ("\n" + ctx.read(ctx.path(input_file)))
  
  ctx.file(deb_packages_input_file_str, content=content)
  ctx.file(s3_config_file_str, content=ctx.read(ctx.path(ctx.attr.s3_config_file)))
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
  """.format(deb_packages_input_file_str, s3_config_file_str))

  deb_packages_path = str(ctx.path(deb_packages_input_file_str))
  s3_config_path = str(ctx.path(s3_config_file_str))
  ctx.file("dep_bazelizer_config.py", """
def get_deb_packages_path() -> str:
    return "{}"
def get_s3_config_file_path() -> str:
    return "{}"
  """.format(deb_packages_path, s3_config_path))

concat_input_files = repository_rule(
  implementation = _concat_input_files_impl,
  attrs = {
      "deb_packages_input_files":  attr.label_list(mandatory = True),
      "s3_config_file": attr.label(mandatory = True),
  },
)

def _bazelizer_impl(ctx):
  deb_packages_input_files = []
  s3_config_file = None
  for mod in ctx.modules:
    for config in mod.tags.config:
        deb_packages_input_files.append(config.deb_packages_input_file)
    if mod.is_root:
        if not ctx.path(config.s3_config_file).basename.endswith(".json"):
          fail("s3 config file must be a json file")
        s3_config_file = config.s3_config_file
  
  concat_input_files(
    name = "hello",
    deb_packages_input_files = deb_packages_input_files,
    s3_config_file = s3_config_file,
  )

bazelizer = module_extension(
  implementation = _bazelizer_impl,
  tag_classes = {"config": tag_class(attrs = {"deb_packages_input_file": attr.label(mandatory=True), "s3_config_file": attr.label(mandatory=True)})},
)
