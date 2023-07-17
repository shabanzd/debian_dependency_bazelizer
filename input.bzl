def _bazelizer_impl(ctx):
  # collect artifacts from across the dependency graph
  artifacts = []
  i = 0
  for mod in ctx.modules:
    for input in mod.tags.input:
        i += 1
        file_name = "in" + str(i) + ".in"
        content = module_ctx.read(module_ctx.path(input))
        module_ctx.file(path=file_name, content=content)

_input = tag_class(attrs = {"input_file": attr.label()})
bazelizer = module_extension(
  implementation = _bazelizer_impl,
  tag_classes = {"input": _input},
)
