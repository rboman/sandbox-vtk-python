#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
target="${1:-}"

clean_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

if [[ $# -gt 1 ]]; then
  shift
  exec env -i \
    HOME="${HOME}" \
    USER="${USER:-}" \
    LOGNAME="${LOGNAME:-${USER:-}}" \
    SHELL="${SHELL:-/bin/bash}" \
    TERM="${TERM:-xterm-256color}" \
    LANG="${LANG:-C.UTF-8}" \
    PATH="${clean_path}" \
    PYTHONNOUSERSITE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SANDBOX_VTK_PYTHON_REPO_ROOT="${repo_root}" \
    SANDBOX_VTK_PYTHON_TARGET="${target}" \
    bash --noprofile --norc -lc "$*"
fi

echo "Prepared sanitized environment for sandbox-vtk-python"
echo "Repo root: ${repo_root}"
if [[ -n "${target}" ]]; then
  echo "Target: ${target}"
fi

exec env -i \
  HOME="${HOME}" \
  USER="${USER:-}" \
  LOGNAME="${LOGNAME:-${USER:-}}" \
  SHELL="${SHELL:-/bin/bash}" \
  TERM="${TERM:-xterm-256color}" \
  LANG="${LANG:-C.UTF-8}" \
  PATH="${clean_path}" \
  PYTHONNOUSERSITE=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  SANDBOX_VTK_PYTHON_REPO_ROOT="${repo_root}" \
  SANDBOX_VTK_PYTHON_TARGET="${target}" \
  bash --noprofile --norc
