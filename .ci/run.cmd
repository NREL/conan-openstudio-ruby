
set CONAN_PKG_NAM=openstudio_ruby
set RUBY_VERSION=2.5.5
set CONAN_REPO=openstudio
set CONAN_CHANNEL=testing
set CONAN_USER=commercialbuilding

git rev-parse --short=10 HEAD > sha.txt
set /p GIT_SHA_SHORT=<sha.txt


conan remote add bincrafters https://api.bintray.com/conan/bincrafters/public-conan
conan remote add conan-center https://conan.bintray.com
conan remote add %CONAN_REPO% https://api.bintray.com/conan/commercialbuilding/openstudio

conan user -p %BINTRAY_API% -r %CONAN_REPO% %CONAN_USER%

conan create . %CONAN_PKG_NAM%/%RUBY_VERSION%-%GIT_SHA_SHORT%@%CONAN_REPO%/%CONAN_CHANNEL%

conan upload "%CONAN_PKG_NAM%/%RUBY_VERSION%-%GIT_SHA_SHORT%@%CONAN_REPO%/%CONAN_CHANNEL%" -r %CONAN_REPO%


