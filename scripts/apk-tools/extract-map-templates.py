"""Extract the quest board templates (TINY, SMALL, MEDIUM, WIDE ...) from libapp.so.

CLayoutMgr::FillValidCellsTemplate compares the template name and then walks a
null-terminated table of cell names ("C3", "H6" ...) that it marks invalid on
the full 9x9 quest board.  This script follows that code with capstone and
writes the removed cells per template.
usage: extract-map-templates.py path/to/libapp.so out.json   (pip install capstone pyelftools)
"""
import sys, struct, json
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

lib, out_path = sys.argv[1:3]
data = open(lib, 'rb').read()
elf = ELFFile(open(lib, 'rb'))

def off(v):
    for s in elf.iter_segments():
        if s['p_type'] == 'PT_LOAD' and s['p_vaddr'] <= v < s['p_vaddr'] + s['p_filesz']:
            return v - s['p_vaddr'] + s['p_offset']
def u32(v): return struct.unpack_from('<I', data, off(v))[0]
def cstr(v):
    o = off(v); return data[o:data.index(b'\0', o)].decode()

sym = next(s for s in elf.get_section_by_name('.dynsym').iter_symbols() if s.name == '_ZN10CLayoutMgr22FillValidCellsTemplateER8RZStringR7tLAYOUT')
start, size = sym['st_value'], sym['st_size']
regs, name, out = {}, None, {}
loop = None
for i in Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[off(start):off(start) + size], start):
    m, o = i.mnemonic, i.op_str
    if loop is None and m == 'ldr' and o.startswith('sb, [r5]'):
        loop = i.address
    if m.startswith('ldr') and '[pc, #' in o:
        regs[o.split(',')[0]] = u32(i.address + 8 + int(o.split('#')[1].rstrip(']'), 16))
    elif m.startswith('add') and ', pc, ' in o:
        r = o.split(',')[0]; regs[r] = (regs[r] + i.address + 8) & 0xffffffff
        if r == 'r1': name = cstr(regs['r1'])
    elif m.startswith('add') and o.startswith('r5, r5, #'):
        regs['r5'] += int(o.split('#')[1], 16)
    elif (m.startswith('b') and loop and hex(loop) in o) or (m == 'ldr' and o.startswith('sb, [r5]')):
        if name and 'r5' in regs and name not in out:
            t, cells = regs['r5'], []
            while (p := u32(t)):
                cells.append(cstr(p)); t += 4
            out[name] = cells
json.dump(out, open(out_path, 'w'), indent=1)
print({k: len(v) for k, v in out.items()})
