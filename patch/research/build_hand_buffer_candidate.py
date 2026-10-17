"""Build a separate glove draw-buffer candidate; never installs or launches it."""
from pathlib import Path
from hand_buffer_cache import SELECT_ASM,CALLER_ASM,SHAPE_ASM
p=Path(__file__).resolve().parent.parent
s=(p/'native-prototype/build_glove_scale_candidate.py').read_text()
s=s.replace('from glove_scale_shape import SHAPE_ASM','from hand_buffer_cache import SELECT_ASM,SHAPE_ASM')
s=s.replace('from glove_scale_caller import CALLER,CALLER_ASM','from hand_buffer_cache import CALLER_ASM\nCALLER=0x224ae0')
s=s.replace("parts['scene_capture']=CAPTURE_ASM", """CAPTURE_ASM=CAPTURE_ASM.replace('ldr r7, [r4, #0x50]\\nmov r8, r7\\nldr r0, [r4, #0x54]', 'mov r0,r4\\nbl hand_buffer_select\\nmov r7,r1\\nmov r8,r7\\nmov r0,r2')
RENDER_ASM=RENDER_ASM.replace('ldr r1, [r0, #0x50]\\ncmp r1, r6\\nbne next\\nldr r1, [r0, #0x54]', 'bl hand_buffer_select\\ncmp r1,r6\\nbne next\\nmov r1,r2')
parts['scene_capture']=CAPTURE_ASM""")
s=s.replace(".replace('subs r8, r8, #1','bl '+str(CALLER))", ".replace('subs r8, r8, #1','bl hand_world_caller')")
s=s.replace("parts['glove_shape']=SHAPE_ASM", "parts['hand_world_caller']=CALLER_ASM\nparts['hand_buffer_select']=SELECT_ASM")
s=s.replace("caller=bytes(ks.asm(CALLER_ASM.replace('bl 0x3a177c','bl '+str(addresses['glove_shape'])).replace('bl 0x3a1a84','bl '+str(addresses['glove_scale_midpoint'])),addr=CALLER)[0])", "caller=bytes(ks.asm(SHAPE_ASM,addr=CALLER)[0])")
s=s.replace("out=p/'glove-scale-candidate'", "out=p/'hand-buffer-candidate'")
exec(compile(s,__file__,'exec'))
import json
o=p/'hand-buffer-candidate';m=json.loads((o/'manifest.json').read_text())
m.update(status='Offline built native rigid-glove buffer candidate; run validation before installing',baseline='Normal Play Mario launcher retains primary-stereo-candidate',risks=['Fresh integrated startup and level transitions require validation.','User visual glove assessment is pending.'])
(o/'manifest.json').write_text(json.dumps(m,indent=2))
