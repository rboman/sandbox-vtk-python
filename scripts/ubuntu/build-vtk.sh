#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"

target="${1:-linux-x86_64-gcc-py312-release}"
python_exe="${PYTHON_EXE:-python3}"
venv_dir="${repo_root}/.venvs/${target}"
vtk_source_dir="${repo_root}/external/src/vtk-9.3.1"
build_dir="${repo_root}/external/build/vtk-9.3.1/${target}"
install_dir="${repo_root}/external/install/vtk-9.3.1/${target}/sdk"
wheelhouse_dir="${repo_root}/external/wheelhouse/vtk-9.3.1/${target}"
audit_script="${repo_root}/scripts/validate/audit-environment.py"
manifest_path="${build_dir}/build-manifest.json"

ensure_wheel_support() {
  if "${resolved_python}" -c "import wheel.bdist_wheel" >/dev/null 2>&1; then
    return
  fi

  echo "Installing missing 'wheel' package into the target venv..."
  "${resolved_python}" -m pip install wheel
  "${resolved_python}" -c "import wheel.bdist_wheel" >/dev/null
}

if [[ ! -d "${venv_dir}" ]]; then
  echo "Target venv does not exist yet: ${venv_dir}. Run sync-venv first." >&2
  exit 1
fi

resolved_python="$(command -v "${python_exe}")"
if [[ -z "${resolved_python}" ]]; then
  echo "Unable to resolve python executable: ${python_exe}" >&2
  exit 1
fi

case "${resolved_python}" in
  "${venv_dir}"/*) ;;
  *)
    echo "PYTHON_EXE must resolve inside the target venv. Expected under ${venv_dir} but got ${resolved_python}." >&2
    exit 1
    ;;
esac

mkdir -p "${build_dir}" "${install_dir}" "${wheelhouse_dir}"

"${resolved_python}" "${audit_script}" --mode strict --target-venv "${venv_dir}" --target-sdk-root "${install_dir}"

cmake \
  -S "${vtk_source_dir}" \
  -B "${build_dir}" \
  -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="${install_dir}" \
  -DVTK_WRAP_PYTHON=ON \
  -DVTK_WHEEL_BUILD=ON \
  -DPython3_EXECUTABLE="${resolved_python}" \
  -DVTK_GROUP_ENABLE_Qt=WANT \
  -DVTK_MODULE_ENABLE_VTK_GUISupportQtQuick=DONT_WANT \
  -DVTK_GROUP_ENABLE_Rendering=WANT \
  -DVTK_GROUP_ENABLE_Views=WANT \
  -DVTK_GROUP_ENABLE_StandAlone=WANT \
  -DVTK_MODULE_ENABLE_VTK_RenderingOpenGL2=WANT \
  -DVTK_MODULE_ENABLE_VTK_InteractionStyle=WANT \
  -DVTK_MODULE_ENABLE_VTK_RenderingMatplotlib=WANT

cmake --build "${build_dir}"
cmake --install "${build_dir}"

if [[ -f "${build_dir}/setup.py" ]]; then
  ensure_wheel_support
  (
    cd "${build_dir}"
    "${resolved_python}" setup.py bdist_wheel --dist-dir "${wheelhouse_dir}"
  )
fi

"${resolved_python}" - <<'PY' "${manifest_path}" "${target}" "${resolved_python}" "${vtk_source_dir}" "${build_dir}" "${install_dir}" "${wheelhouse_dir}"
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
manifest = {
    "target": sys.argv[2],
    "python_executable": sys.argv[3],
    "vtk_source_dir": sys.argv[4],
    "build_dir": sys.argv[5],
    "install_dir": sys.argv[6],
    "wheelhouse_dir": sys.argv[7],
    "vtk_version": "9.3.1",
    "generator": "Ninja",
}
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
PY
