Manage Bitbucket snippets from command line easy
=================================================


## Synopsis

```bash
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
```

## Installation

You can install snipper shown as below:

    python setup.py install


### Creating new snippet

Create a snippet from the contents of `foo.py` just:

    snipper new foo.py

Create snippet from multiple files:

    snipper new a b c
    snipper new *.py

‌By default it reads from STDIN, and you can set a filename with `-f`.

    snipper new -f test.py < a.py

‌Alternatively, you can just paste from the clipboard:

    snipper new -P

snipper creates snippets private by default. ‌Use `-p` to make the gist public:

    snipper new -p a.py

‌Use `-t` to add title to snippet:

    snipper new -t "Postgresql notes" postgres.md

‌If you'd like to copy the resulting URL to your clipboard, use `-c`.

    snipper new -c a.py

And you can just ask snipper to open created snippet on a browser tab with `-o`.

    snipper new -o < a.md

### Adding files to existing snippet

You can add existing file to snippet:

    snipper add [snippetId] a.py

If you don't give snippet id to `add` command, snipper open an fuzzy snippet selection prompt
which snippet to add file to.

    snipper add foo.py

Also if you don't give a file to snipper, snipper opens a new file with your default editor.
After you save and close editor new file will be added to selected snippet.

    snipper add

Also you can read content from clipboard(`-P`) or STDIN with redirecting output to snipper.

    cat *.txt | snipper add -f foo.txt
    snipper add -P

If you didn't specified file name with `-f` option, `default_filename` config using as the file name.

### Editing snippet files

You should give path of snippet file for editing.
    snipper edit

If you don't give a path, snipper opens a prompt for file selection with
fuzzy search:

    snipper edit Ahg2l/notes.md


### Pulling/Syncing snippets

If you make changes snippets on bitbucket.org website, you can get new changes from
Bitbucket with `pull` command

    snipper pull

If you disabled auto pushing feature from config file you should sync snippets manually.
`sync` pushes unpushed local changes to Bitbucket and pull new changes from Bitbucket if exist:

    snipper sync

‌See `snipper --help` for more detail.
Also you can get help for specified command as below:

    snippet new --help

------

## Login

Bitbucket does not support token authenticaion for users for now. But you can
create an app password permitted only to snippets on Bitbucket settings page.
Anybody can't login or access to your bitbucket data with given username/password
except make request to Bitbucket API for youur snippets.

Bitbucket snippets are git or mercurial repositories. So while pulling changes from Bitbucket or pushing changes to Bitbucket requires to public key authentication. So you should use ssh-agent for not typing password while pull/push every snippet.

## Configuration

When you run snipper first time snipper create a config file in your home directory by default.


Config file example with defaults:

```
[snipper]
username=
password=
auto_push=on
default_filename=file.txt
colorize=on
```

**username**, **password**: Using for authenticating to Bitbucket API

**default_filename** : If you don't specified filename with `-f` parementer while creating new snippet or adding new files to snippet this name using as file name.

**auto_push** : If this option enabled, snipper pushes changes after `new`,`add` and `edit` command executed.

**colorize** : Snipper colorizing output by default. But you can disable colorizing in config file. Also you can use `--no-color` option with any snipper command.

‌If you want to keep snipper config file another location, you can use `-C`
to be the default when you use the snipper executable, add an
alias to your `~/.bashrc` (or equivalent). For example:

    alias sp='snipper -C ~/dotfiles/snipperrc'


### Environment variables

`SNIPPER_USERNAME`,  `SNIPPER_PASSWORD`: Use this username and password instad reading from config file.

`HTTP_PROXY`, `HTTPS_PROXY`:  If you need to use an proxy to access the internet, use one of these environment variables and snipper will use it.

`BROWSER` : Use specified browser for opening snippets in browser.

------
‌
Licensed under the [MIT license](http://opensource.org/licenses/MIT). Bug-reports, and pull requests are welcome.
