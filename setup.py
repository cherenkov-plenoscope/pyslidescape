import setuptools
import os


with open("README.rst", "r", encoding="utf-8") as f:
    long_description = f.read()

with open(os.path.join("pyslidescape", "version.py")) as f:
    txt = f.read()
    last_line = txt.splitlines()[-1]
    version_string = last_line.split()[-1]
    version = version_string.strip("\"'")

setuptools.setup(
    name="pyslidescape",
    version=version,
    description=("This is pyslidescape."),
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/cherenkov-plenoscope/pyslidescape",
    author="AUTHOR",
    author_email="AUTHOR@mail",
    packages=["pyslidescape", "pyslidescape.apps"],
    package_data={"pyslidescape": [os.path.join("resources", "*")]},
    install_requires=["img2pdf"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ],
    entry_points={
        "console_scripts": [
            "pyslidescape=pyslidescape.apps.main:main",
        ]
    },
)
