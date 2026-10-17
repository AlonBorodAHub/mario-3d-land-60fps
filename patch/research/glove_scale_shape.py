"""V3 shape preservation with signed determinant fallback and the same two passes."""
from glove_shape_helper import SHAPE_ASM as ORIGINAL
SHAPE_ASM=ORIGINAL.replace('bic r2,r2,#0x80000000\n','').replace('addhs r1,sp,#48','addge r1,sp,#48').replace('movlo r1,r7','movlt r1,r7')
