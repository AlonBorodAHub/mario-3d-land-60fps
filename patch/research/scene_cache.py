"""Bounded, shared-skeleton native cache candidate. Not installed by this module.

Pool 0x433000..0x473000: head, bump offset, allocation count, overflow count.
Entry: next, skeleton, world, compact, joints, phase, current pointer, capacity;
       previous packed matrices, current packed matrices (capacity * 48 each).
Capture follows native world calculation, never advances the game's animation.
"""
CAPTURE_ASM=r'''
push {r4, r5, r6, r7, r8, r9, r10, r11, r12, lr}
vpush {d0, d1}
mov r4, r0
ldr r5, =0x432000
ldr r0, [r5, #0x90]
cmp r0, #0
beq done
ldr r0, [r5, #0x94]
cmp r0, #1
bne done
mrc p15, 0, r0, c13, c0, 3
ldr r1, [r5, #0x98]
cmp r0, r1
bne done
ldr r6, [r5, #8]
tst r6, #1
bne done
cmp r4, #0
beq done
ldr r7, [r4, #0x30]
ldr r8, [r4, #0x40]
ldr r0, [r4, #0x34]
subs r9, r0, r7
beq done
tst r9, #63
bne done
lsr r9, r9, #6
cmp r9, #128
bhi done
cmp r7, #0
cmpne r8, #0
beq done
ldr r5, =0x433000
ldr r10, [r5]
mov r11, #0
lookup:
cmp r10, #0
beq missing
ldr r0, [r10, #4]
cmp r0, r4
beq found
cmp r0, #0
bne next
ldr r0, [r10, #28]
cmp r0, r9
movhs r11, r10
next:
ldr r10, [r10]
b lookup
missing:
cmp r11, #0
movne r10, r11
bne reuse
ldr r0, [r5, #4]
cmp r0, #0
moveq r0, #64
add r1, r9, r9, lsl #1
lsl r1, r1, #5
add r1, r1, #32
add r2, r0, r1
cmp r2, #0x40000
bhi overflow
add r10, r5, r0
str r2, [r5, #4]
ldr r0, [r5]
str r0, [r10]
str r10, [r5]
ldr r0, [r5, #8]
add r0, r0, #1
str r0, [r5, #8]
str r9, [r10, #28]
add r0, r9, r9, lsl #1
lsl r0, r0, #4
add r0, r0, #32
add r0, r10, r0
str r0, [r10, #24]
reuse:
mov r3, #2
b configure
found:
ldr r0, [r10, #8]
cmp r0, r7
ldreq r0, [r10, #12]
cmpeq r0, r8
ldreq r0, [r10, #16]
cmpeq r0, r9
bne changed_layout
ldr r0, [r10, #20]
cmp r0, r6
moveq r3, #0
beq configure
add r0, r0, #2
cmp r0, r6
moveq r3, #1
movne r3, #2
b configure
changed_layout:
ldr r0, [r10, #28]
cmp r0, r9
blo invalidate_large
mov r3, #2
configure:
str r4, [r10, #4]
str r7, [r10, #8]
str r8, [r10, #12]
str r9, [r10, #16]
str r6, [r10, #20]
add r1, r10, #32
ldr r2, [r10, #24]
capture_bone:
mov r12, #12
capture_float:
vldr s0, [r7]
cmp r3, #1
vldreq s1, [r2]
vstreq s1, [r1]
cmp r3, #2
vstreq s0, [r1]
vstr s0, [r2]
add r7, r7, #4
add r1, r1, #4
add r2, r2, #4
subs r12, r12, #1
bne capture_float
add r7, r7, #16
subs r9, r9, #1
bne capture_bone
b done
invalidate_large:
mov r0, #0
str r0, [r10, #4]
b done
overflow:
ldr r0, [r5, #12]
add r0, r0, #1
str r0, [r5, #12]
done:
vpop {d0, d1}
pop {r4, r5, r6, r7, r8, r9, r10, r11, r12, pc}
'''

RENDER_ASM=r'''
push {r4, r5, r6, r7, r8, r9, r10, r11, r12, lr}
vpush {d0, d1}
mov r11, r0
ldr r4, =0x432000
ldr r0, [r4, #0x90]
cmp r0, #0
beq done
ldr r5, [r4, #8]
vldr s2, [r4, #0xb0]
ldr r4, =0x433000
ldr r4, [r4]
entry:
cmp r4, #0
beq done
ldr r0, [r4, #4]
cmp r0, #0
beq next
ldr r6, [r4, #8]
ldr r7, [r4, #12]
ldr r8, [r4, #16]
ldr r1, [r0, #0x30]
cmp r1, r6
ldreq r1, [r0, #0x40]
cmpeq r1, r7
bne next
ldr r1, [r0, #0x34]
add r2, r6, r8, lsl #6
cmp r1, r2
bne next
add r9, r4, #32
ldr r10, [r4, #24]
mov r3, #0
cmp r11, #0
beq bone
tst r5, #1
bne bone
ldr r0, [r4, #20]
cmp r0, r5
moveq r3, #1
bone:
mov r12, #12
float_loop:
vldr s0, [r10]
cmp r3, #0
beq store
vldr s1, [r9]
vadd.f32 s0, s0, s1
vmul.f32 s0, s0, s2
store:
vstr s0, [r6]
vstr s0, [r7]
add r6, r6, #4
add r7, r7, #4
add r9, r9, #4
add r10, r10, #4
subs r12, r12, #1
bne float_loop
add r6, r6, #16
subs r8, r8, #1
bne bone
next:
ldr r4, [r4]
b entry
done:
vpop {d0, d1}
pop {r4, r5, r6, r7, r8, r9, r10, r11, r12, pc}
'''

INVALIDATE_ASM=r'''
push {r1, r2, r3, lr}
ldr r1, =0x433000
ldr r1, [r1]
loop:
cmp r1, #0
beq done
ldr r2, [r1, #4]
cmp r2, r0
moveq r3, #0
streq r3, [r1, #4]
ldr r1, [r1]
b loop
done:
pop {r1, r2, r3, pc}
'''
