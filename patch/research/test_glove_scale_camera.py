import sys
sys.argv.extend(["--gloves","--integrated"])
from pathlib import Path
import sys,struct,json
root=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(root/'deps'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from camera_helper import *
cadence='--cadence' in sys.argv or '--gpu-cadence' in sys.argv or '--gloves' in sys.argv
scene='--scene' in sys.argv or cadence
output=root/('glove-scale-candidate' if '--gloves' in sys.argv else 'gpu-cadence-candidate' if '--gpu-cadence' in sys.argv else 'stereo-cadence-candidate' if cadence else 'scene-candidate' if scene else 'camera-research')
if scene:
 manifest=json.loads((output/'manifest.json').read_text())
 CAMERA_ADDRESS=int(manifest['symbols']['camera_entry'],16)
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x3a1000,0x1000),(0x36d000,0x1000),(0x432000,0x1000),(0x3e2000,0x1000),(0x10000000,0x5000),(0x20000000,0x1000)]:u.mem_map(a,n)
u.reg_write(UC_ARM_REG_C1_C0_2,0xf<<20);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
k=Ks(KS_ARCH_ARM,KS_MODE_ARM)
if scene:u.mem_write(int(manifest.get('code_cave_address','0x3a1800'),16),(output/'code-cave.bin').read_bytes())
else:
 u.mem_write(CAMERA_ADDRESS,bytes(k.asm(CAMERA_ASM,addr=CAMERA_ADDRESS)[0]));u.mem_write(CAMERA_BODY_ADDRESS,bytes(k.asm(CAMERA_BODY_ASM,addr=CAMERA_BODY_ADDRESS)[0]))
# The native callee may alter CPU and floating-point condition flags.
u.mem_write(0x36de80,bytes(k.asm('mov r1, #0; cmp r1, #1; vmsr fpscr, r1; bx lr',addr=0x36de80)[0]))
w=lambda a,v:u.mem_write(a,struct.pack('<I',v))
w(0x3e23c4,0x10000000);w(0x10000054,0x10001000);w(0x10001020,0x10002000);w(0x10002000,0x10003000);w(0x10003000,0x3d9628)
B=0x432000;C=0x10003000;w(B+0x78,1);u.mem_write(B+0xb0,struct.pack('<ff',.5,300))
if cadence:
 u.mem_map(0x265000,0x1000)
 # Execute the candidate's actual argument capture wrapper before a native spy.
 u.mem_write(0x265b88,bytes(k.asm('b '+manifest['symbols']['stereo_capture'],addr=0x265b88)[0]))
 u.mem_write(0x265b8c,bytes(k.asm('ldr r12,=0x432000; ldr r3,[r2,#0x34]; str r3,[r12,#0xc40]; ldr r3,[r12,#0xc44]; add r3,r3,#1; str r3,[r12,#0xc44]; pop {pc}',addr=0x265b8c)[0]))
 w(B+0xe00,C)
 u.mem_write(B+0xc00,struct.pack('<3I',0x10004000,0x10004100,C))
 u.mem_write(B+0xc10,struct.pack('<2f',750,.4))
def raw(x):u.mem_write(C+0x34,struct.pack('<9f',x,0,0,x,0,-1,0,1,0))
def x():return struct.unpack('<f',u.mem_read(C+0x34,4))[0]
def step(phase,stage):
 w(B+8,phase);u.reg_write(UC_ARM_REG_R0,stage);u.reg_write(UC_ARM_REG_SP,0x20000ff0);u.reg_write(UC_ARM_REG_LR,0x3a1700)
 flags=0xa0000000
 u.reg_write(UC_ARM_REG_CPSR,(u.reg_read(UC_ARM_REG_CPSR)&0x0fffffff)|flags)
 u.reg_write(UC_ARM_REG_FPSCR,flags)
 u.emu_start(CAMERA_ADDRESS,0x3a1700,count=2000)
 assert u.reg_read(UC_ARM_REG_CPSR)&0xf0000000==flags
 assert u.reg_read(UC_ARM_REG_FPSCR)==flags
