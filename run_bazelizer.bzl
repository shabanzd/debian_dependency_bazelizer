load("@rules_python//python:defs.bzl", "py_binary")
load("@rules_python//python/pip_install:repositories.bzl", "requirement")

def run_bazelizer():
    # Execute the command
    py_binary(
        name = "debian_dependency_bazelizer",
        srcs = [Label("//src:main.py")],
        main = Label("//src:main.py"),
        deps = [
            Label("//src:bazelize_deps"),
            Label("//src:read_input_files"),
            requirement("click")
            ],
)
