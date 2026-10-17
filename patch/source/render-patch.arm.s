.word root_entry
.word left_entry
.word camera_thunk
.word capture_thunk
.word destroy_thunk
.word view_refresh
.word view_thunk_0
.word view_thunk_1
.word view_thunk_2
.word view_thunk_3
.word input_entry
.word camera_entry
.word camera_body
.word scene_capture
.word scene_render
.word scene_invalidate
.word scene_clear
.word scene_kill_thunk
.word scene_init_thunk
.word stereo_capture
.word gpu_render_after_view
.word glove_scale_midpoint
.word hand_world_caller
.word hand_buffer_select
root_entry:

push {r0,r1,r2,r3,r12,lr}
ldr r12, =0x432000
ldr r1, [r12, #8]
add r1, r1, #1
str r1, [r12, #8]
ldr r2, [r12, #12]
cmp r2, #0
beq root_entry_no_force
ldr r3, =0x3e23e8
ldr r3, [r3]
cmp r3, #0
strbne r2, [r3, #0x5c]
root_entry_no_force:
bl input_entry
mov r0, #0
bl camera_entry
mov r0, #0
bl scene_render
ldr r12, =0x432000
ldr r2, [r12, #4]
tst r2, #1
beq root_entry_execute
ldr r1, [r12, #8]
tst r1, #1
bne root_entry_skip
root_entry_execute:
ldr r3, [r12, #0x40]
add r3, r3, #1
str r3, [r12, #0x40]
mov r3, #1
str r3, [r12, #0x94]
mrc p15, 0, r3, c13, c0, 3
str r3, [r12, #0x98]
pop {r0,r1,r2,r3,r12,lr}
push {r4,lr}
bl root_entry_root_native
ldr r12, =0x432000
mov r1, #0
str r1, [r12, #0x94]
pop {r4,pc}
root_entry_root_native:
.word 0xe92d4070
b 0x3187b8
root_entry_skip:
pop {r0,r1,r2,r3,r12,pc}

left_entry:
push {r0,r1,r2,r3,r12,lr}; mov r0,#1; bl scene_render;
pop {r0,r1,r2,r3,r12,lr}; .word 0xe5900008; b 0x11abfc;
camera_thunk:
push {r0,r1,r2,r3,r12,lr}; rsb r0,r5,#2; bl camera_entry;
pop {r0,r1,r2,r3,r12,lr}; cmp r5,#0; b 0x162e84;
capture_thunk:
push {r4,lr}; mov r4,r0; bl 0x272418;
push {r0,r1,r2,r3,r12,lr}; ldr r0,[r4,#0x220]; bl scene_capture;
pop {r0,r1,r2,r3,r12,lr}; pop {r4,pc};
destroy_thunk:
push {r0,r1,r2,r3,r12,lr}; ldr r0,[r0,#0x220]; bl scene_invalidate;
pop {r0,r1,r2,r3,r12,lr}; .word 0xe92d4ff0; b 0x2a0740;
view_refresh:

push {r0,r1,r2,r3,r12,lr}
mrs r3, cpsr
vmrs r12, fpscr
push {r3,r12}
vpush {d0,d1,d2,d3,d4,d5,d6,d7}
ldr r12, =0x432000
ldr r3, [r12,#0x78]
ldr r1, [r12,#0x90]
orrs r3,r3,r1
beq view_refresh_done
ldr r1, [r0]
ldr r3, =0x3d81bc
cmp r1,r3
bne view_refresh_done
bl 0x27254c
mov r1,r0
ldr r0,[sp,#72]
bl capture_thunk
view_refresh_done:
vpop {d0,d1,d2,d3,d4,d5,d6,d7}
pop {r3,r12}
vmsr fpscr,r12
msr cpsr_f,r3
pop {r0,r1,r2,r3,r12,pc}

view_thunk_0:
push {r0,lr}; mov r0,r6; bl view_refresh;
    pop {r0,lr}; .word 3800440687; b 3365060;
view_thunk_1:
push {r0,lr}; mov r0,r4; bl view_refresh;
    pop {r0,lr}; .word 3800305519; b 2753544;
view_thunk_2:
push {r0,lr}; mov r0,r4; bl view_refresh;
    pop {r0,lr}; .word 3800305519; b 2817320;
view_thunk_3:
push {r0,lr}; mov r0,r4; bl view_refresh;
    pop {r0,lr}; .word 3800350575; b 2742732;
input_entry:

push {r0, r1, r2, r3, r12, lr}
nop
ldr r1, [r12, #4]
tst r1, #1
ldrne r1, [r12, #12]
cmp r1, #1
bne input_entry_disabled
ldr r0, =0x3e26bc
ldr r0, [r0]
cmp r0, #0
ldrne r1, [r0, #0xd0]
cmpne r1, #0
ldrne r0, [r0, #0xd8]
ldrne r0, [r0]
cmpne r0, #0
beq input_entry_done
ldr r1, [r0, #4]
ldr r2, [r12, #0x60]
orr r1, r1, r2
ldr r3, [r12, #8]
tst r3, #1
streq r1, [r0, #4]
moveq r1, #0
input_entry_retain:
str r1, [r12, #0x60]
b input_entry_done
input_entry_disabled:
mov r1, #0
str r1, [r12, #0x60]
input_entry_done:
pop {r0, r1, r2, r3, r12, pc}

camera_entry:

push {r4, r5, r6, r7, r8, r9, r10, r11, r12, lr}
mrs r2, cpsr
vmrs r3, fpscr
push {r2, r3}
vpush {d0, d1, d2, d3, d4, d5, d6, d7}
mov r9, r0
ldr r4, =0x432000
ldr r0, [r4, #0x78]
cmp r0, #0
beq camera_entry_done
ldr r0, =0x3e23c4
ldr r0, [r0]
cmp r0, #0
beq camera_entry_done
ldr r0, [r0, #0x54]
cmp r0, #0
beq camera_entry_done
ldr r0, [r0, #0x20]
cmp r0, #0
beq camera_entry_done
ldr r0, [r0]
cmp r0, #0
beq camera_entry_done
ldr r1, [r0]
ldr r2, =0x3d9628
cmp r1, r2
bne camera_entry_done
add r7, r4, #0xd00
add r8, r4, #0xd80
add r10, r4, #0xe00
ldr r1, [r10]
cmp r1, r0
movne r11, #1
moveq r11, #0
str r0, [r10]
bl camera_body
camera_entry_done:
vpop {d0, d1, d2, d3, d4, d5, d6, d7}
pop {r2, r3}
vmsr fpscr, r3
msr cpsr_f, r2
pop {r4, r5, r6, r7, r8, r9, r10, r11, r12, pc}

camera_body:

push {r0, lr}
add r1, r0, #0x34
mov r2, r7
mov r3, r8
ldr lr, [r4, #8]
and lr, lr, #1
mov r12, #9
camera_body_float_loop:
vldr s0, [r1]
cmp r11, #0
bne camera_body_init
vldr s1, [r3]
cmp r9, #0
beq camera_body_current
cmp lr, #0
bne camera_body_current
cmp r9, #1
bne camera_body_existing_midpoint
vstr s1, [r2]
vstr s0, [r3]
b camera_body_midpoint
camera_body_existing_midpoint:
vmov.f32 s0, s1
vldr s1, [r2]
camera_body_midpoint:
vadd.f32 s0, s0, s1
vldr s2, [r4, #0xb0]
vmul.f32 s0, s0, s2
b camera_body_store
camera_body_init:
vstr s0, [r2]
vstr s0, [r3]
b camera_body_store
camera_body_current:
vmov.f32 s0, s1
camera_body_store:
camera_body_store_final:
vstr s0, [r1]
add r1, r1, #4
add r2, r2, #4
add r3, r3, #4
subs r12, r12, #1
bne camera_body_float_loop
ldr r0, [sp]
add r1, r0, #4
bl 0x36de80
ldr r12, =0x432c00
ldmia r12, {r0,r1,r2}
ldr r3, [sp]
cmp r2, r3
vldreq d0, [r12,#16]
bleq 0x265b88
pop {r0, pc}

scene_capture:

push {r4, r5, r6, r7, r8, r9, r10, r11, r12, lr}
vpush {d0, d1}
mov r4, r0
ldr r5, =0x432000
ldr r0, [r5, #0x90]
cmp r0, #0
beq scene_capture_done
ldr r0, [r5, #0x94]
cmp r0, #1
bne gpu_render_after_view
mrc p15, 0, r0, c13, c0, 3
ldr r1, [r5, #0x98]
cmp r0, r1
bne scene_capture_done
ldr r6, [r5, #8]
tst r6, #1
bne scene_capture_done
cmp r4, #0
beq scene_capture_done
mov r0,r4
bl hand_buffer_select
mov r7,r1
mov r8,r7
mov r0,r2
ldr r9, [r4, #0x58]
cmp r9, #0
beq scene_capture_done
add r1, r9, r9, lsl #1
sub r0, r0, r7
cmp r0, r1, lsl #4
bne scene_capture_done
cmp r9, #128
bhi scene_capture_done
cmp r7, #0
beq scene_capture_done
ldr r5, =0x433000
ldr r10, [r5]
mov r11, #0
scene_capture_lookup:
cmp r10, #0
beq scene_capture_missing
ldr r0, [r10, #4]
cmp r0, r4
beq scene_capture_found
cmp r0, #0
bne scene_capture_next
ldr r0, [r10, #28]
cmp r0, r9
movhs r11, r10
scene_capture_next:
ldr r10, [r10]
b scene_capture_lookup
scene_capture_missing:
cmp r11, #0
movne r10, r11
bne scene_capture_reuse
ldr r0, [r5, #4]
cmp r0, #0
moveq r0, #64
add r1, r9, r9, lsl #1
lsl r1, r1, #5
add r1, r1, #32
add r2, r0, r1
cmp r2, #0x40000
bhi scene_capture_overflow
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
scene_capture_reuse:
mov r3, #2
b scene_capture_configure
scene_capture_found:
ldr r0, [r10, #8]
cmp r0, r7
ldreq r0, [r10, #12]
cmpeq r0, r8
ldreq r0, [r10, #16]
cmpeq r0, r9
bne scene_capture_changed_layout
ldr r0, [r10, #20]
cmp r0, r6
moveq r3, #0
beq scene_capture_configure
add r0, r0, #2
cmp r0, r6
moveq r3, #1
movne r3, #2
b scene_capture_configure
scene_capture_changed_layout:
ldr r0, [r10, #28]
cmp r0, r9
blo scene_capture_invalidate_large
mov r3, #2
scene_capture_configure:
str r4, [r10, #4]
str r7, [r10, #8]
str r8, [r10, #12]
str r9, [r10, #16]
str r6, [r10, #20]
add r1, r10, #32
ldr r2, [r10, #24]
scene_capture_capture_bone:
mov r12, #12
scene_capture_capture_float:
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
bne scene_capture_capture_float
subs r9, r9, #1
bne scene_capture_capture_bone
b scene_capture_done
scene_capture_invalidate_large:
mov r0, #0
str r0, [r10, #4]
b scene_capture_done
scene_capture_overflow:
ldr r0, [r5, #12]
add r0, r0, #1
str r0, [r5, #12]
scene_capture_done:
vpop {d0, d1}
pop {r4, r5, r6, r7, r8, r9, r10, r11, r12, pc}

scene_render:

push {r4, r5, r6, r7, r8, r9, r10, r11, r12, lr}
vpush {d0,d1,d2,d3,d4,d5,d6,d7}
mov r11, r0
ldr r4, =0x432000
ldr r0, [r4, #0x90]
cmp r0, #0
beq scene_render_done
ldr r5, [r4, #8]
vldr s2, [r4, #0xb0]
ldr r4, =0x433000
ldr r4, [r4]
scene_render_entry:
cmp r4, #0
beq scene_render_done
ldr r0, [r4, #4]
cmp r0, #0
beq scene_render_next
ldr r6, [r4, #8]
ldr r7, [r4, #12]
ldr r8, [r4, #16]
bl hand_buffer_select
cmp r1,r6
bne scene_render_next
mov r1,r2
add r2, r8, r8, lsl #1
add r2, r6, r2, lsl #4
cmp r1, r2
bne scene_render_next
add r9, r4, #32
ldr r10, [r4, #24]
mov r3, #0
cmp r11, #0
beq scene_render_bone
tst r5, #1
bne scene_render_bone
ldr r0, [r4, #20]
cmp r0, r5
moveq r3, #1
scene_render_bone:
mov r12, #12
scene_render_float_loop:
vldr s0, [r10]
cmp r3, #0
beq scene_render_store
vldr s1, [r9]
vadd.f32 s0, s0, s1
vmul.f32 s0, s0, s2
scene_render_store:
vstr s0, [r6]
vstr s0, [r7]
add r6, r6, #4
add r7, r7, #4
add r9, r9, #4
add r10, r10, #4
subs r12, r12, #1
bne scene_render_float_loop
bl hand_world_caller
bne scene_render_bone
scene_render_next:
ldr r4, [r4]
b scene_render_entry
scene_render_done:
vpop {d0,d1,d2,d3,d4,d5,d6,d7}
pop {r4, r5, r6, r7, r8, r9, r10, r11, r12, pc}

scene_invalidate:

push {r1, r2, r3, lr}
ldr r1, =0x433000
ldr r1, [r1]
scene_invalidate_loop:
cmp r1, #0
beq scene_invalidate_done
ldr r2, [r1, #4]
cmp r2, r0
moveq r3, #0
streq r3, [r1, #4]
ldr r1, [r1]
b scene_invalidate_loop
scene_invalidate_done:
pop {r1, r2, r3, pc}

scene_clear:

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

scene_kill_thunk:
push {r0,lr}; bl scene_clear; pop {r0,lr}; mov r1,#0; b 0x13e220;
scene_init_thunk:
push {r0,lr}; bl scene_clear; pop {r0,lr}; .word 0xe92d41f0; b 0x1dcba4;
stereo_capture:

ldr r12, =0x432000
ldr r3, [r12,#0xe00]
cmp r2,r3
addeq r12,r12,#0xc00
stmiaeq r12,{r0,r1,r2}
vstreq d0,[r12,#16]
str lr,[sp,#-4]!
b 0x265b8c

gpu_render_after_view:
mov r0,#1; bl scene_render; b scene_capture_done
glove_scale_midpoint:

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

hand_world_caller:

push {r3,lr}
sub sp,sp,#16
cmp r3,#0
beq hand_world_caller_finish
ldr r0,[r4,#4]
ldr r1,[r0,#0x40]
ldr r0,[r4,#8]
cmp r0,r1
bne hand_world_caller_finish
sub r3,r10,#48
mov r0,sp
mov r1,r3
bl 0x25f978
bl glove_scale_midpoint
mov r2,sp
sub r0,r6,#48
bl 0x224ae0
vmov.f32 s2,#0.5
hand_world_caller_finish:
add sp,sp,#16
subs r8,r8,#1
pop {r3,pc}

hand_buffer_select:

mov r12,#0x50
ldr r1,[r0,#0x58]
cmp r1,#4
bne hand_buffer_select_selected
ldr r1,[r0,#8]
ldr r2,[r1,#0x1c]!
add r1,r1,r2
ldr r2,[r1,#0x34]!
add r1,r1,r2
ldr r1,[r1]
ldr r2,=0x646e6148
cmp r1,r2
moveq r12,#0x40
hand_buffer_select_selected:
ldr r1,[r0,r12]
add r12,r12,#4
ldr r2,[r0,r12]
bx lr
