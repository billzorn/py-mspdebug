import settings
import manager
import interface

import pexpect
from pexpect.replwrap import REPLWrapper
import os


def logpath(tty):
    return os.path.join(settings.log_dir, tty+'.log')

log_error_re = settings.make_log_error_re()

class NoTTYError(Exception):
    pass


class Mspdebug(object):
    def __init__(self):
        self.tty = None
        self.log_f = None
        self.spawn = None
        self.repl = None

    def open_log(self):
        if not os.path.isdir(settings.log_dir):
            os.makedirs(settings.log_dir, exist_ok=True)
        self.log_f = open(logpath(self.tty), 'at')
        self.log_f.write(settings.make_log_spacer())
        self.log_f.flush()

    # I don't know if pexpect does this for us, but it probably doesn't hurt.
    def close_log(self):
        self.log_f.close()

    # This is kind of a stupid hack, but it looks like REPLWrapper blows away any
    # info that would let us pull this out of the pexpect.spawn object directly.
    def get_error_from_log(self):
        self.log_f.flush()
        with open(logpath(self.tty), 'rb') as f:
            try:
                f.seek(-settings.log_error_window, 2)
                logtail = f.read(1024).decode()
            except OSError:
                # Seek can fail if the file is to short, so just read the whole thing.
                f.seek(0)
                logtail = f.read().decode()
        codes = log_error_re.findall(logtail)
        try:
            error_code = int(codes[-1])
        except Exception:
            error_code = None
        return error_code
            
    def start_repl(self):
        repl = None
        
        while repl is None:
            tty = manager.get_tty()
            if tty is None:
                raise NoTTYError
            else:
                self.tty = tty

            mspargs = [settings.mspdebug_driver, '-d', self.tty]
            self.open_log()

            try:
                P = pexpect.spawn('mspdebug', mspargs, encoding='ascii', logfile=self.log_f)
                R = REPLWrapper(P, '(mspdebug) ', None)
                manager.claim_tty(self.tty, P.pid)
                spawn = P
                repl = R
            except pexpect.EOF:
                #import pdb; pdb.set_trace()
                error_code = self.get_error_from_log()
                if error_code in settings.errors_to_mark:
                    manager.mark_tty(self.tty)
                self.close_log()

        self.spawn = spawn
        self.repl = repl

    def exit_repl(self):
        try:
            self.repl.run_command('exit')
        except pexpect.EOF:
            manager.release_tty(self.tty)
        else:
            print('failed to release tty {}'.format(repr(self.tty)))

    def __enter__(self):
        self.start_repl()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit_repl()
        self.close_log()

    def run(self, cmd):
        return self.repl.run_command(cmd)

    # replwrap isn't going to like the non-returning run procedure of mspdebug...

    def interrupt(self):
        self.spawn.sendintr()
