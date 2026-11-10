exec(open('/workspace/scratch/d96bc0fd2488/rules-audit/decode_tables.py').read().split('addr=')[0])
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
import re,json,subprocess
cs=Cs(CS_ARCH_ARM,CS_MODE_ARM);cs.skipdata=True
sym=e.get_section_by_name('.dynsym');records=[]
for st in sym.iter_symbols():
 if st['st_size']<30 or st['st_info']['type']!='STT_FUNC':continue
 code=get(st['st_value'],st['st_size'])
 if code is None:continue
 regs={}
 for ins in cs.disasm(code,st['st_value']):
  mn=ins.mnemonic;ops=ins.op_str.split(', ');old=regs.copy();pc=ins.address+8
  try:
   dst=ops[0]
   if mn in ['mov','movw'] and ops[1].startswith('#'):regs[dst]=int(ops[1][1:],0)
   elif mn=='movt' and ops[1].startswith('#'):regs[dst]=(regs.get(dst,0)&65535)|(int(ops[1][1:],0)<<16)
   elif mn=='ldr' and '[pc' in ins.op_str:
    mm=re.search(r'\[pc(?:, #(-?0x[0-9a-f]+|-?\d+))?\]',ins.op_str)
    if mm:regs[dst]=word(pc+(int(mm[1],0) if mm[1] else 0))
   elif mn in ['add','sub'] and len(ops)==3:
    a=pc if ops[1]=='pc' else regs.get(ops[1]);b=int(ops[2][1:],0) if ops[2].startswith('#') else regs.get(ops[2]);regs[dst]=None if a is None or b is None else (a+b if mn=='add' else a-b)&0xffffffff
   elif mn=='bl' and ins.op_str=='#0x14ecd8':
    a=regs.get('r0');n=regs.get('r1');x=get(a,n*2) if a and n and 0<n<3000000 else None
    if x:
     out=bytes(a^b for a,b in zip(x[:n],x[n:]));ascii=sum(32<=t<127 or t in [9,10,13,0] for t in out)/len(out)
     if ascii>.95:
      name=f'table-{a:x}.txt';Path('/workspace/scratch/d96bc0fd2488/rules-audit/'+name).write_bytes(out);records.append(dict(file=name,address=hex(a),length=n,call=hex(ins.address),function=st.name,head=out[:100].decode(errors='replace')))
  except Exception:pass
Path('/workspace/scratch/d96bc0fd2488/rules-audit/table-index.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
