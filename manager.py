import settings

import os
import subprocess
import io
import fcntl
import json

def lstty():
    ls = subprocess.check_output(['ls', settings.tty_dir]).decode()
    return [line.strip() for line in ls.split('\n') if settings.tty_name in line]

def suser(tty):
    fuser = subprocess.Popen(['fuser', os.path.join(settings.tty_dir, tty)],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = fuser.communicate()
    returncode = fuser.wait()

    if returncode == 0:
        return int(stdout.decode().strip())
    else:
        return None

def psname(pid):
    ps = subprocess.Popen(['ps', 'chp', str(pid)],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = ps.communicate()
    returncode = ps.wait()

    fields = stdout.decode().split()
    if returncode == 0 and len(fields) > 0:
        return fields[-1]
    else:
        return None

def hasopen(pid, tty):
    lsof = subprocess.Popen(['lsof', '-p', str(pid)],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = lsof.communicate()
    returncode = lsof.wait()
    
    if returncode == 0:
        return os.path.join(settings.tty_dir, tty) in stdout.decode()
    else:
        return False

def status_exists():
    return os.path.isfile(settings.status_path)

def status_init():
    os.makedirs(settings.status_dir, exist_ok=True)
    with open(settings.status_path, 'wt'):
        pass

# this is slow due to many .1s calls to fuser
def status_new():
    ttys = lstty()
    status = {tty : suser(tty) for tty in ttys}
    return status

# use as a context manager to wrap flock-ed updates to a global status file
class Status(object):
    def __init__(self):
        self.status = None
        self.status_f = None
        
        self.open_status()

    def open_status(self):
        if not status_exists():
            status_init()
        self.status_f = open(settings.status_path, 'r+t')

    def close_status(self):
        self.status_f.close()

    def import_status(self):        
        fcntl.flock(self.status_f, fcntl.LOCK_EX)
        self.status_f.seek(0, io.SEEK_SET)
        try:
            status = json.load(self.status_f)
        except json.decoder.JSONDecodeError:
            status = status_new()
        self.status = status

    def export_status(self):
        self.status_f.seek(0, io.SEEK_SET)
        json.dump(self.status, self.status_f, indent=2, sort_keys=True)
        self.status_f.write('\n')
        self.status_f.truncate()
        self.status_f.flush()
        fcntl.flock(self.status_f, fcntl.LOCK_UN)

    def __enter__(self):
        self.import_status()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.export_status()
        self.close_status()


# primary API

# Check a given set of ttys and update the configuration in place.
def check(ttys, all_ttys = None):
    if all_ttys is None:
        all_ttys = lstty()
    with Status() as s:
        for tty in ttys:
            if tty in all_ttys:
                if tty in s.status:
                    p = s.status[tty]
                    if isinstance(p, int) and (psname(p) == settings.interpreter or hasopen(p, tty)):
                        # this entry appears to be a valid user; do nothing
                        pass
                    else:
                        user = suser(tty)
                        if isinstance(user, int):
                            # there appears to be another user, add them
                            s.status[tty] = user
                        elif isinstance(p, int):
                            # clear invalid label
                            s.status[tty] = None
                else:
                    # tty exists, but is not recorded in status, so add it
                    s.status[tty] = suser(tty)


# Check current configuration for consistency (quickly) and clear ttys marked
# as not connecting to mspdebug. Intended for use after changing physical device configuration.
def refresh():
    ttys = lstty()
    new_status = {tty : None for tty in ttys}
    with Status() as s:
        for tty in ttys:
            if tty in s.status:
                p = s.status[tty]
                if isinstance(p, int) and (psname(p) == settings.interpreter or hasopen(p, tty)):
                    new_status[tty] = p
        s.status = new_status

def display():
    status = None
    with Status() as s:
        status = s.status
    for tty in sorted(status):
        print('{:9s} : {}'.format(tty, repr(status[tty])))

# Reserve the next free tty for an mspdebug session. The TTY will be labeled according to the PID
# of the current python process.
def get_tty():
    free_tty = None
    with Status() as s:
        for tty in s.status:
            p = s.status[tty]
            if p is None:
                free_tty = tty
                s.status[tty] = os.getpid()
                break
    return free_tty

# Change the label of a tty session to the given pid, presumably an actual mspdebug process.
def claim_tty(tty, pid):
    with Status() as s:
        if tty in s.status:
            s.status[tty] = pid
        else:
            print('WARNING: claim_tty: no tty {} for pid {}'.format(repr(tty), repr(pid)))

# Remove the label of a tty session, presumably because the mspdebug process has exited.
def release_tty(tty):
    with Status() as s:
        if tty in s.status:
            s.status[tty] = None
        else:
            print('WARNING: release_tty: no tty {}'.format(repr(tty)))

# Mark that a tty does not connect to an mspdebug controller.
def mark_tty(tty):
    with Status() as s:
        if tty in s.status:
            s.status[tty] = settings.tty_mark
        else:
            print('WARNING: mark_tty: no tty {}'.format(repr(tty)))

# Report the current status of a single tty.
def check_tty(tty):
    with Status() as s:
        if tty in s.status:
            return s.status[tty]
        else:
            return None
