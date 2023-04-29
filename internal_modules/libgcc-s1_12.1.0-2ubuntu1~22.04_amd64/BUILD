filegroup(
    name = "all_files",
    srcs = [
      "usr/share/lintian/overrides/libgcc-s1",
      "lib/x86_64-linux-gnu/libgcc_s.so.1",
    ],
    data = [
      "@gcc-12-base_amd64//:all_files",
      "@libc6_amd64//:all_files",
    ],
    visibility = ["//visibility:public"],
)


exports_files([
    "usr/share/lintian/overrides/libgcc-s1",
      "lib/x86_64-linux-gnu/libgcc_s.so.1",
])


