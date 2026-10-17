import sys
sys.argv.extend(["--gloves","--integrated"])
from pathlib import Path
import sys,struct,json
root=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(root/'deps'))
from unicorn import *
from unicorn.arm_const import *
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
b=(root/'camera-research/instrumentation.ips').read_bytes();i=5;blob=None
while b[i:i+3]!=b'EOF':
 a=int.from_bytes(b[i:i+3],'big')+0x100000;n=int.from_bytes(b[i+3:i+5],'big');i+=5
 if a==0x3a1900:blob=b[i:i+n]
 i+=n
scene='--scene' in sys.argv or '--cadence' in sys.argv or '--gpu-cadence' in sys.argv or '--gloves' in sys.argv
output=root/('glove-scale-candidate' if '--gloves' in sys.argv else 'gpu-cadence-candidate' if '--gpu-cadence' in sys.argv else 'stereo-cadence-candidate' if '--cadence' in sys.argv else 'scene-candidate' if scene else 'camera-research')
entry=0x3a1900
if scene:
 manifest=json.loads((output/'manifest.json').read_text());entry=int(manifest['symbols']['view_refresh'],16)
 blob=(output/'code-cave.bin').read_bytes()
assert blob
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x3a1000,0x1000),(0x272000,0x1000),(0x432000,0x1000),(0x10000000,0x5000),(0x20000000,0x1000)]:u.mem_map(a,n)
u.reg_write(UC_ARM_REG_C1_C0_2,0xf<<20);u.reg_write(UC_ARM_REG_FPEXC,0x40000000);u.mem_write(int(manifest.get('code_cave_address','0x3a1800'),16) if scene else entry,blob)
u.mem_write(0x27254c,bytes.fromhex('1eff2fe1'));u.mem_write(0x272418,bytes.fromhex('1eff2fe1'))
called=[]
def clobber(uc,address,size,user):
 called.append(address)
 for i,r in enumerate([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12]):uc.reg_write(r,0xdead0000+i)
 for i in range(16):uc.reg_write(UC_ARM_REG_S0+i,0x40000000+i)
 uc.reg_write(UC_ARM_REG_CPSR,(uc.reg_read(UC_ARM_REG_CPSR)&0x0fffffff)|0x50000000);uc.reg_write(UC_ARM_REG_FPSCR,0x90000000)
 if address==0x27254c:uc.reg_write(UC_ARM_REG_R0,0x10004000)
u.hook_add(UC_HOOK_CODE,clobber,begin=0x272418,end=0x272418);u.hook_add(UC_HOOK_CODE,clobber,begin=0x27254c,end=0x27254c)
regs=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12]
for mode,vt,expect in [(1,0x3d81bc,2),(0,0x3d81bc,0),(1,0x123456,0)]:
 u.mem_write(0x432078,struct.pack('<I',mode));u.mem_write(0x10003000,struct.pack('<I',vt));vals=[0x10003000,123,456,789,1011]
 for reg,val in zip(regs,vals):u.reg_write(reg,val)
 for i in range(16):u.reg_write(UC_ARM_REG_S0+i,0x3f800000+i)
 flags=(u.reg_read(UC_ARM_REG_CPSR)&0x0fffffff)|0xa0000000;u.reg_write(UC_ARM_REG_CPSR,flags);u.reg_write(UC_ARM_REG_FPSCR,0x60000000)
 u.reg_write(UC_ARM_REG_SP,0x20000ff0);u.reg_write(UC_ARM_REG_LR,0x3a1700);called.clear();u.emu_start(entry,0x3a1700,count=1000)
 assert len(called)==expect
 assert [u.reg_read(reg) for reg in regs]==vals
 assert all(u.reg_read(UC_ARM_REG_S0+i)==0x3f800000+i for i in range(16))
 assert u.reg_read(UC_ARM_REG_CPSR)&0xf0000000==flags&0xf0000000
 assert u.reg_read(UC_ARM_REG_FPSCR)==0x60000000
print('PASS: draw-view hook preserves CPU flags, FPSCR, volatile registers and all caller-saved VFP registers; disabled/type guards passed')
(output/'view-hook-validation.json').write_text(json.dumps({'passed':True,'scope':'Exact ARM hook with callees deliberately clobbering caller-saved state'},indent=2))
