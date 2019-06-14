# Conan OpenStudio Ruby

A [conan](https://conan.io/) package to build ruby for [OpenStudio](https://github.com/NREL/OpenStudio).

## Package Status

| Bintray | Windows | Linux & macOS |
|:--------:|:---------:|:-----------------:|
|[![Download](https://api.bintray.com/packages/commercialbuilding/nrel/openstudio_ruby%3Anrel/images/download.svg)](https://bintray.com/commercialbuilding/nrel/openstudio_ruby%3Anrel/_latestVersion)|[![Build status](https://ci.appveyor.com/api/projects/status/github/jmarrec/conan-openstudio-ruby?svg=true)](https://ci.appveyor.com/project/jmarrec/conan-openstudio-ruby)|[![Build Status](https://travis-ci.org/jmarrec/conan-openstudio-ruby.svg?branch=master)](https://travis-ci.org/jmarrec/conan-openstudio-ruby)|

CI is done by Travis for Linux&Mac, and AppVeyor for Windows. To ignore specific commits, please add tags in your commit message such as `[skip ci]` (skip all), `[skip travis]` or `[skip appveyor]`.

## Uploading to bintray (unecessary due to CI)

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
