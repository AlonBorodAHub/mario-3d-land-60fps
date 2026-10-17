"""Retain stereo arguments only for the active central camera.
Auxiliary stage preview cameras must not replace the gameplay camera's args.
Native 0x265b98 overwrites R3 before use; caller-saved R12 is also overwritten.
"""
STEREO_CAPTURE_ASM='''
ldr r12, =0x432000
ldr r3, [r12,#0xe00]
cmp r2,r3
addeq r12,r12,#0xc00
stmiaeq r12,{r0,r1,r2}
vstreq d0,[r12,#16]
str lr,[sp,#-4]!
b 0x265b8c
'''
