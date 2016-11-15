# -*- coding: utf-8 -*-

import setuptools
import os

setuptools.setup(
    name="nionutils",
    version="0.0.1",
    author="Nion Software",
    author_email="swift@nion.com",
    description="Nion utility classes.",
    long_description=open("README.rst").read(),
    license="MIT",
    url="https://github.com/nion-software/nionutils",
    packages=setuptools.find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=['numpy'],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
    ],
    include_package_data=True,
    test_suite="nion.utils.test",
)
