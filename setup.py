"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
import os

from setuptools import setup, find_packages

# pylint: disable=redefined-builtin

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.rst"), encoding="utf-8") as fid:
    long_description = fid.read()

with open(os.path.join(here, "requirements.txt"), encoding="utf-8") as fid:
    install_requires = [line for line in fid.read().splitlines() if line.strip()]

setup(
    name="aas-core3.0-testgen",
    version="0.0.1",
    description="Generate test data based on the meta-model V3.0.",
    long_description=long_description,
    url="https://github.com/aas-core-works/aas-core-codegen",
    author="Marko Ristin",
    author_email="marko@ristin.ch",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    license="License :: OSI Approved :: MIT License",
    keywords="asset administration shell code generation industry 4.0 industrie i4.0",
    packages=find_packages(exclude=["tests", "continuous_integration", "dev_scripts"]),
    install_requires=install_requires,
    # fmt: off
    extras_require={
        "dev": [
            "black==22.3.0",
            "mypy==0.950",
            "pylint==2.13.8",
            "pydocstyle>=2.1.1<3",
            "coverage>=6,<7",
            "twine",
            "aas-core-meta@git+https://github.com/aas-core-works/aas-core-meta@8f18a8c#egg=aas-core-meta",
            "aas-core-codegen@git+https://github.com/aas-core-works/aas-core-codegen@0e16f63#egg=aas-core-codegen",
            "hypothesis==6.46.3",
            "xmlschema==1.10.0",
            "jsonschema==4.17.3",
        ]
    },
    # fmt: on
    py_modules=["aas_core3_0_testgen"],
    package_data={"aas_core3_0_testgen": ["py.typed"]},
    data_files=[(".", ["LICENSE", "README.rst", "requirements.txt"])],
)
