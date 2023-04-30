# dependency-bazelizer (WIP)

The dependency bazelizer aims at analyzing the transitive dependency graph of each input dependency and the turning entire graph into bzlmods that fetch each other as needed. The modules are also automatically referenced by the local registry of the repo.

So far, this is only done for debian packages. The plan is to include Python as well in the following versions.

# Summary

Since bazel6 and the introduction of bzlmods, one can, at least in theory, build a dependency graph consisting of bazel modules. See, modules act cool, but in reality, they are anything with a `MODULE.bazel` file on top, and a few accessory files like an empty `WORKSPACE` and a `BUILD.bazel` file exposing the files and targets to be used by other modules. 

So in order to turn a debian package (say `deb_a`), for example, into a module, all we need to do is: unpackage it, put a `MODULE.bazel`, empty `WORKSPACE` and a `BUILD.bazel` file on top, and store the folder containing everything somewhere in the repo (or archive it and upload it somewhere).

Great, so now `deb_a` is a module. Problem is, it is likely that deb_a has transitive dependencies. In order for the `deb_a` module to fetch those dependencies, they also need to be modules. In other words, the entire subgraph needs to be built up of bazel modules. This means that the modularization process mentioned above should be done for the entire dependency subgraph.

The dependency-bazelizer tries to do exactly that; it processes the entire dependency graph and repackages it into modules. It also adds references to these modules in a local registry inside the repo. One can visualize the process as in the graph below

```mermaid
graph LR;
    A[Unpackage Dependency]-->B[Modularize Dependency];
    B-->C[Reference Dependency in The Local Registry];
    D[Next Dependency]-->A;
    C --> D;
```

# Give it a try!

In order to try the dependency-bazelizer, you need a linux machine and `patchelf` installed on that machine. The reason `patchelf` was not bazelized is that I don't know where this script will run (ubuntu, wsl ... etc). In case you are interested in bazelizing the `patchelf` dependency, you can easily do that using the dependency-bazelizer itself on your chosen OS.

* clone the repo.
* `cd dependency-bazelizer`
* `bazelisk run //src:dependency-bazelizer`

Now you have iproute2 modularized! you can go ahead and add it to `MODULE.bazel` and run the demo `demos:iproute2-demo` (you may need to tweek the path in `demos/iproute2_demo.py`, depending on the version of iproute2 in your apt-cache)

