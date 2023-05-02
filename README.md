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

# Nerdy details

The work is not done by adding a `MODULE.bazel` to a package and making sure that this module fetches the needed transitive dependencies. The pre-compiled C/C++ files in a package don't only expect their transitive runtime dependencies to exist on the system, but also to exist in a specific predefined location (`/bin/` for example). However, we don't want the transitive dependencies to be accessed directly from the system, we want the transitive deps in the runfiles to be the ones used ! This makes the problem way more exciting :wink:

### RPath patching


The problem above has a solution: RPaths! Rpaths are both searched before `LD_LIBRARY_PATH` (they take priority over `LD_LIBRARY_PATH`s) and they can be patched after the library has already been compiled. The RPath patching can be acheived using tools like patchelf, which is the tool we are using here. For more info: https://www.qt.io/blog/2011/10/28/rpath-and-runpath

But how does a dependency know the `rpath` of its transitive runtime deps ? 

I will answer this with an art work:

<img width="1612" alt="Screenshot 2023-05-02 at 16 27 38" src="https://user-images.githubusercontent.com/8200878/235696979-3784c0a4-a2c8-42b4-a8d3-605a18f55652.png">

<img width="1563" alt="Screenshot 2023-05-02 at 16 28 17" src="https://user-images.githubusercontent.com/8200878/235697542-3f043ecf-8e0d-48b2-8824-08847f2a7489.png">

So basically dependency B needs to be processed ahead of dependency A. It also needs to self declare all the parent directories of all the ELF files in it. In other words, the dependency graph needs to be processed in a **topological order**.


### Code Workflow - Debian Only

Now in the case of debian packages, the implementation details mentioned above can be translated into the following workflow:

```mermaid
graph TB;
    A[Queue of deb dependencies, deb_q]-->|deb_dep|B{Visited?};
    %% if visited, pop and process next
    B-->|yes|C[Pop deb_q]-->A;
    %% if not in visited, continue
    B-->|no|D[Find transitive dependencies of deb_dep]-->E{Are all transitive dependencies processed? Meaning: did all transitive dependencies declare their rpaths?}-->|yes|F[Modularize and rpath patch deb_dep]-->C;
    %% if not all transitive dep processed already, add them to queue
    E-->|no|G[add unprocessed transitive deps to deb_q]-->A
```

A more detailed view would look like:

```mermaid
graph TB;
    A[Queue of deb dependencies, deb_q]-->|deb_dep|B{Visited?};
    %% if visited, pop and process next
    B-->|yes|C[Pop deb_q]-->A;
    %% if not in visited, check registry
    B-->|no|D{In Registry?};
    %% if in registry, retrieve and mark visited
    D-->|yes|E[Retrieve info from egistry]-->F[Mark as Visited]-->C;
    %% if not in registry, 
    D-->|no|G[apt-get download deb_dep_pinned_name] -->|get transitive deps|H[dpkg-deb -I deb_archive_path]-->|list files|I[dpkg -X deb_archive_path pkg_dir] --> J[get rpath directories]-->K{are all transitive dependency visited?};
    %% if all transitive deps are visited => edge => rpath patch and modularize
    K-->|yes|L[rpath patch ELF files in the package]-->M[Turn package into a module]-->N[Upload as an archive, or add to repo]-->O[reference the module in the registry]-->C;
    %% if all transitive deps are visited => process next
    K-->|no|P[add all non-processed transitive deps to deb_q]-->A;
```

