#!/usr/bin/env python

import manager
import driver

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

    if go:
        with driver.Mspdebug() as mspdebug:
            print('mspdebug on {}'.format(mspdebug.tty))
            sys.stdout.flush()
            
            for line in sys.stdin:
                print(mspdebug.run(line.strip()))
                sys.stdout.flush()

    exit(0)
