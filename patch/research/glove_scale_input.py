"""Equivalent input latch without counters, plus render-only hand scale midpoint.
The 56 bytes recovered from the original 164-byte input routine hold the scale
helper. The helper uses the cached previous skinning matrix; recorded hand bind
bases preserve its scale to below 3e-7 relative to previous world scale.
"""
from input_latch import INPUT_ASM as ORIGINAL_INPUT_ASM
LIVE_INPUT=0x3a1a18
LIVE_SCALE=LIVE_INPUT+108
SCALE_ASM=r'''
vldmia r0,{s3,s4,s5}
sub r1,r9,#48
push {lr}
bl 0x25f978
vldmia r0,{s0,s1,s2}
vadd.f32 s0,s0,s3
vadd.f32 s1,s1,s4
vadd.f32 s2,s2,s5
vmov.f32 s6,#0.5
vmul.f32 s0,s0,s6
vmul.f32 s1,s1,s6
vmul.f32 s2,s2,s6
vstmia r0,{s0,s1,s2}
pop {pc}
'''
INPUT_ASM=ORIGINAL_INPUT_ASM.replace("ldr r12, =0x432000\n", "")
replacements=[(
"tst r1, #1\nbeq disabled\nldr r1, [r12, #12]",
"tst r1, #1\nldrne r1, [r12, #12]"),(
"cmp r0, #0\nbeq done\nldr r1, [r0, #0xd0]\ncmp r1, #0\nbeq done\nldr r0, [r0, #0xd8]\nldr r0, [r0]\ncmp r0, #0\nbeq done",
"cmp r0, #0\nldrne r1, [r0, #0xd0]\ncmpne r1, #0\nldrne r0, [r0, #0xd8]\nldrne r0, [r0]\ncmpne r0, #0\nbeq done"),(
"str r0, [r12, #0x70]\n", ""),(
"str r1, [r12, #0x6c]\ncmp r1, #0\nldrne r2, [r12, #0x68]\naddne r2, r2, #1\nstrne r2, [r12, #0x68]\n", ""),(
"tst r3, #1\nbne retain\nstr r1, [r0, #4]\nmov r1, #0",
"tst r3, #1\nstreq r1, [r0, #4]\nmoveq r1, #0"),(
"ldr r2, [r12, #0x64]\nadd r2, r2, #1\nstr r2, [r12, #0x64]\n", "")]
for before,after in replacements:
 assert INPUT_ASM.count(before)==1,before
 INPUT_ASM=INPUT_ASM.replace(before,after)
