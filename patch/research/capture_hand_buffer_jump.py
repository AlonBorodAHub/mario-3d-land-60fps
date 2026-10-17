"""Finite in-place jump/camera pan capture, with all input restored in finally."""
from pathlib import Path
import sys,time,json,struct
import numpy as np
p=Path(__file__).resolve().parent.parent;sys.path[:0]=[str(p/'deps'),str(p/'Azahar-validation/scripting')]
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from AzaharRPC import AzaharRPC
c=AzaharRPC(timeout=3,retries=0);c.set_process(11);k=Ks(KS_ARCH_ARM,KS_MODE_ARM)
o=p/'hand-buffer-candidate/live-jump';o.mkdir(exist_ok=True)
def u(a):return struct.unpack('<I',c.read_memory(a,4))[0]
w,h,b=c.screenshot_raw(res_scale=1);im=np.frombuffer(b,np.uint8).reshape(h,w,3);roi=im[290:440,45:145].astype(int)
assert ((roi[:,:,0]>180)&(roi[:,:,1]>120)&(roi[:,:,2]<100)).mean()>.5
assert c.read_memory(0x224ae0,168)==(p/'hand-buffer-candidate/shape-caller.bin').read_bytes()
code=(p/'code-decompressed.bin').read_bytes();sites={'right':(0x2db088,'mov r2,#0x10'),'a':(0x2db04c,'movs r2,#1'),'start':(0x2db070,'mov r2,#8')}
original={n:code[a-0x100000:a-0x100000+4] for n,(a,_) in sites.items()}
assert all(c.read_memory(a,4)==original[n] for n,(a,_) in sites.items())
def force(n,on):
 a,asm=sites[n];c.write_memory(a,bytes(k.asm(asm,addr=a)[0]) if on else original[n])
frames=[];rows=[];poses=[];rendered=[];world=[];hands=[];begin=time.perf_counter();counters=[u(0x432008),u(0x432040)]
try:
 force('start',True);time.sleep(.085);force('start',False);time.sleep(.6)
 models=json.loads((p/'glove-scale-candidate/hand-draw-research/hand-model-caches.json').read_text())
 entries={};e=u(0x433000)
 while e:entries[u(e+4)]=(e,u(e+20));e=u(e)
 for suffix in ['L','R']:
  options=[]
  for m in models:
   if m['name'] in ['MarioHand'+suffix,'MarioMiniHand'+suffix]:
    s=int(m['skeleton'],16)
    if s in entries:options.append((entries[s][1],s,entries[s][0],m['name']))
  assert options;phase,s,e,name=max(options);assert u(e+8)==u(s+0x40)
  hands.append({'name':name,'skeleton':s,'entry':e})
 for i in range(120):
  if i==20:force('right',True);force('a',True)
  if i==26:force('right',False);force('a',False)
  w,h,b=c.screenshot_raw(res_scale=2);frames.append(np.frombuffer(b,np.uint8).reshape(h,w,3)[:480].copy())
  row={'frame':i,'time':time.perf_counter()-begin,'phase':u(0x432008),'hands':[]};pp=[];rr=[];ww=[]
  for hand in hands:
   s,e=hand['skeleton'],hand['entry'];entry=struct.unpack('<8I',c.read_memory(e,32));assert entry[1]==s and entry[4]==4 and entry[2]==u(s+0x40)
   pp.append(np.stack([np.frombuffer(c.read_memory(e+32,192),'<f4').reshape(4,3,4),np.frombuffer(c.read_memory(entry[6],192),'<f4').reshape(4,3,4)]))
   rr.append(np.frombuffer(c.read_memory(entry[2],192),'<f4').reshape(4,3,4))
   ww.append(np.frombuffer(c.read_memory(u(s+0x30),256),'<f4').reshape(4,16)[:,:12].reshape(4,3,4))
   row['hands'].append({'capture_phase':entry[5]})
  poses.append(np.stack(pp));rendered.append(np.stack(rr));world.append(np.stack(ww));row['phase_after']=u(0x432008);rows.append(row)
finally:
 force('right',False);force('a',False);force('start',True);time.sleep(.085);force('start',False)
time.sleep(.6);c.save_screenshot(str(o/'after-paused.png'),res_scale=2)
assert all(c.read_memory(a,4)==original[n] for n,(a,_) in sites.items())
np.savez_compressed(o/'jump.npz',frames=np.stack(frames),poses=np.stack(poses),rendered=np.stack(rendered),world=np.stack(world))
(o/'frames.json').write_text(json.dumps(rows,indent=2));(o/'hands.json').write_text(json.dumps(hands,indent=2))
even=[];odd=[];native=[]
for i,row in enumerate(rows):
 if row['phase']!=row['phase_after']:continue
 for hand in range(2):
  if row['hands'][hand]['capture_phase']!=row['phase']:continue
  prev,cur=poses[i][hand];actual=rendered[i][hand]
  if row['phase']%2==0:
   even.append(float(np.abs(actual[:,:,3]-(prev[:,:,3]+cur[:,:,3])*.5).max()))
  else:odd.append(float(np.abs(actual-cur).max()))
  native.append(float(np.abs(cur-world[i][hand]).max()))
report={'input_restored':True,'frames':len(frames),'stable_even_hand_samples':len(even),'maximum_even_translation_error':max(even,default=None),'stable_odd_hand_samples':len(odd),'maximum_odd_true_pose_error':max(odd,default=None),'maximum_native_world_vs_true_cache_error':max(native,default=None),'callback_delta':u(0x432008)-counters[0],'simulation_delta':u(0x432040)-counters[1],'visual_assessment':'pending'}
(o/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
