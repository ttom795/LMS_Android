#!/bin/sh
# Regenerates gen/ (recompiled C) from your own LEGO Marvel Super Heroes files.
# Usage: tools/regen_gen.sh GAME_DIR
# GAME_DIR must contain LEGOMARVEL.exe, D3DX9_43.dll and D3DCompiler_43.dll
# (the DLLs may be in GAME_DIR/redist). See docs/GAME_FILES.md.
# Needs Python 3.10+: pip install capstone==5.0.9 pefile==2024.8.26
set -e
G=$(cd "${1:?usage: tools/regen_gen.sh GAME_DIR}" && pwd)
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
find_file() { for d in "$G" "$G/redist" "$G/Redist"; do for f in "$d"/*; do
    [ "$(echo "${f##*/}" | tr A-Z a-z)" = "$1" ] && { echo "$f"; return; }; done; done
    echo "missing $1 in $G" >&2; exit 1; }
EXE=$(find_file legomarvel.exe); D3DX=$(find_file d3dx9_43.dll); D3DC=$(find_file d3dcompiler_43.dll)
mkdir -p analysis gen
export LIFT_GAME=marvel
# discover.py imports peimg.py from tools/, so run it from there.
(cd tools && python3 discover.py "$EXE" ../analysis/functions.json)
(cd tools && python3 discover.py "$D3DX" ../analysis/functions_d3dx.json 08000000)
(cd tools && python3 discover.py "$D3DC" ../analysis/functions_d3dc.json 09000000)
python3 tools/lift.py "$EXE" analysis/functions.json gen exe
python3 tools/lift.py "$D3DX" analysis/functions_d3dx.json gen d3dx9 08000000
python3 tools/lift.py "$D3DC" analysis/functions_d3dc.json gen d3dc 09000000
python3 tools/patch_gen.py gen
python3 tools/gen_d3d9_bridge.py runtime
echo "gen/ is ready"
