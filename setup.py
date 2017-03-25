import sys


from os.path import dirname, abspath, join
from setuptools import setup
from setuptools.command.test import test


class RunTests(test):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        test.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        from pytest import main

        sys.exit(main(self.pytest_args))


def get_requirements():
    requirements_file = join(dirname(abspath(__file__)), 'requirements.txt')

    return open(requirements_file).read().split()


setup(
    name="websvc",
    version="0.0.1",
    author="Ian Kinsey",
    description="Web application framework",
    license="MIT",
    packages=["websvc"],
    cmdclass={'test': RunTests},
    install_requires=get_requirements()
)
