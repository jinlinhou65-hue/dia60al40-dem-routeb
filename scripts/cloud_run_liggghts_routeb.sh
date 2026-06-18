#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$PWD}"
cd "$ROOT"

echo "[CLOUD] Ubuntu info"
cat /etc/os-release || true

echo "[CLOUD] install LIGGGHTS dependencies"
sudo apt-get update
sudo apt-get install -y build-essential gcc g++ gfortran make git \
  libopenmpi-dev openmpi-bin python3 python3-pip python3-matplotlib

if ! command -v liggghts >/dev/null 2>&1; then
  echo "[CLOUD] build LIGGGHTS-PUBLIC from source"
  rm -rf /tmp/lpub
  git clone --depth=1 https://github.com/CFDEMproject/LIGGGHTS-PUBLIC.git /tmp/lpub
  (
    cd /tmp/lpub/src
    ( cd STUBS && make 2>&1 | tail -10 )
    if ! make -j"$(nproc)" auto 2>&1 | tee /tmp/build_auto.log; then
      echo "[CLOUD] auto build failed; falling back to serial"
      make clean-all || true
      ( cd STUBS && make 2>&1 | tail -5 )
      make -j"$(nproc)" serial 2>&1 | tee /tmp/build_serial.log
    fi
    if [ -x lmp_auto ]; then sudo install -m 0755 lmp_auto /usr/local/bin/liggghts; fi
    if [ -x lmp_serial ]; then sudo install -m 0755 lmp_serial /usr/local/bin/liggghts; fi
  )
fi

echo "[CLOUD] LIGGGHTS binary"
command -v liggghts
liggghts -h >/tmp/liggghts_help.txt 2>&1 || true
head -40 /tmp/liggghts_help.txt
grep -q "LIGGGHTS" /tmp/liggghts_help.txt

echo "[CLOUD] prepare meshes"
python3 - <<'PY' > /tmp/dem_case_height.env
import os
from python.render_dem_deck import DIAMOND_CASES, initial_die_height_um
case = DIAMOND_CASES[os.environ.get("DIAMOND_SIZE_CASE", "C")]
print(f"HEIGHT_UM={initial_die_height_um(case):.9g}")
PY
source /tmp/dem_case_height.env
python3 python/prepare_meshes.py --height-um "$HEIGHT_UM"
python3 python/render_dem_deck.py \
  --input liggghts/in.dia60al40_dem_staged.liggghts \
  --output liggghts/in.dia60al40_dem_staged.rendered.liggghts \
  --diamond-size-case "${DIAMOND_SIZE_CASE:-C}" \
  --e-al-e0-gpa "${E_AL_E0_GPA:-5}" \
  --e-al-emax-gpa "${E_AL_EMAX_GPA:-12}" \
  --e-diamond-gpa "${E_DIAMOND_GPA:-300}" \
  --e-tool-gpa "${E_TOOL_GPA:-600}" \
  --e-wall-gpa "${E_WALL_GPA:-200}" \
  --mu-al-al "${MU_AL_AL:-0.30}" \
  --mu-al-diamond "${MU_AL_DIAMOND:-0.30}" \
  --mu-al-tool "${MU_AL_TOOL:-0.08}" \
  --mu-al-wall "${MU_AL_WALL:-0.08}" \
  --mu-diamond-diamond "${MU_DIAMOND_DIAMOND:-0.10}" \
  --mu-diamond-tool "${MU_DIAMOND_TOOL:-0.08}" \
  --mu-diamond-wall "${MU_DIAMOND_WALL:-0.08}" \
  --mu-scale "${MU_SCALE:-1.0}" \
  --seed-index "${DEM_SEED_INDEX:-0}"

echo "[CLOUD] run staged DEM"
cd liggghts
mkdir -p DEM
liggghts -in in.dia60al40_dem_staged.rendered.liggghts | tee dia60al40_liggghts_staged.run.log
cd "$ROOT"

echo "[CLOUD] verify staged DEM handoff dumps"
python3 python/verify_dem_stages.py --root liggghts/DEM
test -s liggghts/DEM/pressure_density_curve_raw.csv

echo "[CLOUD] convert stage dumps to COMSOL CSV"
for stage in stage0_preload stage1_rho065 stage2_rho072 stage3_rho080 stage4_rho088 stage5_rho095; do
  dump=$(ls -1 "liggghts/DEM/${stage}_"*.dump | sort -V | tail -1)
  python3 python/convert_liggghts_csv_to_comsol.py \
    --input "$dump" \
    --mode 2d \
    --auto-shrink-overlap \
    --clearance-um 0.02 \
    --output "liggghts/DEM/comsol_particles_${stage}.csv"
  python3 python/export_dem_stage_handoff.py \
    --input "$dump" \
    --stage-id "$stage" \
    --output "liggghts/DEM/dem_fem_handoff_${stage}.csv"
done

python3 python/export_pressure_density_curve.py \
  --root liggghts/DEM \
  --raw liggghts/DEM/pressure_density_curve_raw.csv \
  --output liggghts/DEM/pressure_density_curve.csv
cat liggghts/DEM/pressure_density_curve.csv
python3 python/analyze_pressure_density.py \
  --curve liggghts/DEM/pressure_density_curve.csv \
  --output liggghts/DEM/pressure_density_summary.csv \
  --target-rho 0.95 \
  --target-pressure-mpa 200
cat liggghts/DEM/pressure_density_summary.csv
python3 python/plot_dem_results.py \
  --root liggghts/DEM \
  --curve liggghts/DEM/pressure_density_curve.csv \
  --outdir liggghts/DEM/plots
python3 python/plot_plastic_morphology.py \
  --root liggghts/DEM \
  --outdir liggghts/DEM/plots \
  --metrics liggghts/DEM/plastic_morphology_metrics.csv
python3 scripts/process_stage_series.py \
  --snapshot-dir liggghts/DEM \
  --pressure-curve liggghts/DEM/pressure_density_curve.csv \
  --outdir liggghts/DEM/paper_reproduction \
  --width-um 400
echo "[CLOUD] paper reproduction acceptance"
cat liggghts/DEM/paper_reproduction/series_acceptance_summary.csv
find liggghts/DEM/plots -maxdepth 1 -type f | sort

echo "[CLOUD] done."
find liggghts/DEM -maxdepth 1 -type f | sort | tail -20
