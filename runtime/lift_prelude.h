/* Included by generated files only. */
#pragma once
#include <setjmp.h>
jmp_buf *rt_setjmp_slot(CPU *c, uint32_t guest_jb);
void rt_setjmp3(CPU *c);
#define SPILL() do { c->r[0] = eax; c->r[1] = ecx; c->r[2] = edx; c->r[3] = ebx; \
    c->r[4] = esp; c->r[5] = ebp; c->r[6] = esi; c->r[7] = edi; } while (0)
#define RELOAD() do { eax = c->r[0]; ecx = c->r[1]; edx = c->r[2]; ebx = c->r[3]; \
    esp = c->r[4]; ebp = c->r[5]; esi = c->r[6]; edi = c->r[7]; } while (0)
static inline void rt_movsd(uint32_t n, uint32_t dst, uint32_t src) {
    /* forward rep movsd; overlapping copies must behave like the dword loop */
    if (dst <= src || dst >= src + n * 4) memmove(MEM + dst, MEM + src, (size_t)n * 4);
    else for (uint32_t k = 0; k < n; k++) M32(dst + 4 * k) = M32(src + 4 * k);
}
#pragma GCC diagnostic ignored "-Wunused-label"
#pragma GCC diagnostic ignored "-Wunused-variable"
#pragma GCC diagnostic ignored "-Wunused-but-set-variable"
