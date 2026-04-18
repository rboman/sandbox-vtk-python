#!/bin/bash
set -eu

# install VTK

if [ ! -d VTKBIN ] ; then
    echo "build VTK first!"
    exit
fi
cd VTKBIN
sudo ninja install
sudo chmod -R a+rX /opt/vtk-9.3.1
sudo ln -s /opt/vtk-9.3.1 /opt/vtk

# load env variables: (in "linuxbin")
#   add2env PATH "/opt/vtk/bin" front
#   add2env LD_LIBRARY_PATH "/opt/vtk/lib"
#   add2env PYTHONPATH "/opt/vtk/lib/python3.12/site-packages"
#   add2env INCLUDE "/opt/vtk/include" front
#   add2env LIB "/opt/vtk/lib" front
#   add2env CMAKE_PREFIX_PATH "/opt/vtk" front
#
# then:
#   python3 -c "import vtk; print(vtk.vtkVersion.GetVTKVersion())"
