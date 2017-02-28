#!/usr/bin/env python

import manager
import driver
import interface

import argparse
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--refresh', action='store_true',
                        help='refresh configuration')
    parser.add_argument('-l', '--list', action='store_true',
                        help='print current status')
    parser.add_argument('-c', '--check', default='', metavar='TTYS',
                        help='check status of a comma-separated list of ttys')
    parser.add_argument('-g', '--get', default='', metavar='TTYS',
                        help='get status of a comma-separated list of ttys')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='launch a human-usable repl')

    args = parser.parse_args()
    go = True
    
    if args.refresh:
        manager.refresh()
        go = False
    if args.check:
        ttys = args.check.strip().split(',')
        manager.check(ttys)
        go = False
    if args.get:
        for tty in args.get.strip().split(','):
            print('{:9s} : {}'.format(tty, repr(manager.check_tty(tty))))
        go = False
    if args.list:
        manager.display()
        go = False

    if args.interactive or go:
        with driver.Mspdebug() as mspdebug:
            sys.stdout.write('{:s}\n'.format(mspdebug.tty))
            sys.stdout.flush()

            if args.interactive:
                interface.repl(mspdebug, f_in=sys.stdin, f_out=sys.stdout)
            else:
                interface.protocol(mspdebug, f_in=sys.stdin, f_out=sys.stdout)

    exit(0)
