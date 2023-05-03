filegroup(
    name = "all_files",
    srcs = [
      "usr/share/doc/patchelf/copyright",
      "usr/share/doc/patchelf/changelog.Debian.gz",
      "usr/share/man/man1/patchelf.1.gz",
      "usr/share/doc/patchelf/README.md.gz",
      "usr/bin/patchelf",
    ],
    data = [
      "@libstdcplusplus6_amd64//:all_files",
      "@libc6_amd64//:all_files",
      "@libgcc-s1_amd64//:all_files",
    ],
    visibility = ["//visibility:public"],
)


exports_files([
    "usr/share/doc/patchelf/copyright",
      "usr/share/doc/patchelf/changelog.Debian.gz",
      "usr/share/man/man1/patchelf.1.gz",
      "usr/share/doc/patchelf/README.md.gz",
      "usr/bin/patchelf",
])


