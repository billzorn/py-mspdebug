import os
import time
import re

interpreter = 'python'
mspdebug = 'mspdebug'
mspdebug_driver = 'tilib'
mspdebug_prompt = '(mspdebug) '

status_dir = '/tmp/py-mspdebug-1000'
status_fname = 'status.json'
status_path = os.path.join(status_dir, status_fname)

tty_name = 'ttyACM'
tty_dir = '/dev'
tty_mark = 'x'

log_dir = os.path.join(status_dir, 'logs')
log_error_window = 1024
errors_to_mark = {57}

def make_log_spacer():
    return '\n\n\n<<<< {} >>>>\n\n\n'.format(time.asctime())

def make_log_error_re():
    return re.compile(r'.*?\(error = ([0-9]+)\)', flags=re.DOTALL)
