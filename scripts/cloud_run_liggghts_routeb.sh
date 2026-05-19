#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$PWD}"
cd "$ROOT"

echo "[CLOUD] Ubuntu info"
cat /etc/os-release || true

echo "[CLOUD] install LIGGGHTS from Ubuntu universe if available"
sudo apt-get update
sudo apt-get install -y liggghts python3 python3-pip || {
  echo "[CLOUD] apt liggghts failed; falling back to source build is not implemented in this short runner script" >&2
  exit 20
}

echo "[CLOUD] LIGGGHTS binary"
command -v liggghts || command -v lmp_auto || command -v lmp || true
liggghts -h | head -40 || true

echo "[CLOUD] prepare meshes"
python3 python/prepare_meshes.py

echo "[CLOUD] run DEM"
cd liggghts
mkdir -p DEM
liggghts -in in.dia60al40_dem_preload.liggghts | tee dia60al40_liggghts.run.log
cd "$ROOT"

echo "[CLOUD] done. Export final VTK to CSV via ParaView, then run convert script. If pvpython is available, add automatic conversion here."
find liggghts/DEM -maxdepth 1 -type f | sort | tail -20
