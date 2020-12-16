# coding: utf-8
import os
import time

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(os.path.join(this_directory, "requirements.in"), encoding="utf-8") as f:
    requirements = f.read()
    requirements = [
        requirement
        for requirement in requirements.splitlines()
        if requirement and not requirement.startswith("#")
    ]

try:
    from setuptools import find_packages, setup
except ImportError:
    from distutils.core import find_packages, setup

if os.environ.get("CI_COMMIT_TAG"):
    # Development version of the package
    version = os.environ["CI_COMMIT_TAG"] + ".devel"
elif os.environ.get("CI_COMMIT_BRANCH"):
    if (
        os.environ["CI_COMMIT_BRANCH"].startswith("v")
        and "." in os.environ["CI_COMMIT_BRANCH"]
    ):
        # Production version of the package
        version = os.environ["CI_COMMIT_BRANCH"][1:]
    else:
        # Any other branch
        version = (
            f"{os.environ['CI_COMMIT_BRANCH']}.{os.environ['CI_COMMIT_SHORT_SHA']}"
        )
elif os.environ.get("CI_JOB_ID"):
    version = os.environ["CI_JOB_ID"]
else:
    version = time.strftime("%Y.%-m.%-d.%H%M")

setup(
    name="syntropycli",
    py_modules=["syntropycli"],
    version=version,
    url="https://github.com/SyntropyNet/syntropy-cli/",
    author="Andrius Mikonis",
    author_email="andrius@noia.network",
    description="Syntropy Universal Command Line Interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=requirements,
    packages=find_packages(exclude=["tests*"]),
    entry_points={"console_scripts": ["syntropyctl = syntropycli.__main__:main"]},
    python_requires=">=3.6",
    include_package_data=True,
    zip_safe=False,
    platforms="any",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
