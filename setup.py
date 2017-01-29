import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='snipper',
    version=__import__('snipper').__version__,
    url='https://github.com/mesuutt/snipper',
    author='Mesut Tasci',
    author_email='mst.tasci@gmail.com',
    description=('A command-line tool for creating, listing, and editing Bitbucket snippets.'),
    license='MIT',
    test_suite='tests',
    keywords="bitbucket snippet gist commandline cli",
    long_description=read('README.rst'),
    entry_points={
        'console_scripts': [
            'snipper = snipper.snipper:cli',
        ]
    },
    packages=['snipper'],
    install_requires=[
        'requests>=2.12',
        'click>=6.7',
        'prompt_toolkit>=1.0',
        'pyperclip>=1.5',
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        "Environment :: Console",
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 2.7',
        'Intended Audience :: Developers',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
    ],
)
