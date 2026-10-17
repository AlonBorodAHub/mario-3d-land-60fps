# Render-only camera pose experiment; recomputes views using native LookAtCamera code.
CAMERA_ADDRESS=0x3a1a28
CAMERA_BODY_ADDRESS=0x3a1ed0
CAMERA_ASM=r'''
push {r4, r5, r6, r7, r8, r9, r10, r11, r12, lr}
mrs r2, cpsr
vmrs r3, fpscr
push {r2, r3}
vpush {d0, d1, d2, d3, d4, d5, d6, d7}
mov r9, r0
ldr r4, =0x432000
ldr r0, [r4, #0x78]
cmp r0, #0
beq done
ldr r0, =0x3e23c4
ldr r0, [r0]
cmp r0, #0
beq done
ldr r0, [r0, #0x54]
cmp r0, #0
beq done
ldr r0, [r0, #0x20]
cmp r0, #0
beq done
ldr r0, [r0]
cmp r0, #0
beq done
ldr r1, [r0]
ldr r2, =0x3d9628
cmp r1, r2
bne done
add r7, r4, #0xd00
add r8, r4, #0xd80
add r10, r4, #0xe00
ldr r1, [r10]
cmp r1, r0
movne r11, #1
moveq r11, #0
str r0, [r10]
bl 0x3a1ed0
done:
vpop {d0, d1, d2, d3, d4, d5, d6, d7}
pop {r2, r3}
vmsr fpscr, r3
msr cpsr_f, r2
pop {r4, r5, r6, r7, r8, r9, r10, r11, r12, pc}
'''
CAMERA_BODY_ASM=r'''
push {r0, lr}
add r1, r0, #0x34
mov r2, r7
mov r3, r8
ldr lr, [r4, #8]
and lr, lr, #1
mov r12, #9
float_loop:
vldr s0, [r1]
cmp r11, #0
bne init
vldr s1, [r3]
cmp r9, #0
beq current
cmp lr, #0
bne current
cmp r9, #1
bne existing_midpoint
vstr s1, [r2]
vstr s0, [r3]
b midpoint
existing_midpoint:
vmov.f32 s0, s1
vldr s1, [r2]
midpoint:
vadd.f32 s0, s0, s1
vldr s2, [r4, #0xb0]
vmul.f32 s0, s0, s2
b store
init:
vstr s0, [r2]
vstr s0, [r3]
b store
current:
vmov.f32 s0, s1
store:
cmp r9, #0
beq store_final
ldr r0, [r4, #0x78]
cmp r0, #2
bne store_final
cmp r12, #9
cmpne r12, #6
vldreq s2, [r4, #0xb4]
vaddeq.f32 s0, s0, s2
store_final:
vstr s0, [r1]
add r1, r1, #4
add r2, r2, #4
add r3, r3, #4
subs r12, r12, #1
bne float_loop
ldr r0, [sp]
add r1, r0, #4
bl 0x36de80
pop {r0, pc}
'''
