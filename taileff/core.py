#!/usr/bin/env python

"""
Usage:
  tailf <file>
    [-s -i -n -d -l <language> -g <seconds>]
  tailf languages <lang_regex>
  tailf --version
  tailf --help

Options:
  -h --help                  Show this screen
  -l, --lang <language>      Language for syntax colouring [default: guessing]
  -g, --grouping <seconds>   Group events by time; don't if 0 [default: 1]
  -s, --separator            Separate each event with a line
  -i, --indent               Indent output
  -n, --number               Number output
  -d, --show-duplicates      Mark duplicate lines

"""

VERSION = "0.2.0"

import os
import sys
import datetime
import time
import re
import signal
import hashlib
import collections

import sqlparse
from docopt import docopt
from termcolor import colored
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import get_lexer_by_name, guess_lexer, get_all_lexers


class FileTypeRegister(object):
    files = {}

    def add(self, cls):
        self.files[cls.filename] = cls
        return cls

filetypes = FileTypeRegister()


@filetypes.add
class FileDjangoSqlLog:
    stamp_regex = '^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}\] \(\d+.\d+\) '
    filename = 'django_sql.log'
    syntax = 'sql'


def print_grouping_separator(**kwargs):
    (width, _) = getTerminalSize()
    kwargs['events_plural'] = 's' if 1 < kwargs['events'] else ''
    text = " {events} event{events_plural}, "\
           "{seconds}s elapsed, "\
           "{unique_events} unique events".format(**kwargs)
    print(colored(text + " " * (width - len(text)), 'white', attrs=['reverse']))


def print_separator(msg):
    (width, _) = getTerminalSize()
    print(("-" * (width - len(msg))) + msg)


def getTerminalSize():
    env = os.environ

    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import termios
            import struct
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))
    return int(cr[1]), int(cr[0])


def follow(file, timeout_seconds):
    """
    Source: pytailer
    """
    trailing = True
    line_terminators = ('\r\n', '\n', '\r')
    delay = 1.0
    seconds_waiting = 0
    lines_read = 0

    # move to end of file
    file.seek(0, 2)

    while 1:
        where = file.tell()
        line = file.readline()
        if line:
            if trailing and line in line_terminators:
                # This is just the line terminator added to the end of the file
                # before a new line, ignore.
                trailing = False
                continue

            if line[-1] in line_terminators:
                line = line[:-1]
                if line[-1:] == '\r\n' and '\r\n' in line_terminators:
                    # found crlf
                    line = line[:-1]

            trailing = False
            seconds_waiting = 0
            lines_read += 1
            yield line
        else:
            if trailing and 0 < lines_read and 0 < timeout_seconds:
                seconds_waiting += delay
                if timeout_seconds <= seconds_waiting:
                    lines_read = 0
                    yield None
            trailing = True
            file.seek(where)
            time.sleep(delay)


class Grouping(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.events = 0
        self.dupes = collections.defaultdict(lambda: {'count': 0})
        self.since = datetime.datetime.now()


def go(args):
    f = open(args['<file>'])
    basename = os.path.basename(args['<file>'])
    filetype = filetypes.files.get(basename, None)
    group = Grouping()

    for line in follow(f, int(args['--grouping'])):
        if not line:
            now = datetime.datetime.now()
            print_grouping_separator(
                seconds=(now - group.since).seconds - int(args['--grouping']),
                events=group.events,
                unique_events=len(group.dupes))
            group.clear()
            continue

        prefix = ''
        group.events += 1

        if 0 < int(args['--grouping']):
            item = re.sub(filetype.stamp_regex, '', line) if filetype else line
            m = hashlib.md5()
            m.update(item)
            dupe = group.dupes[m.digest()]
            dupe['count'] += 1
            if 1 < dupe['count']:
                if '#' not in dupe:
                    dupe['#'] = len([c for c in group.dupes.values() if 1 < c['count']])
                if '--show-duplicates' in args:
                    msg = ' duplicate #{#} count:{count} '.format(**dupe)
                    prefix += colored(msg, 'red', attrs=['reverse']) + ' '

        if 'guessing' == args['--lang']:
            lexer = guess_lexer(line)
        else:
            lexer = get_lexer_by_name(args['--lang'])

        if args['--indent'] and args['--lang'] == 'sql':
            line = sqlparse.format(line, reindent=True, keyword_case='upper')

        text = highlight(line, lexer, Terminal256Formatter())

        if not args['--separator'] and args['--number']:
            sys.stdout.write('{0} '.format(str(group.events).zfill(3)))

        try:
            print(prefix + text.strip())
        except UnicodeEncodeError:
            print(prefix + text.encode('utf-8').strip())

        if args['--separator']:
            msg = '{0}'.format(str(group.events).zfill(3)) if args['--number'] else ''
            print_separator(msg)


def get_language(lang):
    potentials = set()
    for lexer in get_all_lexers():
        potentials.update(set([l for l in lexer[1] if re.match(lang, l)]))
    return sorted(list(potentials))


def main():
    def signal_handler(signal, frame):
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    args = docopt(__doc__, version=VERSION)
    if args['--version']:
        print VERSION
        exit(0)
    elif args['languages']:
        print ", ".join(get_language(args['<lang_regex>']))
        exit(0)
    elif args['<file>']:
        lang = None
        if args['--lang'] == 'guessing':
            basename = os.path.basename(args['<file>'])
            if basename in filetypes.files:
                args['--lang'] = filetypes.files[basename].syntax
        else:
            lang = get_language('^{0}$'.format(args['--lang']))
            if 0 == len(lang):
                print('Error: Invalid language {0}\n'.format(args['--lang']))
                exit(1)
            if 1 < len(lang):
                print('Error: Choose a single language {0}\n'.format(lang))
                exit(1)
    go(args)


if __name__ == '__main__':
    main()
