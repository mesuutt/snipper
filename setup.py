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
    description=('A command-line tool to manage Bitbucket snippets.'),
    license='MIT',
    test_suite='tests',
    keywords="bitbucket snippet gist command-line cli",
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
        "Environment :: Console",
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
    ],
)
