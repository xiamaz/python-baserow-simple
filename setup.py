"""Python setup.py for python_baserow_simple package"""
import io
import os
from setuptools import find_packages, setup


def read(*paths, **kwargs):
    """Read the contents of a text file safely.
    >>> read("python_baserow_simple", "VERSION")
    '0.1.0'
    >>> read("README.md")
    ...
    """

    content = ""
    with io.open(
        os.path.join(os.path.dirname(__file__), *paths),
        encoding=kwargs.get("encoding", "utf8"),
    ) as open_file:
        content = open_file.read().strip()
    return content


def read_requirements(path):
    return [
        line.strip()
        for line in read(path).split("\n")
        if not line.startswith(('"', "#", "-", "git+"))
    ]


setup(
    name="python_baserow_simple",
    version=read("python_baserow_simple", "VERSION"),
    description="Awesome python_baserow_simple created by xiamaz",
    url="https://github.com/xiamaz/python-baserow-simple/",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="xiamaz",
    packages=find_packages(exclude=["tests", ".github"]),
    install_requires=read_requirements("requirements.txt"),
    entry_points={
        "console_scripts": ["python_baserow_simple = python_baserow_simple.__main__:main"]
    },
    extras_require={"test": read_requirements("requirements-test.txt")},
)
