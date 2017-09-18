from setuptools import setup

try:
   import pypandoc
   description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
   description = open('README.md').read()

setup(
    packages = ['cppimport'],

    install_requires = [
        'mako', 'pybind11'
    ],
    zip_safe = False,
    entry_points = {
        'console_scripts': [
            'cpprun=cppimport.cpprun:cpp_run'
        ]
    },

    name = 'cppimport',
    version = '17.09.18',
    description = 'Import C++ files directly from Python!',
    long_description = description,

    url = 'https://github.com/tbenthompson/cppimport',
    author = 'T. Ben Thompson',
    author_email = 't.ben.thompson@gmail.com',
    license = 'MIT',
    platforms = ['any'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: C++'
    ]
)
