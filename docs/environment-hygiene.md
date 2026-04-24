# Environment Hygiene

## Why this matters

This repository is designed for numerical simulation work on research
workstations. Those machines may already expose unmanaged SDKs and Python
packages globally.

On the current Windows machine used for development, there are already examples of:

- global `INCLUDE` and `LIB`
- pre-existing `vtk==9.3.1` outside any project venv
- injected `sys.path` entries unrelated to this repository

That is why the repo must audit and sanitize the parts of the environment that
can silently change build or runtime behavior.

The goal is not to build a heavyweight isolation framework. The goal is to make
daily lab development reproducible enough that a successful run means something.

## Variables treated as unsafe by default

### Python-related

- `PYTHONPATH`
- `PYTHONHOME`
- `PYTHONSTARTUP`
- `VIRTUAL_ENV` when it does not match the target
- `PIP_INDEX_URL`
- `PIP_EXTRA_INDEX_URL`
- `PIP_FIND_LINKS`
- `PIP_CONSTRAINT`
- `PIP_REQUIRE_VIRTUALENV`

### Native/CMake-related

- `CMAKE_PREFIX_PATH`
- `VTK_DIR`
- `CMAKE_TOOLCHAIN_FILE`
- `INCLUDE`
- `LIB`
- `LIBRARY_PATH`
- `CPATH`

### Runtime-loader-related

- `PATH`
- `LD_LIBRARY_PATH`
- `DYLD_LIBRARY_PATH`

### Environment managers

- `CONDA_PREFIX`
- `CONDA_DEFAULT_ENV`

## Repo policy

- Sanitized shell entry scripts construct a minimal environment instead of inheriting everything.
- Audit scripts can run in `audit` mode or `strict` mode.
- `strict` mode must fail on suspicious global injections.
- `PYTHONNOUSERSITE=1` is forced during repo-managed validation.
- Prefer simple, explicit checks over broad compatibility machinery.
- Assume normal network access for installing basic Python development tools.

## Practical guidance

### Windows

- Prefer `cmd.exe` for user-facing commands and day-to-day testing.
- PowerShell is still used by some existing scripts during the transition, but
  new instructions should avoid requiring PowerShell knowledge.
- Do not reuse a terminal that has already sourced historical SDK setup scripts.
- Treat any successful run from a "dirty" shell as untrusted until it also succeeds in a clean repo shell.
- As the Python-first workflow grows, add thin `.cmd` wrappers before asking the
  user to run PowerShell directly.

### Ubuntu

- Start with `scripts/ubuntu/enter-clean-dev-shell.sh`.
- Do not source `/opt/vtk-*` helper scripts before using the repo.
- Prefer `env -i`-style isolation for reproducibility.

## Success criterion

A supported command sequence must remain valid after removing:

- global Python site-package injections
- global VTK-related path entries
- native build helper variables inherited from unrelated projects

## Important nuance

A clean shell is necessary, but not sufficient.

If the selected interpreter is itself a global Python installation that already contains `vtk` in its own `site-packages`, then:

- `PYTHONNOUSERSITE=1` will not hide that package
- a sanitized `PATH` will not hide that package
- the audit must still report it

For this reason, all supported repo workflows must switch to a target venv before any meaningful runtime validation.
