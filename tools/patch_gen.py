#!/usr/bin/env python3
"""Applies the port's hand edits to freshly lifted LEGO Marvel code in gen/.
Usage: python3 tools/patch_gen.py [GEN_DIR]   (run after tools/lift.py)
Each edit is found by function and exact text, so it does not depend on
which gen/exe_NN.c file the lifter put the function in. Safe to re-run."""
import glob, os, re, sys

GEN = sys.argv[1] if len(sys.argv) > 1 else "gen"
PROTO = "int port_async_shaders(void);\n"

# (function, old text, new text, needs the port_async_shaders prototype)
EDITS = [
    # Display mode filter: keep modes below 800x600 so the resolution scaler works.
    ("f_6E1920",
     "    ebp = (uint32_t)((uint32_t)0x258u);\n",
     "    ebp = (uint32_t)((uint32_t)0x0u);  /* port: was 600, keep every scaled mode */\n", False),
    ("f_6E1920",
     "    (void)sub32(M32((uint32_t)(eax)), (uint32_t)0x320u, &f);\n",
     "    (void)sub32(M32((uint32_t)(eax)), (uint32_t)0x0u, &f);  /* port: was 800 */\n", False),
    # Per-material shader fetch: always take the game's queued (worker thread) path.
    ("f_652EA0",
     "L_652FD2:\n    (void)logic8((uint8_t)(((uint8_t)ebx) & ((uint8_t)ebx)), &f);\n    if (f.zf) goto L_653098;\n",
     "L_652FD2:\n    (void)logic8((uint8_t)(((uint8_t)ebx) & ((uint8_t)ebx)), &f);\n"
     "    if (f.zf || port_async_shaders()) goto L_653098; /* PORT: always queue on workers */\n", True),
    # pcconfig DisableMultithreadedShaders setter: keep the worker threads on.
    ("f_6D3E20",
     "    M8((uint32_t)(0x147102Eu)) = (uint8_t)(((uint8_t)ecx));\n",
     "    M8((uint32_t)(0x147102Eu)) = (uint8_t)(((uint8_t)ecx));\n"
     "    if (port_async_shaders()) M8((uint32_t)(0x147102Eu)) = 0; /* PORT: keep worker threads on */\n", True),
]

def func_span(src, name):
    m = re.search(r"^void %s\(CPU \*c\) \{\n" % name, src, re.M)
    if not m:
        return None
    end = src.find("\nvoid f_", m.end())
    return m.start(), (len(src) if end < 0 else end)

files = sorted(glob.glob(os.path.join(GEN, "exe_*.c")))
fail = 0
for fn, old, new, proto in EDITS:
    for path in files:
        src = open(path).read()
        span = func_span(src, fn)
        if not span:
            continue
        body = src[span[0]:span[1]]
        if new in body:
            print(f"{fn}: already patched ({os.path.basename(path)})")
        elif old in body:
            src = src[:span[0]] + body.replace(old, new, 1) + src[span[1]:]
            if proto and PROTO not in src:
                src = src.replace('#include "lift_prelude.h"\n', '#include "lift_prelude.h"\n' + PROTO, 1)
            open(path, "w").write(src)
            print(f"{fn}: patched ({os.path.basename(path)})")
        else:
            print(f"{fn}: pattern NOT found in {os.path.basename(path)}"); fail = 1
        break
    else:
        print(f"{fn}: function not found"); fail = 1
sys.exit(fail)
