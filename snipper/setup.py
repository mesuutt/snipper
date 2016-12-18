'''
Setup script.
To install snipper:
[sudo] python setup.py install
'''

import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


# Dynamically calculate the version based on snipper.VERSION.
setup(
    name='snipper',
    version=__import__('snipper').__version__,
    url='https://github.com/mesuutt/snipper',
    author='Mesut Tasci',
    author_email='mst.tasci@gmail.com',
    description=('A command-line interface for creating, listing, and editing Bitbucket Snippets.'),
    license='MIT',
    test_suite='tests',
    keywords="bitbucket snippet gist command line cli",
    long_description=read('README.md'),
    entry_points={
        'console_scripts': [
            'sp = snipper.__main__:main',
        ]
    },
    packages=['snipper'],
    install_requires=[
        'requests',
        'click',
        'pyperclip'
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        "Environment :: Console",
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
