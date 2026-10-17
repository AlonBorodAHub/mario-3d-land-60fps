"""Camera helper that refreshes the actual stereo cameras after central LookAt.

Native 0x265b88 receives projection, central camera and separation parameters.
Retain its most recent arguments and replay only for the same central camera.
"""
from camera_helper import CAMERA_ASM, CAMERA_BODY_ASM as ORIGINAL_BODY
diagnostic=ORIGINAL_BODY[ORIGINAL_BODY.index('cmp r9, #0\nbeq store_final'):ORIGINAL_BODY.index('store_final:')]
CAMERA_BODY_ASM=ORIGINAL_BODY.replace(diagnostic,'').replace(
 'bl 0x36de80\npop {r0, pc}',
 '''bl 0x36de80
ldr r12, =0x432c00
ldmia r12, {r0,r1,r2}
ldr r3, [sp]
cmp r2, r3
vldreq d0, [r12,#16]
bleq 0x265b88
pop {r0, pc}''')
STEREO_CAPTURE_ASM='''
ldr r12, =0x432c00
stmia r12, {r0,r1,r2}
vstr d0, [r12,#16]
str lr, [sp,#-4]!
b 0x265b8c
'''
