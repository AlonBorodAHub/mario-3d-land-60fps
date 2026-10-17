"""Build a separate general-skeleton candidate. Does not install or alter emulator memory."""
from pathlib import Path
import sys,re,struct,json,hashlib
p=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(p/'deps'))
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from glove_scale_input import INPUT_ASM,SCALE_ASM
from camera_stereo_helper import CAMERA_ASM,CAMERA_BODY_ASM
from primary_stereo_capture import STEREO_CAPTURE_ASM
from gpu_pose_cache import CAPTURE_ASM,RENDER_ASM
from scene_cache import INVALIDATE_ASM
from scene_lifecycle import CLEAR_COMMON_ASM,KILL_ASM,INIT_ASM
from glove_scale_shape import SHAPE_ASM
from glove_scale_caller import CALLER,CALLER_ASM

code=(p/'code-decompressed.bin').read_bytes()
expected='c705711154b1c514d7a0b5d133fabff42834110b198bd4cf86397d0d1c1597e9'
assert hashlib.sha256(code).hexdigest()==expected
base=0x100000;cave=0x3a177c
assert not any(code[cave-base:0x3a2000-base])
ks=Ks(KS_ARCH_ARM,KS_MODE_ARM)
def namespaced(source,prefix):
    for label in set(re.findall(r'(?m)^([a-zA-Z_][a-zA-Z_0-9]*):',source)):
        source=re.sub(r'\b'+label+r'\b',prefix+'_'+label,source)
    return source

parts={}
parts['root_entry']=r'''
push {r0,r1,r2,r3,r12,lr}
ldr r12, =0x432000
ldr r1, [r12, #8]
add r1, r1, #1
str r1, [r12, #8]
ldr r2, [r12, #12]
cmp r2, #0
beq no_force
ldr r3, =0x3e23e8
ldr r3, [r3]
cmp r3, #0
strbne r2, [r3, #0x5c]
no_force:
bl input_entry
mov r0, #0
bl camera_entry
mov r0, #0
bl scene_render
ldr r12, =0x432000
ldr r2, [r12, #4]
tst r2, #1
beq execute
ldr r1, [r12, #8]
tst r1, #1
bne skip
execute:
ldr r3, [r12, #0x40]
add r3, r3, #1
str r3, [r12, #0x40]
mov r3, #1
str r3, [r12, #0x94]
mrc p15, 0, r3, c13, c0, 3
str r3, [r12, #0x98]
pop {r0,r1,r2,r3,r12,lr}
push {r4,lr}
bl root_native
ldr r12, =0x432000
mov r1, #0
str r1, [r12, #0x94]
pop {r4,pc}
root_native:
.word 0xe92d4070
b 0x3187b8
skip:
pop {r0,r1,r2,r3,r12,pc}
'''
parts['left_entry']='''push {r0,r1,r2,r3,r12,lr}; mov r0,#1; bl scene_render;
pop {r0,r1,r2,r3,r12,lr}; .word 0xe5900008; b 0x11abfc;'''
parts['camera_thunk']='''push {r0,r1,r2,r3,r12,lr}; rsb r0,r5,#2; bl camera_entry;
pop {r0,r1,r2,r3,r12,lr}; cmp r5,#0; b 0x162e84;'''
parts['capture_thunk']='''push {r4,lr}; mov r4,r0; bl 0x272418;
push {r0,r1,r2,r3,r12,lr}; ldr r0,[r4,#0x220]; bl scene_capture;
pop {r0,r1,r2,r3,r12,lr}; pop {r4,pc};'''
parts['destroy_thunk']='''push {r0,r1,r2,r3,r12,lr}; ldr r0,[r0,#0x220]; bl scene_invalidate;
pop {r0,r1,r2,r3,r12,lr}; .word 0xe92d4ff0; b 0x2a0740;'''
parts['view_refresh']=r'''
push {r0,r1,r2,r3,r12,lr}
mrs r3, cpsr
vmrs r12, fpscr
push {r3,r12}
vpush {d0,d1,d2,d3,d4,d5,d6,d7}
ldr r12, =0x432000
ldr r3, [r12,#0x78]
ldr r1, [r12,#0x90]
orrs r3,r3,r1
beq done
ldr r1, [r0]
ldr r3, =0x3d81bc
cmp r1,r3
bne done
bl 0x27254c
mov r1,r0
ldr r0,[sp,#72]
bl capture_thunk
done:
vpop {d0,d1,d2,d3,d4,d5,d6,d7}
pop {r3,r12}
vmsr fpscr,r12
msr cpsr_f,r3
pop {r0,r1,r2,r3,r12,pc}
'''
view_sites=[(0x3358c0,'r6'),(0x2a0404,'r4'),(0x2afd24,'r4'),(0x29d9c8,'r4')]
for i,(site,reg) in enumerate(view_sites):
    original=struct.unpack_from('<I',code,site-base)[0]
    parts['view_thunk_'+str(i)]=f'''push {{r0,lr}}; mov r0,{reg}; bl view_refresh;
    pop {{r0,lr}}; .word {original}; b {site+4};'''
