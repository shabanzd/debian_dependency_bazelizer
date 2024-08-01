def run_bazelizer():
    # Execute the command
    native.alias(
        name = "debian_dependency_bazelizer",
        actual = Label("//src:debian_dependency_bazelizer")
    )
