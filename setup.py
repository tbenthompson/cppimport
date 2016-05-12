from setuptools import setup

setup(
    packages = ['cppimport'],
    install_requires = ['pybind11'],
    zip_safe = False

    name = 'cppimport',
    version = '0.0.1',
    description = 'Import C++ files directly from python!',
    long_description = """cppimport is a small import hook that determines whether there is a C++ source file that matches the requested module. If there is, the file is compiled as an extension and placed in the same folder as the C++ source file. The standard module loading capabilities of python then load the module.""",
    url = 'https://github.com/tbenthompson/cppimport',
    author = 'T. Ben Thompson',
    author_email = 't.ben.thompson@gmail.com',
    license = 'MIT',
    platforms = ['any'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: C++'
    ]
)