parts['input_entry']=INPUT_ASM.replace('push {r0, r1, r2, r3, r12, lr}', 'push {r0, r1, r2, r3, r12, lr}\nnop')
parts['camera_entry']=CAMERA_ASM.replace('bl 0x3a1ed0','bl camera_body')
parts['camera_body']=CAMERA_BODY_ASM
parts['scene_capture']=CAPTURE_ASM.replace('cmp r0, #1\nbne done','cmp r0, #1\nbne gpu_render_after_view')
parts['scene_render']=RENDER_ASM.replace('vpush {d0, d1}','vpush {d0,d1,d2,d3,d4,d5,d6,d7}').replace('vpop {d0, d1}','vpop {d0,d1,d2,d3,d4,d5,d6,d7}').replace('subs r8, r8, #1','bl '+str(CALLER))
parts['scene_invalidate']=INVALIDATE_ASM
parts['scene_clear']=CLEAR_COMMON_ASM
parts['scene_kill_thunk']=KILL_ASM
parts['scene_init_thunk']=INIT_ASM
parts['stereo_capture']=STEREO_CAPTURE_ASM
parts['gpu_render_after_view']='mov r0,#1; bl scene_render; b scene_capture_done'
parts['glove_scale_midpoint']=SCALE_ASM
parts['glove_shape']=SHAPE_ASM
symbols=list(parts)
source='\n'.join('.word '+name for name in symbols)+'\n'
source+='\n'.join(name+':\n'+namespaced(asm,name) for name,asm in parts.items())
table_bytes=len(symbols)*4
assembled=bytes(ks.asm(source,addr=cave-table_bytes)[0])
addresses=dict(zip(symbols,struct.unpack_from('<'+'I'*len(symbols),assembled)))
blob=bytearray(assembled[table_bytes:])
# Reuse the root's existing control literal rather than adding another pool word.
root_load=addresses['root_entry']+4
instruction=struct.unpack_from('<I',blob,root_load-cave)[0]
assert instruction&0xfffff000==0xe59fc000
control_literal=root_load+8+(instruction&0xfff)
assert struct.unpack_from('<I',blob,control_literal-cave)[0]==0x432000
input_load=addresses['input_entry']+4
assert blob[input_load-cave:input_load-cave+4]==bytes(ks.asm('nop',addr=input_load)[0])
blob[input_load-cave:input_load-cave+4]=bytes(ks.asm(f'ldr r12,[pc,#{control_literal-input_load-8}]',addr=input_load)[0])
blob=bytes(blob)
caller=bytes(ks.asm(CALLER_ASM.replace('bl 0x3a177c','bl '+str(addresses['glove_shape'])).replace('bl 0x3a1a84','bl '+str(addresses['glove_scale_midpoint'])),addr=CALLER)[0])
assert CALLER+len(caller)<=0x224b88
assert code[0x224ad4-base:0x224ae0-base]==bytes(ks.asm('mov r3,#0x10; cmp r3,#0xc; bne 0x224b88',addr=0x224ad4)[0])
out=p/'glove-scale-candidate';out.mkdir(exist_ok=True)
(out/'candidate.s').write_text(source)
assert cave+len(blob)<=0x3a2000,('Candidate exceeds executable padding',len(blob),hex(cave+len(blob)))
hooks=[(0x3187b4,'root_entry',False),(0x11abf8,'left_entry',False),
       (0x162e80,'camera_thunk',False),(0x129064,'capture_thunk',False),
       (0x129350,'capture_thunk',False),(0x2a073c,'destroy_thunk',False),
       (0x13e21c,'scene_kill_thunk',False),(0x1dcba0,'scene_init_thunk',False),
       (0x265b88,'stereo_capture',False)]
assert struct.unpack_from('<I',code,0x2a073c-base)[0]==0xe92d4ff0
assert struct.unpack_from('<I',code,0x13e21c-base)[0]==0xe3a01000
assert struct.unpack_from('<I',code,0x1dcba0-base)[0]==0xe92d41f0
patches=[(cave-base,blob),(CALLER-base,caller)]
for site,label,link in hooks:
    patches.append((site-base,bytes(ks.asm(('bl ' if link else 'b ')+str(addresses[label]),addr=site)[0])))
for i,(site,_) in enumerate(view_sites):
    patches.append((site-base,bytes(ks.asm('b '+str(addresses['view_thunk_'+str(i)]),addr=site)[0])))
control=bytearray(0xc0)
struct.pack_into('<I',control,0,0x4d363050)
for off in [4,12,0x78,0x90]:struct.pack_into('<I',control,off,1)
struct.pack_into('<ff',control,0xb0,.5,20)
patches.append((0x432000-base,control))
ips=bytearray(b'PATCH')
for off,b in sorted(patches):ips+=off.to_bytes(3,'big')+len(b).to_bytes(2,'big')+b
ips+=b'EOF'
exheader=bytearray((p/'exheader.bin').read_bytes())
assert struct.unpack_from('<I',exheader,0x3c)[0]==0x3d684
struct.pack_into('<I',exheader,0x3c,0x3d684+0x41000)
(out/'code.ips').write_bytes(ips);(out/'code-cave.bin').write_bytes(blob);(out/'shape-caller.bin').write_bytes(caller);(out/'exheader.bin').write_bytes(exheader)
manifest={'status':'Integrated glove candidate; live equivalent tested, fresh integrated launch pending','code_cave_address':hex(cave),'code_bytes':len(blob),'external_caller_address':hex(CALLER),'external_caller_bytes':len(caller),'symbols':{k:hex(v) for k,v in addresses.items()},
          'pool_start':'0x433000','pool_end':'0x473000','ips_sha256':hashlib.sha256(ips).hexdigest(),
          'baseline':'native-stereo-preview remains installed','risks':['Capture hook coverage not established','Shared skeleton lifetime and culling require live validation','Pool size and performance unvalidated']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
