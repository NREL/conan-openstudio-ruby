# Conan OpenStudio Ruby

A [conan](https://conan.io/) package to build ruby for [OpenStudio](https://github.com/NREL/OpenStudio).

## Package Status

| Bintray | Windows | Linux & macOS |
|:--------:|:---------:|:-----------------:|
|[![Download](https://api.bintray.com/packages/commercialbuilding/nrel/openstudio_ruby%3Anrel/images/download.svg)](https://bintray.com/commercialbuilding/nrel/openstudio_ruby%3Anrel/_latestVersion)|[![Build status](https://ci.appveyor.com/api/projects/status/github/nrel/conan-openstudio-ruby?branch=master&svg=true)](https://ci.appveyor.com/project/ci-commercialbuildings/conan-openstudio-ruby/branch/master)|[![Build Status](https://travis-ci.org/nrel/conan-openstudio-ruby.svg?branch=master)](https://travis-ci.org/nrel/conan-openstudio-ruby)|

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
