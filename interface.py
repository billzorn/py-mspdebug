import settings

import sys

def prot_ack(f_out):
    f_out.write('\n')
    f_out.flush()

def prot_execute(mspdebug, f_out, args):
    if len(args) < 1:
        f_out.write('error: no command')
        return

    cmd = args[0]
        
    if cmd == settings.prot_reset:
        mspdebug.reset()
        
    elif cmd == settings.prot_prog:
        try:
            fname = args[1]
        except Exception as e:
            f_out.write('error: {}: input: {}'.format(settings.prot_prog, repr(e)))
        else:
            mspdebug.prog(fname)

    elif cmd == settings.prot_mw:
        try:
            addr = int(args[1], 16)
            pattern = [int(x, 16) for x in args[2:]]
            assert len(pattern) > 0
        except Exception as e:
            f_out.write('error: {}: intput: {}'.format(settings.prot_mw, repr(e)))
        else:
            mspdebug.mw(addr, pattern)

    elif cmd == settings.prot_fill:
        try:
            addr = int(args[1], 16)
            size = int(args[2])
            pattern = [int(x, 16) for x in args[3:]]
            assert len(pattern) > 0
        except Exception as e:
            f_out.write('error: {}: intput: {}'.format(settings.prot_fill, repr(e)))
        else:
            mspdebug.fill(addr, size, pattern)

    elif cmd == settings.prot_setreg:
        try:
            rn = int(args[1])
            x = int(args[2], 16)
        except Exception as e:
            f_out.write('error: {}: intput: {}'.format(settings.prot_setreg, repr(e)))
        else:
            mspdebug.setreg(rn, x)

    elif cmd == settings.prot_md:
        try:
            addr = int(args[1], 16)
            size = int(args[2])
        except Exception as e:
            f_out.write('error: {}: intput: {}'.format(settings.prot_md, repr(e)))
        else:
            data = mspdebug.md(addr, size)
            f_out.write(' '.join('{:#x}'.format(x) for x in data))

    elif cmd == settings.prot_regs:
        data = mspdebug.regs()
        f_out.write(' '.join('{:#x}'.format(x) for x in data))

    elif cmd == settings.prot_step:
        data = mspdebug.step()
        f_out.write('{:#x}'.format(data))

    elif cmd == settings.prot_run:
        try:
            interval = float(args[1])
        except Exception as e:
            f_out.write('error: {}: intput: {}'.format(settings.prot_run, repr(e)))
        else:
            data = mspdebug.run(interval=interval)
            f_out.write('{:#x}'.format(data))

    else:
        f_out.write('error: unknown command {}'.format(cmd))

# start text protocol for communication with other tools
def protocol(mspdebug, f_in = sys.stdin, f_out = sys.stdout):
    for line in f_in:
        args = line.split()
        prot_execute(mspdebug, f_out, args)
        prot_ack(f_out)

def prompt(f_out):
    f_out.write('(py-mspdebug) ')
    f_out.flush()

# start command line repl
def repl(mspdebug, f_in = sys.stdin, f_out = sys.stdout):
    prompt(f_out)
    for line in f_in:
        args = line.split()
        if len(args) < 1:
            pass
        else:
            cmd = args[0]
            if cmd == 'run':
                f_out.write(repr(mspdebug.run_continue()))
                prot_ack(f_out)
            elif cmd == 'int':
                f_out.write(mspdebug.interrupt())
                prot_ack(f_out)
            elif cmd == 'prot':
                prot_execute(mspdebug, f_out, args[1:])
                prot_ack(f_out)
            else:
                # pass through
                f_out.write(mspdebug.run_command(' '.join(args)))
                prot_ack(f_out)
        prompt(f_out)
    prot_ack(f_out)
