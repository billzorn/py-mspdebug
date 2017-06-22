#!/usr/bin/env python

import manager
import driver
import interface
import elftools

import argparse
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--refresh', action='store_true',
                        help='refresh configuration')
    parser.add_argument('-c', '--check', default='', metavar='TTYS',
                        help='check status of a comma-separated list of ttys')
    parser.add_argument('-l', '--list', action='store_true',
                        help='print current status')
    parser.add_argument('-g', '--get', default='', metavar='TTYS',
                        help='get status of a comma-separated list of ttys')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='launch a human-usable repl')
    parser.add_argument('-loadelf',
                        help='load an elf file (not for human consumption)')

    args = parser.parse_args()
    go = True

    if args.loadelf:
        elfname = args.loadelf
        try:
            mem_blocks, reg_blocks = elftools.load(elfname, restore_regs=False, verbosity=0)
            sys.stdout.write('{:d}\n'.format(len(mem_blocks)))
            sys.stdout.flush()
            for addr in mem_blocks:
                sys.stdout.write('{:#x}\n'.format(addr))
                sys.stdout.write(' '.join('{:#x}'.format(x) for x in mem_blocks[addr]))
                sys.stdout.write('\n')
                sys.stdout.flush()
        except Exception as e:
            sys.stdout.write('error: loadelf\n')
            sys.stdout.flush()
            exit(1)
        exit(0)
    
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
        try:
            with driver.Mspdebug() as mspdebug:
                sys.stdout.write('{:s}\n'.format(mspdebug.tty))
                sys.stdout.flush()

                if args.interactive:
                    interface.repl(mspdebug, f_in=sys.stdin, f_out=sys.stdout)
                else:
                    interface.protocol(mspdebug, f_in=sys.stdin, f_out=sys.stdout)
        except driver.NoTTYError:
            sys.stdout.write('error: no available port for mspdebug\n')
            sys.stdout.flush()
            exit(2)

    exit(0)
