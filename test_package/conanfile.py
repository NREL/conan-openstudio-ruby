#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

from conans import ConanFile, CMake
from conans.errors import ConanException
import os
import re
import glob as gb

class TestFailedException(ConanException):
    pass

class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def _discover_tests(self):
        """ This helper will go in the test folder, and look for individual
        test methods in there in order to create one single test for each

        Returns a list of tuple (filename, test_name) as args to pass
        to openstudio CLI
        eg: [(test_file, test_name), (test_file, test_name2)]
        """
        test_folder = os.path.join(self.source_folder, "test")

        # Glob all tests files
        glob_pattern = os.path.join(test_folder, "test*.rb")
        # glob_pattern = os.path.join(self.package_folder, glob_pattern)

        test_files = gb.glob(glob_pattern, recursive=False)

        re_test = re.compile(r'def +(test_[A-Za-z_0-9 ]+)')
        all_test_args = []
        for test_file in test_files:

            rel_path = os.path.relpath(test_file, start=self.source_folder)

            with open(test_file, 'r') as f:
                content = f.read()
            single_tests = re_test.findall(content)
            if not single_tests:
                self.output.warn("Did not find any test_ methods in "
                                 "{}".format(rel_path))
            for single_test in single_tests:
                all_test_args.append((test_file, single_test))

        return all_test_args

    def test(self):
        cli_path = os.path.abspath("openstudio")
        print("CWD={}".format(os.path.abspath('.')))
        print("source_folder={}".format(os.path.abspath(self.source_folder)))

        # No point in trying to run tests if the --help doesn't even work
        self.output.info("Running openstudio --help")
        self.run('{} --help'.format(cli_path))

        all_test_args = self._discover_tests()
        failed_tests = []
        for test_arg in all_test_args:
            cmd = "{} {} --name={}".format(cli_path, test_arg[0], test_arg[1])
            self.output.info(cmd)
            # Run all tests even if failed, we'll unwind later
            try:
                self.run(cmd)
            except ConanException:
                failed_tests.append(test_arg)

        if failed_tests:
            msg = "{} tests failed:".format(len(failed_tests))
            for failed_test in failed_tests:
                rel_path = os.path.relpath(failed_test[0],
                                           start=self.source_folder)
                msg += "\n * {}: {}".format(rel_path, failed_test[1])

            raise TestFailedException(msg)
