from pathlib import Path
import sys,struct,json
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'deps'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from input_latch import INPUT_ADDRESS,INPUT_ASM
U=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x3a1000,0x1000),(0x432000,0x1000),(0x3e2000,0x1000),(0x10000000,0x4000),(0x20000000,0x1000)]:U.mem_map(a,n)
manifest=json.loads((p/'glove-scale-candidate/manifest.json').read_text());INPUT_ADDRESS=int(manifest['symbols']['input_entry'],16)
blob=(p/'glove-scale-candidate/code-cave.bin').read_bytes();U.mem_write(int(manifest['code_cave_address'],16),blob)
w=lambda a,v:U.mem_write(a,struct.pack('<I',v))
r=lambda a:struct.unpack('<I',U.mem_read(a,4))[0]
B=0x432000;M=0x10000000;C=M+0x2000
w(0x3e26bc,M);w(M+0xd0,1);w(M+0xd8,M+0x1000);w(M+0x1000,C)
regs=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12]
def step(phase,trigger,gate=1,interval=1):
 w(B+4,gate);w(B+12,interval);w(B+8,phase);w(C+4,trigger)
 for i,reg in enumerate(regs):U.reg_write(reg,0x12340000+i)
 U.reg_write(UC_ARM_REG_SP,0x20000ff0);U.reg_write(UC_ARM_REG_LR,0x3a1700)
 U.emu_start(INPUT_ADDRESS,0x3a1700,count=1000)
 assert all(U.reg_read(reg)==0x12340000+i for i,reg in enumerate(regs))
 return r(C+4),r(B+0x60)
assert step(1,1)==(1,1)
assert step(2,0)==(1,0)
assert step(3,0)==(0,0)
assert step(4,0)==(0,0)
assert step(6,2)==(2,0)
assert step(7,1)==(1,1)
assert step(8,2)==(3,0)
w(B+0x60,8);assert step(9,4,gate=0)==(4,0)
w(B+0x60,8);assert step(10,4,interval=2)==(4,0)
for mask in [1<<x for x in range(28)]:
 assert step(11,mask)==(mask,mask)
 assert step(12,0)==(mask,0)
 assert step(14,mask)==(mask,0)
 assert step(16,0)==(0,0)
print('PASS: 121 frame-phase/input cases; trigger retention, one-shot delivery, disabled behavior, and register preservation')
(p/'glove-scale-candidate/input-latch-validation.json').write_text(json.dumps({'passed':True,'cases':121,'integrated_cave_bytes':len(blob),'tested':'Exact integrated ARM input routine in Unicorn; new candidate live controller validation pending'},indent=2))
