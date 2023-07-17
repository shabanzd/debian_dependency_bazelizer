load("@rules_python//python:defs.bzl", "py_binary")
load("@rules_python//python/pip_install:repositories.bzl", "requirement")

def run_bazelizer():
    # Execute the command
    py_binary(
        name = "dependency-bazelizer",
        srcs = [Label("//src:main.py")],
        main = Label("//src:main.py"),
        #data = [Label("//src:dependency-bazelizer")],
        deps = [
            requirement("click"),
            Label("//src:bazelize_deps"),
            Label("//src:read_input_files"),
            ],
)

