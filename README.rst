snipper
================================================

Manage Bitbucket snippets from command line easy
-------------------------------------------------

.. image:: https://img.shields.io/pypi/l/snipper.svg
    :target: https://pypi.python.org/pypi/snipper

Usage
--------

.. code:: bash

    Usage: snipper [OPTIONS] COMMAND [ARGS]...

    Options:
      -C, --config PATH       Config file path: Default: $HOME/.snipperrc
      --no-color              Disable colorizing output
      -h, --help              Show this message and exit.

    Commands:
      ls    List local snippets
      new   Create new snippet from file[s]/STDIN
      add   Add file[s] to snippet
      edit  Edit snippet file
      pull  Update local snippets from Bitbucket.
      sync  Sync snippets with Bitbucket

Installation
~~~~~~~~~~~~~~~~~~~~

::

    pip install snipper


Creating new snippet
~~~~~~~~~~~~~~~~~~~~

Create a snippet from the contents of ``foo.py`` by just the following:

::

    snipper new foo.py

Create snippet from multiple files:

::

    snipper new a b c
    snipper new *.py

‌By default, it reads from STDIN, and you can set a filename with ``-f``
parameter.

::

    snipper new -f test.py < a.py

Alternatively, you can just paste from the clipboard:

::

    snipper new -P

Snipper creates snippets as private by default. ‌Use ``-p`` to make the
snippet public:

::

    snipper new -p a.py

Use ``-t`` parameter to add title to snippet:

::

    snipper new -t "Postgresql notes" postgres.md

If you'd like to copy the resulting URL to your clipboard, use ``-c``
parameter.

::

    snipper new -c a.py

And you can just ask snipper to open a created snippet on a browser tab
with ``-o``.

::

    snipper new -o < a.md

Adding files to existing snippet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can add existing file to a snippet:

::

    snipper add [snippetId] a.py

If you don't give snippet id to ``add`` command, snipper opens a fuzzy
snippet selection prompt in order to add file to the selected snippet.

::

    snipper add foo.py

Also if you don't add a file to snipper as parameter, snipper opens a
new file with your default editor.

After you save and close the editor, new file will be added to selected
snippet.

::

    snipper add

Also you can read content from clipboard by ``-P`` or by redirecting
output from STDIN to snipper.

::

    cat *.txt | snipper add -f foo.txt
    snipper add -P

If you didn't specified any file name with ``-f`` option,
``default_filename`` config will be used as the filename.

Editing snippet files
~~~~~~~~~~~~~~~~~~~~~

You should give the path of a snippet file for editing.

::

    snipper edit

If you don't give any path, snipper opens a fuzzy search prompt for file
selection:

::

    snipper edit Ahg2l/notes.md

Pulling/Syncing snippets
~~~~~~~~~~~~~~~~~~~~~~~~

If you make changes on snippets at bitbucket.org website, you can get
these changes from Bitbucket with ``pull`` command

::

    snipper pull

If you disabled auto pushing feature from config file, you should sync
snippets manually. ``sync`` pushes unpushed local changes to Bitbucket
and pull the new changes from Bitbucket if any exist:

::

    snipper sync

See ``snipper --help`` for more detail. Also you can get help for any
specified command as below:

::

    snippet new --help

--------------

Login
-----

Bitbucket does not support token authentication for users now, but you
can create an app password that is permitted only to snippets on
Bitbucket settings page. Nobody cannot login or access to your bitbucket
data with given username and password, except making request to
Bitbucket API for your snippets.

Bitbucket snippets are git or mercurial repositories. So, pulling
changes from Bitbucket or pushing changes to Bitbucket requires public
key authentication. Therefore, you can use ssh-agent not to enter
password at every snippet pull/push.

Configuration
-------------

When you run snipper for the first time, by default snipper creates a
config file in your home directory.

Config file example with defaults:

::

    [snipper]
    username=
    password=
    auto_push=on
    default_filename=file.txt
    colorize=on

**username**, **password**: Using for authenticating to Bitbucket API

**default\_filename** : If you did not specify filename with ``-f``
parameter, this name will be used as filename while creating a new
snippet or adding new files to a snippet.

**auto\_push** : If this option is enabled, snipper pushes changes after
``new``,\ ``add`` and ``edit`` commands are executed. Otherwise, you
need to push the changes manually.

**colorize** : By default, snipper colorizes the output, but you can
disable colorizing in config file. Also, you can use ``--no-color``
option with any snipper command.

If you want to keep snipper config file at another location different
from home directory, you can use ``-C`` parameter to be the default
location. Also you can add an alias to your ``~/.bashrc`` (or
equivalent). For example:

::

    alias sp='snipper -C ~/dotfiles/snipperrc'

Environment variables
~~~~~~~~~~~~~~~~~~~~~

``SNIPPER_USERNAME``, ``SNIPPER_PASSWORD``: Use this username and
password instead of reading from config file every time.

``HTTP_PROXY``, ``HTTPS_PROXY``: If you need to use a proxy to access
the internet, use one of these environment variables and snipper will
use it.

``BROWSER`` : Use specified browser for opening snippets in a browser.

--------------

Licensed under the `MIT license <http://opensource.org/licenses/MIT>`__.
