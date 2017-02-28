import re

# mspdebug output parsing

reg_re = re.compile(r'\(\s*(PC|SP|SR|R[0-9]+)\s*:\s*([0-9A-F]+)\s*\)', flags=re.I)
rn_re = re.compile(r'R([0-9]+)', flags=re.I)
reg_ids = {
    'PC' : 0,
    'SP' : 1,
    'SR' : 2,
}

def reg_id(rn):
    if rn in reg_ids:
        return reg_ids[rn]
    else:
        match = rn_re.search(rn)
        if match:
            return int(match.group(1))
        else:
            raise ValueError('Unknown register identifier: {}'.format(repr(rn)))

def parse_regs(text):
    regs = reg_re.findall(text)
    iregs = {}
    for rn, x in regs:
        i = reg_id(rn)
        if i in iregs:
            raise ValueError('Duplicate register {}, in {}'.format(repr(rn), text))
        else:
            iregs[i] = int(x, 16)
    return [iregs[k] for k in sorted(iregs)]

mem_re = re.compile(r'\s*([0-9A-F]+):([\s0-9A-F]+)\|.*\|', flags=re.I)

def parse_mem(text):
    rows = reg_re.findall(text)
    base_addr = None
    data = []
    for addr, mem in rows:
        if base_addr is None:
            base_addr = addr
        data += [int(x, 16) for x in mem.split()]
    return base_addr, data
