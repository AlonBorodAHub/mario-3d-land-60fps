"""Run integrated regressions and execute the new rigid glove path in ARM."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
p=Path(__file__).resolve().parent.parent;sys.path[:0]=[str(p/'deps'),str(p/'native-prototype')]
o=p/'hand-buffer-candidate'
for name in ['cache','input','camera','view']:
 f=p/'native-prototype'/('test_glove_scale_'+name+'.py')
 source=f.read_text().replace('glove-scale-candidate','hand-buffer-candidate')
 exec(compile(source,str(f),'exec'),{'__file__':str(f),'__name__':'__main__'})

from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
m=json.loads((o/'manifest.json').read_text());s={k:int(v,16) for k,v in m['symbols'].items()}
code=(p/'code-decompressed.bin').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x100000,0x300000),(0x432000,0x41000),(0x10000000,0x20000),(0x20000000,0x4000)]:u.mem_map(a,n)
u.mem_write(0x100000,code);u.mem_write(0x3a177c,(o/'code-cave.bin').read_bytes());u.mem_write(0x224ae0,(o/'shape-caller.bin').read_bytes())
u.reg_write(UC_ARM_REG_C1_C0_2,0xf<<20);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
def w(a,v):u.mem_write(a,struct.pack('<I',v))
def word(a):return struct.unpack('<I',u.mem_read(a,4))[0]
def run(name,arg):
 saved={r:0x11220000+i for i,r in enumerate([UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11])}
 for r,v in saved.items():u.reg_write(r,v)
 fp=[0x3ff0000000000000+i for i in range(16)]
 for i,v in enumerate(fp):u.reg_write(UC_ARM_REG_D0+i,v)
 u.reg_write(UC_ARM_REG_R0,arg);u.reg_write(UC_ARM_REG_SP,0x20003ff0);u.reg_write(UC_ARM_REG_LR,0x3a1700)
 u.emu_start(s[name],0x3a1700,count=500000)
 assert u.reg_read(UC_ARM_REG_PC)==0x3a1700 and u.reg_read(UC_ARM_REG_SP)==0x20003ff0
 for r,v in saved.items():assert u.reg_read(r)==v
 if name=='scene_render':
  for i,v in enumerate(fp):assert u.reg_read(UC_ARM_REG_D0+i)==v
B=0x432000;S=0x10001000;D=0x10006000;G=0x10007000;resource=0x10002000;dictionary=resource+0x100;nameptr=resource+0x300
w(S+8,resource);w(resource+0x1c,dictionary-resource-0x1c);w(dictionary+0x34,nameptr-dictionary-0x34)
w(S+0x40,D);w(S+0x44,D+192);w(S+0x48,4);w(S+0x50,G);w(S+0x54,G+192);w(S+0x58,4)
w(B+0x90,1);w(B+0x94,1);u.mem_write(B+0xb0,struct.pack('<f',.5))
rng=np.random.default_rng(621);cases=0
def pose():
 result=[]
 for _ in range(4):
  q,_=np.linalg.qr(rng.normal(size=(3,3)))
  if np.linalg.det(q)<0:q[:,0]*=-1
  result.append(np.column_stack([q*rng.uniform(.7,1.5,3),rng.uniform(-7000,7000,3)]))
 return np.array(result,dtype='<f4')
for label in [b'HandL00',b'HandR00',b'Other00']:
 u.mem_write(nameptr,label+b'\0');is_hand=label.startswith(b'Hand')
 for j in range(60):
  run('scene_clear',0);w(B+0x94,1);a=pose();b=a.copy();sentinel=bytes([123])*192
  angle=rng.uniform(-.15,.15);rotation=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]],dtype='f4')
  b[:,:,:3]=np.einsum('ij,njk->nik',rotation,a[:,:,:3])*rng.uniform(.95,1.05,(4,1,3))
  b[:,:,3]+=rng.uniform(-50,50,(4,3))
  u.mem_write(D,a.tobytes());u.mem_write(G,a.tobytes());w(B+8,0);run('scene_capture',S)
  e=word(0x433000);assert word(e+8)==(D if is_hand else G)
  u.mem_write(D,b.tobytes() if is_hand else sentinel);u.mem_write(G,sentinel if is_hand else b.tobytes());w(B+8,2);run('scene_capture',S)
  for stage,phase in [(1,2),(1,2),(0,2),(1,3)]:
   w(B+8,phase);run('scene_render',stage)
   actual=np.frombuffer(u.mem_read(D if is_hand else G,192),'<f4').reshape(4,3,4)
   assert np.isfinite(actual).all()
   assert bytes(u.mem_read(G if is_hand else D,192))==sentinel
   if stage==0 or phase==3:assert np.array_equal(actual,b)
   elif is_hand:
    assert np.allclose(actual[:,:,3],((a+b)*.5)[:,:,3],rtol=0,atol=.001)
    scale=(np.linalg.norm(a[:,:,:3],axis=1)+np.linalg.norm(b[:,:,:3],axis=1))*.5
    assert np.allclose(np.linalg.norm(actual[:,:,:3],axis=1),scale,atol=.0005,rtol=0)
    determinant=np.linalg.det(actual[:,:,:3])/np.prod(scale,axis=1)
    assert np.allclose(determinant,1,atol=.0005,rtol=0),(label,j,determinant,actual[0],a[0],b[0])
   else:assert np.array_equal(actual,(a+b)*.5)
   cases+=1
  run('scene_invalidate',S);assert word(e+4)==0
  before=bytes(u.mem_read(D,192));run('scene_render',1);assert bytes(u.mem_read(D,192))==before

# Recorded main-body palettes must retain ordinary 60 Hz interpolation.
run('scene_clear',0);e=0x433040;current=e+32+960
w(0x433000,e);w(e,0);w(e+4,S);w(e+8,G);w(e+12,G);w(e+16,20);w(e+20,2);w(e+24,current);w(e+28,20)
w(S+0x50,G);w(S+0x54,G+960);w(S+0x58,20)
body_cases=0
for previous,nextpose in np.load(p/'gpu-cadence-candidate/glove-research/jump.npz')['poses']:
 u.mem_write(e+32,previous.astype('<f4').tobytes());u.mem_write(current,nextpose.astype('<f4').tobytes())
 for stage,phase in [(1,2),(1,2),(0,2),(1,3)]:
  w(B+8,phase);run('scene_render',stage)
  actual=np.frombuffer(u.mem_read(G,960),'<f4').reshape(20,3,4)
  assert np.array_equal(actual,(previous+nextpose)*.5 if stage and phase==2 else nextpose)
  body_cases+=1

# Original native stride dispatcher still skips the repurposed branch.
for j in range(32):
 a,b=pose()[0],pose()[0];u.mem_write(D,a.tobytes());u.mem_write(G,b.tobytes());results=[]
 for block in [code[0x224ae0-0x100000:0x224b88-0x100000],(o/'shape-caller.bin').read_bytes().ljust(168,b'\0')]:
  u.mem_write(0x224ae0,block)
  for r,v in [(UC_ARM_REG_R0,D+0x400),(UC_ARM_REG_R1,D),(UC_ARM_REG_R2,G),(UC_ARM_REG_SP,0x20003ff0),(UC_ARM_REG_LR,0x3a1700)]:u.reg_write(r,v)
  u.emu_start(0x224ac8,0x3a1700,count=5000);results.append(bytes(u.mem_read(D+0x400,48)))
 assert results[0]==results[1]
report={'passed':True,'rigid_and_unrelated_render_cases':cases,'recorded_main_body_render_cases':body_cases,'native_dispatcher_cases':32,'scope':'Exact integrated capture/selection/render with native ARM matrix math; left/right four-bone rigid gloves, unrelated four-bone models, recorded main body palettes, both repeated eye draws, true-pose restore, phase gaps, lifetime invalidation, register and floating-point preservation. Rigid random tests use consecutive rotations within 0.15 radians and endpoint scales 0.7..1.5. No emulator visual claim.'}
(o/'hand-buffer-arm-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
