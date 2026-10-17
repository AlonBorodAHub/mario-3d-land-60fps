"""Cache final 48-byte skinning matrices used by the renderer.

The earlier cache changed joint-world matrices (+30/+40), while the renderer
continued reading final inverse-bind skinning matrices (+50) at 30 Hz.
Preserve simulation joint buffers and interpolate the final render buffer.
"""
from scene_cache import CAPTURE_ASM as OLD_CAPTURE,RENDER_ASM as OLD_RENDER
old='''ldr r7, [r4, #0x30]
ldr r8, [r4, #0x40]
ldr r0, [r4, #0x34]
subs r9, r0, r7
beq done
tst r9, #63
bne done
lsr r9, r9, #6'''
new='''ldr r7, [r4, #0x50]
mov r8, r7
ldr r0, [r4, #0x54]
ldr r9, [r4, #0x58]
cmp r9, #0
beq done
add r1, r9, r9, lsl #1
sub r0, r0, r7
cmp r0, r1, lsl #4
bne done'''
assert old in OLD_CAPTURE
CAPTURE_ASM=OLD_CAPTURE.replace(old,new).replace('cmpne r8, #0\n','').replace('add r7, r7, #16\n','')
old='''ldr r1, [r0, #0x30]
cmp r1, r6
ldreq r1, [r0, #0x40]
cmpeq r1, r7
bne next
ldr r1, [r0, #0x34]
add r2, r6, r8, lsl #6'''
new='''ldr r1, [r0, #0x50]
cmp r1, r6
bne next
ldr r1, [r0, #0x54]
add r2, r8, r8, lsl #1
add r2, r6, r2, lsl #4'''
assert old in OLD_RENDER
RENDER_ASM=OLD_RENDER.replace(old,new).replace('add r6, r6, #16\n','')
