import os
import re

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.validation import Validator, ValidationError

from .snippet import Snippet
from . import utils


class BasePathCompleter(Completer):
    collection = []

    def get_completions(self, document, complete_event):
        # https://github.com/dbcli/pgcli/blob/master/pgcli/pgcompleter.py#L336
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        text_len = len(word_before_cursor)
        collection = self.fuzzyfinder(word_before_cursor, self.collection)
        matches = []

        for item in collection:
            matches.append(
                Completion(item, start_position=-text_len)
            )

        return matches

    @staticmethod
    def fuzzyfinder(user_input, collection):
        """Find text in collections"""
        suggestions = []
        pattern = '.*?'.join(user_input)   # Converts 'djm' to 'd.*?j.*?m'
        regex = re.compile(pattern, re.IGNORECASE)
        for item in collection:
            match = regex.search(item)
            if match:
                suggestions.append((len(match.group()), match.start(), item))

        return [x for _, _, x in sorted(suggestions)]


class SnippetFileCompleter(BasePathCompleter):

    def __init__(self, config):
        super(SnippetFileCompleter, self).__init__()

        data = utils.read_metadata(config)

        for item in data['values']:
            snippet = Snippet(config, item)
            if not snippet.get_path():
                continue

            file_dir = os.path.split(snippet.get_path())[1]
            for file_name in snippet.get_files():
                self.collection.append(os.path.join(file_dir, file_name))


class SnippetDirCompleter(BasePathCompleter):

    def __init__(self, config):
        super(SnippetDirCompleter, self).__init__()

        data = utils.read_metadata(config)

        for item in data['values']:
            snippet = Snippet(config, item)
            dir_name = snippet.get_slugified_dirname()
            if not dir_name:
                continue

            self.collection.append(dir_name)


class ValidateSnippetFile(Validator):

    def __init__(self, config):
        super(ValidateSnippetFile, self).__init__()
        self.config = config

    def validate(self, document):
        text_len = len(document.text)
        relative_path = document.text
        snippet_root = self.config.get('snipper', 'snippet_dir')

        if not os.path.exists(os.path.join(snippet_root, relative_path)):
            raise ValidationError(
                message="File not exist. Please select existing file or use 'add' or 'new' command.",
                cursor_position=text_len
            )


class ValidateSnippetDir(Validator):

    def __init__(self, config):
        super(ValidateSnippetDir, self).__init__()
        self.config = config

    def validate(self, document):
        text_len = len(document.text)
        snippet_dir = document.text
        snippet_root = self.config.get('snipper', 'snippet_dir')

        if not os.path.exists(os.path.join(snippet_root, snippet_dir)):
            raise ValidationError(message="Please select existing snippet", cursor_position=text_len)