raw(0);step(0,0);raw(10);step(2,1);assert x()==5
if cadence:assert struct.unpack('<f',u.mem_read(B+0xc40,4))[0]==5
step(2,2);assert x()==5
step(3,0);assert x()==10
step(3,1);assert x()==10
step(3,2);assert x()==10
if cadence:assert struct.unpack('<f',u.mem_read(B+0xc40,4))[0]==10
raw(20);step(4,1);assert x()==15
step(4,2);assert x()==15
step(5,0);assert x()==20
for phase in range(6,206):
 step(phase,0);assert x()==20
 step(phase,1);assert x()==20
 step(phase,2);assert x()==20
w(B+0x78,2);step(206,0);raw(30);step(206,1);assert x()==(25 if cadence else 325)
step(206,2);assert x()==(25 if cadence else 325)
step(207,0);assert x()==30
for address in [0x3e23c4,0x10000054,0x10001020,0x10002000]:
 saved=bytes(u.mem_read(address,4));w(address,0)
 before=bytes(u.mem_read(C+0x34,36));step(208,0)
 assert bytes(u.mem_read(C+0x34,36))==before
 u.mem_write(address,saved)
if cadence:
 before=struct.unpack('<I',u.mem_read(B+0xc44,4))[0]
 w(B+0xc08,C+4);step(210,1)
 assert struct.unpack('<I',u.mem_read(B+0xc44,4))[0]==before
 u.mem_map(0x162000,0x1000)
 for eye in [0,1]:
  u.reg_write(UC_ARM_REG_R5,eye)
  for reg,val in [(UC_ARM_REG_R0,0x1234),(UC_ARM_REG_R1,0x5678),(UC_ARM_REG_R2,0x9012),(UC_ARM_REG_R3,0x3456),(UC_ARM_REG_R12,0x7890)]:u.reg_write(reg,val)
  u.reg_write(UC_ARM_REG_SP,0x20000ff0);u.reg_write(UC_ARM_REG_LR,0x3a1700)
  u.emu_start(int(manifest['symbols']['camera_thunk'],16),0x162e84,count=3000)
  assert u.reg_read(UC_ARM_REG_CPSR)&0xf0000000==(0x60000000 if eye==0 else 0x20000000)
  assert u.reg_read(UC_ARM_REG_SP)==0x20000ff0
  assert [u.reg_read(reg) for reg in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12]]==[0x1234,0x5678,0x9012,0x3456,0x7890]
# An auxiliary camera update must not overwrite the active camera arguments.
saved_args=bytes(u.mem_read(B+0xc00,24))
for reg,val in [(UC_ARM_REG_R0,0x10004200),(UC_ARM_REG_R1,0x10004300),(UC_ARM_REG_R2,C+64)]:u.reg_write(reg,val)
u.reg_write(UC_ARM_REG_SP,0x20000ff0);u.reg_write(UC_ARM_REG_LR,0x3a1700)
u.emu_start(0x265b88,0x3a1700,count=1000)
assert bytes(u.mem_read(B+0xc00,24))==saved_args,'Auxiliary camera replaced active arguments'
assert u.reg_read(UC_ARM_REG_SP)==0x20000ff0
print('PASS: camera capture/restore, matching eye phases, 200 stable paused frames, CPU/FPU flags preserved; stereo candidate also checks refresh and relocated eye dispatch' if cadence else 'PASS: camera capture/restore, matching eye phases, 200 stable paused frames, isolated diagnostic offset, CPU/FPU flags preserved')
(output/'camera-math-validation.json').write_text(json.dumps({'passed':True,'scope':'Exact ARM helper math, phase ordering, null guards and CPU/FPU flag preservation; native LookAt calculation stubbed. Stereo variant also executes the real argument-capture wrapper, verifies native stereo refresh sees midpoint and full poses, and rejects a stale camera pointer. Live evidence is recorded separately.'},indent=2))
