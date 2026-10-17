import sys
sys.argv.extend(["--gloves","--integrated"])
from pathlib import Path
import sys,struct,json,hashlib
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'deps'))
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
from gpu_pose_cache import CAPTURE_ASM,RENDER_ASM
gloves='--gloves' in sys.argv;integrated='--integrated' in sys.argv or gloves
out=p/('glove-scale-candidate' if gloves else 'gpu-cadence-candidate' if integrated else 'stereo-cadence-candidate');m=json.loads((out/'manifest.json').read_text());s={k:int(v,16) for k,v in m['symbols'].items()}
cave=int(m.get('code_cave_address','0x3a1800'),16)
k=Ks(KS_ARCH_ARM,KS_MODE_ARM)
baseline=(out/'code-cave.bin').read_bytes()
def assemble(n,a):
 b=bytearray(k.asm(a,addr=s[n])[0]);literal_start=len(b)-8
 assert struct.unpack_from('<2I',b,literal_start)==(0x432000,0x433000)
 for off in range(0,literal_start,4):
  word=struct.unpack_from('<I',b,off)[0]
  if word&0x0f7f0000!=0x051f0000:continue
  target=s[n]+off+8+(word&4095)*(1 if word&(1<<23) else -1)
  if s[n]+literal_start<=target<s[n]+len(b):
   value=bytes(b[target-s[n]:target-s[n]+4]);where=baseline.rfind(value)
   assert where>=0
   delta=0x3a1800+where-(s[n]+off+8);assert abs(delta)<4096
   word=(word&~(4095|(1<<23)))|abs(delta)|((1<<23) if delta>=0 else 0)
   struct.pack_into('<I',b,off,word)
 return bytes(b[:literal_start])
functions={n:assemble(n,a) for n,a in [('scene_capture',CAPTURE_ASM),('scene_render',RENDER_ASM)]} if not integrated else {
 'scene_capture':baseline[s['scene_capture']-cave:s['scene_render']-cave],
 'scene_render':baseline[s['scene_render']-cave:s['scene_invalidate']-cave]}
assert len(functions['scene_capture'])<=s['scene_render']-s['scene_capture']
assert len(functions['scene_render'])<=s['scene_invalidate']-s['scene_render']
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x3a1000,0x1000),(0x432000,0x41000),(0x10000000,0x10000),(0x20000000,0x1000)]:u.mem_map(a,n)
u.reg_write(UC_ARM_REG_C1_C0_2,0xf<<20);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
u.mem_write(cave,(out/'code-cave.bin').read_bytes())
if gloves:u.mem_map(0x224000,0x1000);u.mem_write(0x224ae0,(out/'shape-caller.bin').read_bytes())
for n,b in functions.items():u.mem_write(s[n],b)
B=0x432000;S=0x10000000;D=S+0x1000
def w(a,n):u.mem_write(a,struct.pack('<I',n))
def word(a):return struct.unpack('<I',u.mem_read(a,4))[0]
def pose(v):u.mem_write(D,struct.pack('<24f',*([v]*12+[v+1]*12)))
def call(n,arg=0):
 u.reg_write(UC_ARM_REG_R0,arg);u.reg_write(UC_ARM_REG_SP,0x20000ff0);u.reg_write(UC_ARM_REG_LR,0x3a1700);u.emu_start(s[n],0x3a1700,count=50000)
def check(v):assert struct.unpack('<24f',u.mem_read(D,96))==tuple([v]*12+[v+1]*12)
w(B+0x90,1);w(B+0x94,1);u.mem_write(B+0xb0,struct.pack('<f',.5))
w(S+0x50,D);w(S+0x54,D+96);w(S+0x58,2)
u.mem_write(S+0x20,b'Q'*48);original_world=bytes(u.mem_read(S+0x20,48))
w(B+8,0);pose(10);call('scene_capture',S)
w(B+8,2);pose(20);call('scene_capture',S);call('scene_render',1);check(15)
call('scene_render',1);check(15)
call('scene_render',0);check(20)
w(B+8,3);call('scene_render',1);check(20)
assert bytes(u.mem_read(S+0x20,48))==original_world
assert word(0x433008)==1
w(B+8,2);pose(30);call('scene_capture',S);call('scene_render',1);check(20)
w(B+8,4);pose(40);call('scene_capture',S);call('scene_render',1);check(35)
w(B+8,6);call('scene_render',1);check(40)
w(B+8,100);pose(50);call('scene_capture',S);call('scene_render',1);check(50)
call('scene_invalidate',S);call('scene_render',1)
alloc=word(0x433008)
for count,end in [(0,D),(129,D+129*48),(2,D+80),(2,D+112)]:
 w(S+0x58,count);w(S+0x54,end);call('scene_capture',S);assert word(0x433008)==alloc
