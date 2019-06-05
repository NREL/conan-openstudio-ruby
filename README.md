## Package Status

| Bintray | Windows | Linux & macOS |
|:--------:|:---------:|:-----------------:|
|[![Download](https://api.bintray.com/packages/jmarrec/testing/openstudio_ruby%3Ajmarrec/images/download.svg)](https://bintray.com/jmarrec/testing/openstudio_ruby%3Ajmarrec/_latestVersion)|[![Build status](https://ci.appveyor.com/api/projects/status/github/jmarrec/openstudio_ruby?svg=true)](https://ci.appveyor.com/project/jmarrec/conan-openstudio-ruby)|[![Build Status](https://travis-ci.com/jmarrec/conan-openstudio-ruby.svg)](https://travis-ci.com/jmarrec/conan-openstudio-ruby)|

# Conan OpenStudio Ruby

A [conan](https://conan.io/) package to build ruby for [OpenStudio](https://github.com/NREL/OpenStudio).

# Uploading to bintray

**TODO: Once the NREL bintray is up and running, only include the information needed to upload (remove the setup portion) and with the right links**

Full instructions available at [Conan Docs](https://docs.conan.io/en/latest/uploading_packages/bintray/uploading_bintray.html).

Steps:

* Setup a new organization and repo on bintray. For now I didn't add an organization, just a repo, at https://bintray.com/jmarrec/testing
* Get your API key by clicking on "View Profile"
* Add remote to conan client
```
conan remote add <REMOTE> <YOUR_BINTRAY_REPO_URL>
# eg:
conan remote add jmarrec https://api.bintray.com/conan/jmarrec/testing
```

* Add your API key:
```
conan user -p <APIKEY> -r <REMOTE> <USERNAME>
# eg:
conan user -p <API_KEY> -r jmarrec jmarrec
```

* Add a new package on bintray, eg 'openstudio_ruby'
* Add a new version for the package, eg '2.5.5:testing'

* Build your binaries locally and Upload them to your remote:
```
conan create . openstudio_ruby/2.5.5@jmarrec/testing -r jmarrec
conan upload openstudio_ruby/2.5.5@jmarrec/testing -r jmarrec
```
