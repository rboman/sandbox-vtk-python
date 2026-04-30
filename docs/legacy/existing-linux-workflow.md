# Existing Linux workflow

A Linux/Ubuntu workflow already exists and is considered a valuable reference.

## What is already validated

Current shell scripts do the following:

- download VTK 9.3.1
- configure VTK with Python wrapping enabled
- enable VTK wheel build
- build VTK
- create a local Python wheel
- install VTK under `/opt/vtk-9.3.1`
- expose native and Python-related paths through environment variables

## Important observations

- The current VTK build is intended to be fairly complete, not minimal.
- The current workflow already treats Python wrapping and wheel generation as first-class concerns.
- The current install script mixes compile-time and runtime concerns in one install tree; this is acceptable as a reference, but the sandbox repository should document the roles more explicitly.

## References

See:
- `scripts/reference/ubuntu/build_vtk_wheel.sh`
- `scripts/reference/ubuntu/install_vtk_wheel.sh`