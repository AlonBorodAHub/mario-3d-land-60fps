"""Post-bone stabilization hook; uses an unreachable native stride branch.

0x224ac8 fixes stride to 16 at 0x224ad4, then branches at 0x224adc past
the stride-12 block 0x224ae0..0x224b88. The untouched dispatcher is tested.
"""
HELPER=0x3a177c
CALLER=0x224ae0
CALLER_ASM=r'''
push {r3,lr}
sub sp,sp,#16
cmp r3,#0
beq finish
ldr r0,[r4,#16]
cmp r0,#20
bne finish
sub r3,r0,r8
cmp r3,#13
cmpne r3,#17
bne finish
ldr r0,[r4,#4]
ldr r1,[r0,#8]
ldr r2,[r1,#0x1c]!
add r1,r1,r2
add r1,r1,r3,lsl #4
ldr r2,[r1,#0x24]
add r2,r1,r2
ldr r2,[r2,#0x24]
ldr r12,=0x646e6148
cmp r2,r12
bne finish
ldr r2,[r1,#0x28]!
add r1,r1,r2
add r1,r1,#0xa4
ldr r0,[r0,#0x40]
add r3,r3,r3,lsl #1
add r3,r0,r3,lsl #4
mov r12,r1
mov r0,sp
mov r1,r3
bl 0x25f978
mov r1,r12
mov r2,sp
sub r0,r6,#48
bl 0x3a177c
vmov.f32 s2,#0.5
finish:
add sp,sp,#16
subs r8,r8,#1
pop {r3,pc}
'''
