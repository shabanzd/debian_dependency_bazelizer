# dependency-bazelizer (WIP)

The dependency bazelizer aims at analyzing the transitive dependency graph of each input dependency and turning the entire graph into bzlmods that fetch each other as needed. The modules are also automatically referenced by the local registry of the repo.

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

In order to try the dependency-bazelizer, you need a linux machine and `patchelf` installed on that machine. The reason `patchelf` was not bazelized is that I don't know where this script will run (ubuntu, wsl ... etc). In case you are interested in bazelizing the `patchelf` dependency, you can easily do that using the dependency-bazelizer itself on your chosen platform.

* clone the repo.
* `cd dependency-bazelizer`
* fill up the deb_packages.in file with the deb packages you want to modularize. Name and architecture of the package are mandatory, and the package needs to follow the format: `name:arch=version`.
* `bazelisk run //src:dependency-bazelizer`

Now you have will have the dependencies, listed in the deb_packages.in, modularized, alongside their entire transitive dependency graphs! :partying_face:

The `dependency-bazelizer` locate the new modules in the folder `modules/` and the internal registry referencing those modules at `registry/`. In the .bazelrc, I already added the internal registry as the main bazel registry, with the Bazel Central Registry as a fallback. So as soon as you modularize the desired dependencies, you can go ahead and play around with them!

If this is the first time you play around with this tool, this video will help you get started: 
https://www.youtube.com/watch?v=LFV-H7djEYw
