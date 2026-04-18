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

if [[ ! -x "${venv_dir}/bin/python" ]]; then
  "${python_exe}" -m venv "${venv_dir}"
fi

venv_python="${venv_dir}/bin/python"

"${venv_python}" "${audit_script}" --mode strict --target-venv "${venv_dir}"
"${venv_python}" -m pip install --no-deps --no-index --find-links "${wheelhouse_dir}" vtk==9.3.1
"${venv_python}" -m pip install --constraint "${constraints_file}" pyvista
"${venv_python}" -m pip install "${repo_root}/packages/codecpp"
"${venv_python}" -m pip install -e "${repo_root}/packages/codepy"
"${venv_python}" -m pip install -e "${repo_root}/packages/pmanager"
