# Open questions

- Should the same VTK build tree produce both the SDK install and the wheel, or should those be treated as separate configured builds?
- What is the cleanest Windows runtime strategy for locating VTK DLLs from `codecpp`?
- How much of the Linux runtime should rely on RPATH versus environment variables?
- What is the exact installation strategy for `pyvista` so that an unwanted `vtk` wheel is never pulled accidentally?
- Which parts of the repository should be editable installs in development?
- What should phase 1 validate on Windows only, Linux only, and both?
