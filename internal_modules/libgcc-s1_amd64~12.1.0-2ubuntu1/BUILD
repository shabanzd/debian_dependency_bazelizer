filegroup(
    name = "all_files",
    srcs = [
      "lib/x86_64-linux-gnu/libgcc_s.so.1",
      "usr/share/lintian/overrides/libgcc-s1",
    ],
    data = [
      "@libc6_amd64//:all_files",
      "@gcc-12-base_amd64//:all_files",
    ],
    visibility = ["//visibility:public"],
)


exports_files([
    "lib/x86_64-linux-gnu/libgcc_s.so.1",
      "usr/share/lintian/overrides/libgcc-s1",
])


