"""Preserve bone volume around the bind pivot using native matrix routines.

R0 final skinning midpoint, R1 inverse bind, R2 current world scale,
R3 current world matrix. Only changes the rendered final skinning matrix.
"""
SHAPE_ASM=r'''
vldmia r2, {s0,s1,s2}
vmul.f32 s0,s0,s1
vmul.f32 s0,s0,s2
vcmp.f32 s0,#0
vmrs apsr_nzcv,fpscr
bxle lr
push {r4,r5,r6,r7,r8,lr}
mov r4,r0
mov r5,r1
mov r6,r2
mov r7,r3
sub sp,sp,#144
mov r0,sp
bl 0x27c524
add r0,sp,#48
mov r1,r4
mov r2,sp
bl 0x281cf0
mov r0,sp
add r1,sp,#48
bl 0x27c524
bic r2,r2,#0x80000000
cmp r2,#0x3a000000
addhs r1,sp,#48
movlo r1,r7
add r0,sp,#96
mov r3,#3
pack:
vldmia r1!,{s0,s1,s2,s3}
vstmia r0!,{s0,s1,s2}
subs r3,r3,#1
bne pack
add r0,sp,#96
vmov.f32 s0,#2.875
bl 0x1f4efc
bl 0x1f4efc
add r1,sp,#96
add r0,sp,#48
mov r3,#3
unpack:
vldmia r1!,{s0,s1,s2}
vstmia r0,{s0,s1,s2}
add r0,r0,#16
subs r3,r3,#1
bne unpack
add r0,sp,#48
mov r1,r0
mov r2,r6
bl 0x2723d8
mov r0,r4
add r1,sp,#48
mov r2,r5
bl 0x281cf0
add sp,sp,#144
pop {r4,r5,r6,r7,r8,pc}
'''
