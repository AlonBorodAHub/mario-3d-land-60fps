# Preserve controller trigger edges across skipped 60 Hz update slots.
INPUT_ADDRESS=0x3a1b80
INPUT_ASM=r'''
push {r0, r1, r2, r3, r12, lr}
ldr r12, =0x432000
ldr r1, [r12, #4]
tst r1, #1
beq disabled
ldr r1, [r12, #12]
cmp r1, #1
bne disabled
ldr r0, =0x3e26bc
ldr r0, [r0]
cmp r0, #0
beq done
ldr r1, [r0, #0xd0]
cmp r1, #0
beq done
ldr r0, [r0, #0xd8]
ldr r0, [r0]
cmp r0, #0
beq done
str r0, [r12, #0x70]
ldr r1, [r0, #4]
ldr r2, [r12, #0x60]
orr r1, r1, r2
ldr r3, [r12, #8]
tst r3, #1
bne retain
str r1, [r0, #4]
str r1, [r12, #0x6c]
cmp r1, #0
ldrne r2, [r12, #0x68]
addne r2, r2, #1
strne r2, [r12, #0x68]
mov r1, #0
retain:
str r1, [r12, #0x60]
ldr r2, [r12, #0x64]
add r2, r2, #1
str r2, [r12, #0x64]
b done
disabled:
mov r1, #0
str r1, [r12, #0x60]
done:
pop {r0, r1, r2, r3, r12, pc}
'''
