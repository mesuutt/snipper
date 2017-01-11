Manage Bitbucket snippets from command line easy
=================================================


## Synopsis

```bash
Usage: snipper [OPTIONS] COMMAND [ARGS]...

Options:
  -C, --config PATH       Config file path: Default: $HOME/.snipperrc
  --no-color              Don't colorize output
  -h, --help              Show this message and exit.

Commands:
  add   Add file[s] to snippet
  edit  Edit snippet file
  ls    List local snippets
  new   Create new snippet from file[s]/STDIN
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

If you dont give any parameter to `add` command, snipper open an fuzzy snippet finder prompt
for selecting which snippet to add file and open default editor you can write content of file.
After you save and close editor new file will be added to selected snippet.

    snipper add

‌Or you can add existing file to snippet:

    snipper add [snippetId] a.py

If you dont specify snippet id, snipper open a fuzzy directory selection promt for selecting snippet.

    snipper add foo.txt bar.txt

Also you can read file content from clipboard(`-P`) or STDIN with redirecting output to snipper.

    snipper add -f foo.txt < *.txt
    snipper add -P

If you dont specify file name with `-f` option, `default_filename` config using as the file name.

### Editing snippet files

You should give path of snippet file for editing.
But if you dont give a path snipper opens a prompt for finding file with
fuzzy search and find file:

    snipper edit
    snipper edit Ahg2l/notes.md


### Pulling Changes

You can get new changes from Bitbucket with pull command

    snipper pull


### Syncing snippets

`sync` pull new changes from Bitbucket and push local changes to Bitbucket

    snipper sync


To list all snippets

    snipper ls

‌See `snipper --help` for more detail.
Also you can get help for specified command as below:

    snippet new --help


## Login

Bitbucket does not support token authenticaion for user for now. But you can
create an app password permitted only to snippets on Bitbucket settings page.
Anybody can't login or access to your bitbucket data with given username/password
except make request to Bitbucket API for snippets.

## Configuration

Snipper reads configs from `~/.snipperrc` if not unless otherwise stated.

.snipperrc example:

```
[snipper]

# Bitbucket credentials
username=mesuutt
# App password for authenticating to Bitbucket API.
password=aa11bb33cc55

# If you dont give filename with `-f` parementer while creating/adding new files
# this name is using as file name.
default_filename=file.md

# Auto push changes to remote after add/edit snippet file
auto_push=on

# Colorizing output by default. But you can disable it with `colorize=off` or using `--no-color` option
colorize=on
```

‌If you want to keep snipper config file another location, you can use `-C`
to be the default when you use the snipper executable, add an
alias to your `~/.bashrc` (or equivalent). For example:

    alias sp='snipper -C ~/dotfiles/snipperrc'

‌If you'd prefer snipper to open a different browser, then you can export the BROWSER
environment variable:

    export BROWSER=google-chrome

Also if you didn't specified `username` and `password` in config file, you should set `SNIPPER_USERNAME` and `SNIPPER_PASSWORD` environment variables.

If you need to use an proxy to access the internet, export the `HTTP_PROXY` or
`HTTPS_PROXY` environment variable and snipper will use it.

Licensed under the [MIT license](http://opensource.org/licenses/MIT). Bug-reports, and pull requests are welcome.
