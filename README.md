# Conan OpenStudio Ruby

A [conan](https://conan.io/) package to build ruby for [OpenStudio](https://github.com/NREL/OpenStudio).

## Package Status

| Bintray | Windows | Linux & macOS |
|:--------:|:---------:|:-----------------:|
|[Download](https://conan.commercialbuildings.dev/ui/repos/tree/General/openstudio%2Fnrel%2Fopenstudio_ruby)|[![openstudio_ruby/stable](https://github.com/NREL/conan-openstudio-ruby/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/NREL/conan-openstudio-ruby/actions/workflows/build.yml)|[![openstudio_ruby/testing](https://github.com/NREL/conan-openstudio-ruby/actions/workflows/build.yml/badge.svg?branch=develop)](https://github.com/NREL/conan-openstudio-ruby/actions/workflows/build.yml)|

CI is done by Travis for Linux&Mac, and AppVeyor for Windows. To ignore specific commits, please add tags in your commit message such as `[skip ci]` (skip all), `[skip travis]` or `[skip appveyor]`.

## Testing

There is a `test_package` folder that builds a CLI that relies on `openstudio_ruby`, as well as `swig_installer` and `zlib` (to embed files).

It's a CLI that has most features of openstudio's CLI, except openstudio-specific stuff (like ApplyMeasure, Run, Update).

It should hopefully help us:

* Catch things that break early on, before we notice it on OpenStudio's side
* Allow us to test/debug cli ruby specific issues (encodings, gem_install, interactive, etc)


If you run the `conan create` command, it will automatically run the tests against the package it built right after.
From the root of the repo:

```
conan create . nrel/testing
```

If you only wanted to run the tests against a package you already have (downloaded or built), you can also do that like so:

```
conan test test_package openstudio_ruby/2.5.5@nrel/stable
```

## Uploading to Bintray (unnecessary due to CI)

Full instructions available at [Conan Docs](https://docs.conan.io/en/latest/uploading_packages/bintray/uploading_bintray.html).

Steps:
* Get your API key by clicking on "View Profile"
* Add remote to conan client
```
conan remote add <REMOTE> <YOUR_BINTRAY_REPO_URL>
# eg:
conan remote add nrel https://api.bintray.com/conan/commercialbuilding/nrel
```

* Add your API key:
```
conan user -p <APIKEY> -r <REMOTE> <USERNAME>
# eg:
conan user -p <API_KEY> -r nrel commercialbuilding
```

* Build your binaries locally and Upload them to your remote:
```
conan create . openstudio_ruby/2.5.5@nrel/testing -r nrel
conan upload openstudio_ruby/2.5.5@nrel/testing -r nrel
```

## Copying a CCI recipe and vendoring it to NREL's remote

eg vendoring zlib/1.2.11

```bash
# Wipe dir to be sure
/bin/rm -Rf /home/julien/.conan/data/zlib/1.2.11

# Download recipe and all binary packages from CCI's remote
conan download -r conan-center zlib/1.2.11@

# Might want to make sure nothing is existing?
conan remove -r nrel zlib/1.2.11@

# Note: sometimes going to bintray and deleting the complete package helps (eg if you have inadvertantly uploaded several revisions and now you get "Upload skipped, package existing")

# Upload recipe
conan upload zlib/1.2.11@ -r nrel --all --no-overwrite recipe --parallel

# Check result?
conan search -r nrel zlib/1.2.11@
# Or output to a html table
conan search -r nrel zlib/1.2.11@ --table zlib.html
# Or a json
conan search -r nrel zlib/1.2.11@ --json zlib.json
```

## Conan and the recipe hash: how to produce the same hash

This section is especially true should you need to manually build some packages or package configurations for example
if CCI doesn't even have a package for the compiler or the recipe option you need.

eg: `zlib` with the `minizip=True` option)

Conan's hash is computed by looking at which files are exported. So you need to make sure that are using the same configuration on all machines.

### Line endings

Line endings matter! This means that by the Git for windows default, you will not compute the same hash since it defaults to CRLF line endings.

```
git config --system core.autocrlf input
git config --system core.eol lf
```

If you had already checked out the repo before settings these settings, you need to tell git to pick the right line endings now:

```
cd conan-openstudio-ruby
git checkout-index --force --all
git rm --cached -r .  # Remove every file from git's index.
git reset --hard      # Rewrite git's index to pick up all the new line endings.
```

### Revisions:

You `conan.conf` should contain `general.revisions_enabled=True`:

```
$ conan config get general.revisions_enabled
True
```

If not, activate it via editing `~/.conan.conf` or by typing `conan config set general.revisions_enabled=True`

### Hooks

The conan-center-index hook in particular will modify the conandata.yml if any, so if you are manually building dependencies from CCI, you need to be consistent.
To activate the hook:

```
conan config install https://github.com/conan-io/hooks.git -sf hooks -tf hooks
conan config set hooks.conan-center
```

Make sure every machine returns the same:

```
$ conan config get hooks
attribute_checker,conan-center
```

### Avoiding human errors for CCI packages

If you are trying to add packages for new configurations/options, instead of building from the repo, you should download then build.
This is especially true for conan-center-index. Downloading the recipe and building it from cache is much better than creating or
exporting the recipe from the conan-center-index repository. From the repository you need to check that you are in the same commit,
that you have the same hooks, etc, and there will be human errors.

```
conan download -r nrel zlib/1.2.11@ --recipe
conan install zlib/1.2.11@ -b zlib -o zlib:minizip=True -s build_type=Release
conan install zlib/1.2.11@ -b zlib -o zlib:minizip=True -s build_type=Debug
```

### Making sure you do not export a NEW recipe

Find the current revision

```
$ conan search -r nrel zlib/1.2.11@ -rev
0df31fd24179543f5720ec7beb2a88d7
```

Then specify it in the upload command! That way you're sure you're exporting the right one (= appending packages).

```
conan upload zlib/1.2.11@ -r nrel --all --parallel --no-overwrite all
conan upload zlib/1.2.11@:0df31fd24179543f5720ec7beb2a88d7 -r nrel --all --parallel --no-overwrite all
```
