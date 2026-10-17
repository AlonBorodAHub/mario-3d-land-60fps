"""Verified reversible paused-game replacement of the glove-scale candidate."""
from pathlib import Path
import sys,json,struct,time,hashlib
import numpy as np
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'Azahar-validation/scripting'))
from AzaharRPC import AzaharRPC
c=AzaharRPC(timeout=3,retries=0);c.set_process(11)
o=p/'hand-buffer-candidate';backup=o/'live-backup';backup.mkdir(exist_ok=True)
def u(a):return struct.unpack('<I',c.read_memory(a,4))[0]
def patches(folder):
 data=(folder/'code.ips').read_bytes();assert data[:5]==b'PATCH';at=5;result={}
 while data[at:at+3]!=b'EOF':
  a=int.from_bytes(data[at:at+3],'big')+0x100000;n=int.from_bytes(data[at+3:at+5],'big');assert n
  at+=5;result[a]=data[at:at+n];at+=n
 return result
assert json.loads((o/'hand-buffer-arm-validation.json').read_text())['passed']
for name in ['input-latch-validation.json','camera-math-validation.json','view-hook-validation.json','gpu-cache-arm-validation.json']:assert json.loads((o/name).read_text())['passed']
old=patches(p/'glove-scale-candidate');new=patches(o);code=(p/'code-decompressed.bin').read_bytes()
hooks=[a for a,b in old.items() if len(b)==4 and a<0x3a177c];assert set(hooks)=={a for a,b in new.items() if len(b)==4 and a<0x3a177c}
assert all(c.read_memory(a,4)==old[a] for a in hooks),'Unexpected installed hook'
assert c.read_memory(0x224ae0,168)==old[0x224ae0]
expected=bytearray(old[0x3a177c]);plan=json.loads((p/'camera-once-live-layout/live-plan.json').read_text());a=int(plan['address'],16)
expected[a-0x3a177c:a-0x3a177c+len(bytes.fromhex(plan['after']))]=bytes.fromhex(plan['after'])
assert c.read_memory(0x3a177c,2180)==expected,'Unexpected live code'
w,h,b=c.screenshot_raw(res_scale=1);im=np.frombuffer(b,np.uint8).reshape(h,w,3);roi=im[290:440,45:145].astype(int)
assert ((roi[:,:,0]>180)&(roi[:,:,1]>120)&(roi[:,:,2]<100)).mean()>.5,'Game must be paused'
c.save_screenshot(str(backup/'before.png'),res_scale=2)
snap={0x3a177c:bytes(expected),0x224ae0:old[0x224ae0],**{a:old[a] for a in hooks}}
(backup/'code.json').write_text(json.dumps({hex(a):b.hex() for a,b in snap.items()},indent=2))
def guard():
 c.write_memory(0x3187b4,bytes.fromhex('1eff2fe1'))
 for a in hooks:
  if a!=0x3187b4:c.write_memory(a,code[a-0x100000:a-0x100000+4])
 time.sleep(.08)
def commit(blocks):
 c.write_memory(0x3a177c,blocks[0x3a177c]);c.write_memory(0x224ae0,blocks[0x224ae0])
 c.write_memory(0x433000,bytes(16));c.write_memory(0x432094,bytes(4))
 for a in hooks:
  if a!=0x3187b4:c.write_memory(a,blocks[a])
 c.write_memory(0x3187b4,blocks[0x3187b4])
 for a,b in blocks.items():assert c.read_memory(a,len(b))==b
try:
 guard()
 # Restore the old cache's true render poses before discarding history.
 e=u(0x433000);count=0
 while e:
  count+=1;assert count<1500
  key,dest,n,current=u(e+4),u(e+8),u(e+16),u(e+24)
  if key and n<=128 and u(key+0x50)==dest and u(key+0x54)==dest+48*n:c.write_memory(dest,c.read_memory(current,48*n))
  e=u(e)
 padded=new[0x3a177c]+bytes.fromhex('0000a0e1')*((2180-len(new[0x3a177c]))//4)
 assert len(padded)==2180
 installed={0x3a177c:padded,0x224ae0:new[0x224ae0],**{a:new[a] for a in hooks}}
 commit(installed)
except BaseException:
 guard();commit(snap);raise
c.save_screenshot(str(o/'live-after-paused.png'),res_scale=2)
report={'installed':True,'ips_sha256':hashlib.sha256((o/'code.ips').read_bytes()).hexdigest(),'all_bytes_verified':True,'normal_launcher_changed':False,'user_visual_validation':'pending','camera_once_experiment':'removed; original confirmed stereo camera filter retained'}
(o/'live-state.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
