ARM source for the patch cave and repurposed native stride block.
Cave source is assembled at 0x3a177c minus its symbol table size (24 words); the table is discarded from the installed code. Input entry contains a post-assembly PC-relative load fixup, so this source is for review and is not a standalone rebuild kit.
Use code.ips as the tested distributable.
