"""Select the actual compact rigid palette for Mario's separate glove models.

All other skeletons retain their final skinned palette. Both arrays have a
48-byte matrix stride, so capture, rendering and lifetime keys stay unchanged.
"""
SELECT_ASM=r'''
mov r12,#0x50
ldr r1,[r0,#0x58]
cmp r1,#4
bne selected
ldr r1,[r0,#8]
ldr r2,[r1,#0x1c]!
add r1,r1,r2
ldr r2,[r1,#0x34]!
add r1,r1,r2
ldr r1,[r1]
ldr r2,=0x646e6148
cmp r1,r2
moveq r12,#0x40
selected:
ldr r1,[r0,r12]
add r12,r12,#4
ldr r2,[r0,r12]
bx lr
'''

# Only entries whose destination is the rigid compact palette need world-basis
# normalization. The visible main model continues ordinary palette blending.
CALLER_ASM=r'''
push {r3,lr}
sub sp,sp,#16
cmp r3,#0
beq finish
ldr r0,[r4,#4]
ldr r1,[r0,#0x40]
ldr r0,[r4,#8]
cmp r0,r1
bne finish
sub r3,r10,#48
mov r0,sp
mov r1,r3
bl 0x25f978
bl glove_scale_midpoint
mov r2,sp
sub r0,r6,#48
bl 0x224ae0
vmov.f32 s2,#0.5
finish:
add sp,sp,#16
subs r8,r8,#1
pop {r3,pc}
'''

from glove_scale_shape import SHAPE_ASM as OLD_SHAPE
# The compact palette already contains world matrices: no inverse-bind
# conversion is required. Keep its midpoint translation and endpoint scale.
SHAPE_ASM=OLD_SHAPE.replace('mov r5,r1\n','').replace('''mov r0,sp
bl 0x27c524
add r0,sp,#48
mov r1,r4
mov r2,sp
bl 0x281cf0''','''add r0,sp,#48
mov r1,r4
bl 0x291468''').replace('''mov r0,r4
add r1,sp,#48
mov r2,r5
bl 0x281cf0''','''mov r0,r4
add r1,sp,#48
bl 0x291468''')
SHAPE_ASM=SHAPE_ASM.replace('''add r0,sp,#48
mov r1,r4
bl 0x291468
mov r0,sp
add r1,sp,#48''','''mov r0,sp
mov r1,r4''').replace('addge r1,sp,#48','movge r1,r4')
SHAPE_ASM=SHAPE_ASM.replace('add r0,sp,#48','mov r0,r4')
SHAPE_ASM=SHAPE_ASM.replace('''mov r0,r4
add r1,sp,#48
bl 0x291468
''','')
SHAPE_ASM=SHAPE_ASM.replace('bl 0x1f4efc\nbl 0x1f4efc','bl 0x1f4efc\nbl 0x1f4efc\nbl 0x1f4efc')
