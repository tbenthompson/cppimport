from setuptools import setup

description = open("README.md").read()

setup(
    use_scm_version={"version_scheme": "post-release"},
    setup_requires=["setuptools_scm"],
    packages=["cppimport"],
    install_requires=["mako", "pybind11", "filelock"],
    zip_safe=False,
    name="cppimport",
    description="Import C++ files directly from Python!",
    long_description=description,
    long_description_content_type="text/markdown",
    url="https://github.com/tbenthompson/cppimport",
    author="T. Ben Thompson",
    author_email="t.ben.thompson@gmail.com",
    license="MIT",
    platforms=["any"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Operating System :: POSIX",
        "Topic :: Software Development",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: C++",
    ],
)
