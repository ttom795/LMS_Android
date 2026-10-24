/* Recompiled modules linked into this build. */
#include "game.h"
#include "rt_table.h"

extern const FnEntry g_fn_table_exe[];
extern const unsigned g_fn_count_exe;
extern const FnEntry g_fn_table_d3dx9[];
extern const unsigned g_fn_count_d3dx9;
#ifdef GAME_MARVEL
/* LEGO Marvel: D3DX9_43 and D3DCompiler_43 (runtime HLSL compiles). */
#define g_fn_table_bink g_fn_table_d3dc
#define g_fn_count_bink g_fn_count_d3dc
#define DLL1 "d3dx9_43.dll"
#define DLL2 "D3DCompiler_43.dll"
#else
#define DLL1 "d3dx9_35.dll"
#define DLL2 "binkw32.dll"
#endif
extern const FnEntry g_fn_table_bink[];
extern const unsigned g_fn_count_bink;

const FnModule g_modules[] = {
    {GAME_EXE, g_fn_table_exe, 0},
    {DLL1, g_fn_table_d3dx9, 0},
    {DLL2, g_fn_table_bink, 0},
};
const unsigned g_nmodules = sizeof g_modules / sizeof g_modules[0];

/* Counts are link-time constants in other translation units. */
unsigned rt_module_count(unsigned m) {
    switch (m) {
    case 0: return g_fn_count_exe;
    case 1: return g_fn_count_d3dx9;
    case 2: return g_fn_count_bink;
    default: return 0;
    }
}

/* Recompiled DLLs loaded at startup, from the game directory. */
const char *const g_dll_modules[] = {DLL1, DLL2, NULL};
const uint32_t g_dll_bases[] = {0x08000000u, 0x09000000u, 0};
