#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"

target="${1:-linux-x86_64-gcc-py312-release}"
python_exe="${PYTHON_EXE:-python3}"
constraints_file="${CONSTRAINTS_FILE:-${repo_root}/constraints/py312.txt}"
venv_dir="${repo_root}/.venvs/${target}"
wheelhouse_dir="${repo_root}/external/wheelhouse/vtk-9.3.1/${target}"
audit_script="${repo_root}/scripts/validate/audit-environment.py"
tmp_dir="${repo_root}/.tmp"

get_vtk_wheel() {
  local wheel
  wheel="$(find "${wheelhouse_dir}" -maxdepth 1 -type f -name 'vtk-*.whl' | sort | tail -n 1)"
  if [[ -z "${wheel}" ]]; then
    echo "No vtk wheel was found in ${wheelhouse_dir}. Build VTK and generate the wheel first." >&2
    exit 1
  fi
  printf '%s\n' "${wheel}"
}

if [[ ! -x "${venv_dir}/bin/python" ]]; then
  "${python_exe}" -m venv "${venv_dir}"
fi

venv_python="${venv_dir}/bin/python"

"${venv_python}" "${audit_script}" --mode strict --target-venv "${venv_dir}"
vtk_wheel="$(get_vtk_wheel)"
"${venv_python}" -m pip install --no-deps --force-reinstall "${vtk_wheel}"
installed_vtk_version="$("${venv_python}" -c "import importlib.metadata; print(importlib.metadata.version('vtk'))")"
mkdir -p "${tmp_dir}"
vtk_constraint_file="${tmp_dir}/vtk-constraint-${target}.txt"
printf 'vtk===%s\n' "${installed_vtk_version}" > "${vtk_constraint_file}"
"${venv_python}" -m pip install --constraint "${constraints_file}" --constraint "${vtk_constraint_file}" pyvista
"${venv_python}" -m pip install "${repo_root}/packages/codecpp"
"${venv_python}" -m pip install -e "${repo_root}/packages/codepy"
"${venv_python}" -m pip install -e "${repo_root}/packages/pmanager"
