load("@rules_python//python:defs.bzl", "py_binary")

def run_bazelizer(repository):
    # Execute the command
    py_binary(
        name = "dependency-bazelizer",
        srcs = [Label("//src:main_module.py")],
        main = Label("//src:main_module.py"),
        deps = [
            Label("//src:bazelize_deps"),
            Label("//src:read_input_files"),
            Label("//src:storage"),
            repository + "//:dep_bazelizer_config"
            ],
)

