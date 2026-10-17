"""Clear pose state before scene kill/init; original instructions live in thunks."""
CLEAR_COMMON_ASM=r'''
push {r1,r2,r3,lr}
ldr r1, =0x433000
mov r2, #0
str r2, [r1]
str r2, [r1, #4]
str r2, [r1, #8]
str r2, [r1, #12]
ldr r3, =0x432000
str r2, [r3, #0x94]
ldr r1, [r3, #0xa8]
add r1, r1, #1
str r1, [r3, #0xa8]
pop {r1,r2,r3,pc}
'''
KILL_ASM='''push {r0,lr}; bl scene_clear; pop {r0,lr}; mov r1,#0; b 0x13e220;'''
INIT_ASM='''push {r0,lr}; bl scene_clear; pop {r0,lr}; .word 0xe92d41f0; b 0x1dcba4;'''
