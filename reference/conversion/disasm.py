from elftools.elf.elffile import ELFFile
from capstone import *
import sys
with open('/workspace/scratch/d96bc0fd2488/apk-review/libCombatMonsters.so','rb') as f:
 e=ELFFile(f);cs=Cs(CS_ARCH_ARM,CS_MODE_ARM);sym=e.get_section_by_name('.dynsym')
 for s in sym.iter_symbols():
  if any(x in s.name for x in sys.argv[1:]):
   a=s['st_value'];size=s['st_size'];sec=e.get_section(s['st_shndx']);b=sec.data()[a-sec['sh_addr']:a-sec['sh_addr']+size];print('\n',s.name,hex(a),size)
   for i in cs.disasm(b,a):print(hex(i.address),i.mnemonic,i.op_str)
