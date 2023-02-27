"""
Errors
------

Exceptions and exception helpers.
"""


class AbrvalgSyntaxError(Exception):

    def __init__(self, message, line, column):
        super(AbrvalgSyntaxError, self).__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.type = "\033[91mSyntax Error\033[0m"


class AbrvalgCompileTimeError(Exception):

    def __init__(self, message, line, column):
        super(AbrvalgCompileTimeError, self).__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.type = "\033[91mCompileTime Error\033[0m"

class AbrvalgInternalError(Exception):

    def __init__(self, message, line, column):
        super(AbrvalgInternalError, self).__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.type = "\033[91mInternal Error\033[0m"


def report_syntax_error(lexer, error, size = 1):
    line = error.line
    column = error.column
    source_line = lexer.source_lines[line -1]
    print('{}: {}: {} at line {}, column {}'.format(lexer.filename, error.type, error.message, line, column))
    print('{} | {}'.format(line, source_line))
    print('{} | {}\033[91m{}\033[0m'.format(' ' * len(str(line)), '~' * (column-1), '^' * size) + '~' * (len(source_line) - ((column-1) + size)))
    exit(4)
