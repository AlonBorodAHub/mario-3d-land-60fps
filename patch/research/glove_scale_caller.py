"""Average endpoint scales for render-only glove midpoints."""
from glove_render_hook import CALLER,HELPER,CALLER_ASM as ORIGINAL
CALLER_ASM=ORIGINAL.replace('bl 0x25f978\n','bl 0x25f978\nbl 0x3a1a84\n')
