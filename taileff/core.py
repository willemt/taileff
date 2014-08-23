#!/usr/bin/env python

"""
Usage:
  tailf <file> [-s -i -n -l <language> -g <seconds>]
  tailf languages <lang_regex>
  tailf --version
  tailf --help

Options:
  -h --help                  Show this screen
  -l, --lang <language>      Language for syntax highlighting [default: guessing]
  -g, --grouping <seconds>   Group events by time; don't if 0 [default: 3]
  -s, --separator            Separate each event with a line
  -i, --indent               Indent output
  -n, --number               Number output

"""

VERSION = "0.1.0"

import os
import sys
import datetime
import re
import signal

import sqlparse
import tailer
from docopt import docopt
from termcolor import colored
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import get_lexer_by_name, guess_lexer


def print_grouping_separator(**kwargs):
    (width, _) = getTerminalSize()
    kwargs['events_plural'] = 's' if 1 < kwargs['events'] else ''
    text = " {events} event{events_plural}, {seconds}s elapsed ".format(**kwargs)
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


def go(args):
    f = open(args['<file>'])
    time_since_last = None
    events = 0
    for line in tailer.follow(f):
        events += 1

        if not int(0 == args['--grouping']):
            now = datetime.datetime.now()
            if time_since_last:
                diff = now - time_since_last
                if int(args['--grouping']) < diff.seconds:
                    print_grouping_separator(seconds=diff.seconds,
                                             events=events)
                    events = 0
            time_since_last = now

        if 'guessing' == args['--lang']:
            lexer = guess_lexer(line)
        else:
            lexer = get_lexer_by_name(args['--lang'])

        if args['--indent'] and args['--lang'] == 'sql':
            line = sqlparse.format(line, reindent=True, keyword_case='upper')

        text = highlight(line, lexer, Terminal256Formatter())

        if not args['--separator'] and args['--number']:
            sys.stdout.write('{0} '.format(str(events).zfill(3)))

        print(text.strip())

        if args['--separator']:
            msg = '{0}'.format(str(events).zfill(3)) if args['--number'] else ''
            print_separator(msg)


def get_language(lang):
    from pygments.lexers import get_all_lexers
    potentials = set()
    for lexer in get_all_lexers():
        potentials.update(set([name for name in lexer[1] if re.match(lang, name)]))
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
        if 'guessing' != args['--lang']:
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