w(S+0x58,2);w(S+0x54,D+96);call('scene_capture',S)
w(S+0x54,D+48);before=bytes(u.mem_read(D,96));call('scene_render',1);assert bytes(u.mem_read(D,96))==before
w(B+0x90,0);call('scene_capture',0xdead0000);call('scene_render',0)
if integrated:
 from unicorn import UC_HOOK_CODE
 u.mem_map(0x272000,0x1000);u.mem_write(0x272418,bytes.fromhex('1eff2fe1'))
 model=S+0x8000;w(model+0x220,S)
 def native_view(uc,address,size,unused):
  if address==0x272418:
   assert uc.reg_read(UC_ARM_REG_R0)==model
   pose(struct.unpack('<f',uc.mem_read(B+0xc80,4))[0])
   for reg,value in [(UC_ARM_REG_R0,111),(UC_ARM_REG_R1,222),(UC_ARM_REG_R2,333),(UC_ARM_REG_R3,444),(UC_ARM_REG_R12,555)]:uc.reg_write(reg,value)
 u.hook_add(UC_HOOK_CODE,native_view)
 w(B+0x90,1);w(B+0x94,1);w(S+0x54,D+96);w(S+0x58,2)
 w(B+8,200);u.mem_write(B+0xc80,struct.pack('<f',10));call('capture_thunk',model)
 w(B+8,202);u.mem_write(B+0xc80,struct.pack('<f',20));call('capture_thunk',model);check(20)
 w(B+0x94,0);call('capture_thunk',model);check(15)
 assert [u.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12]]==[111,222,333,444,555]
 call('capture_thunk',model);check(15)
 w(B+8,203);call('capture_thunk',model);check(20)
 assert bytes(u.mem_read(S+0x20,48))==original_world
 for a in [0x2a0000,0x13e000,0x1dc000,0x318000,0x3e2000]:u.mem_map(a,0x1000)
 head=word(0x433000)
 u.reg_write(UC_ARM_REG_R0,model);u.reg_write(UC_ARM_REG_SP,0x20000ff0);u.reg_write(UC_ARM_REG_LR,0x3a1700)
 u.emu_start(s['destroy_thunk'],0x2a0740,count=2000)
 assert word(head+4)==0 and u.reg_read(UC_ARM_REG_R0)==model and u.reg_read(UC_ARM_REG_SP)==0x20000ff0-36
 u.mem_write(0x13e220,bytes.fromhex('3010c0e51eff2fe1'))
 for name,stop in [('scene_kill_thunk',0x3a1700),('scene_init_thunk',0x1dcba4)]:
  for off,value in [(0,head),(4,4096),(8,5),(12,3)]:w(0x433000+off,value)
  w(B+0x94,1);u.mem_write(model+0x30,b'\x01')
  u.reg_write(UC_ARM_REG_R0,model);u.reg_write(UC_ARM_REG_SP,0x20000ff0);u.reg_write(UC_ARM_REG_LR,0x3a1700)
  u.emu_start(s[name],stop,count=2000)
  assert bytes(u.mem_read(0x433000,16))==bytes(16) and word(B+0x94)==0 and u.reg_read(UC_ARM_REG_R0)==model
  if name=='scene_kill_thunk':assert bytes(u.mem_read(model+0x30,1))==b'\x00'
 w(B+0x90,0);w(B+0x78,0);w(B+4,1);w(B+12,0);w(B+8,0)
 u.mem_write(0x3187b8,bytes.fromhex('7080bde8'))
 for phase in range(1,5):call('root_entry',model);assert word(B+8)==phase and word(B+0x94)==0
 assert word(B+0x40)==2
result={'passed':True,'scope':'Exact ARM final-skinning matrix midpoint/current restoration, repeated draws, shared capture, same-phase recapture, missing/gapped updates, invalidation, count/length guards, stale render buffers, disabled invalid pointer; original joint-world buffers unchanged. Native rendering unvalidated.', 'functions':{}}
if integrated:result['post_view_scope']='Integrated capture wrapper invokes native view once, captures afterward inside simulation, interpolates afterward outside simulation, keeps repeated eye draws stable, and preserves native return registers. Model destruction invalidates before native destructor; scene kill/init clear all caches; four root callbacks execute two simulation updates.'
for n,b in functions.items():
 (out/(n+'-gpu.bin')).write_bytes(b);result['functions'][n]={'address':hex(s[n]),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
(out/'gpu-cache-arm-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
