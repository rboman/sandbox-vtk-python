#!/bin/bash

# build VTK-9 on Ubuntu 24.04 due to bug in XML format handling
#
# debian/vaillant: j'ai dû installer
#   sudo apt install libglvnd-dev
# VTK s’attend à trouver une version de GL gérée par GLVND 
# (OpenGL Vendor Neutral Dispatch). GLVND permet une meilleure cohabitation 
# entre plusieurs implémentations OpenGL (par exemple Mesa et NVIDIA).

if [ ! -d VTK-9.3.1 ] ; then
    wget https://www.vtk.org/files/release/9.3/VTK-9.3.1.tar.gz
    tar xf VTK-9.3.1.tar.gz
    rm VTK-9.3.1.tar.gz
fi

if [ ! -d VTKBIN ] ; then
    mkdir VTKBIN
fi
cd VTKBIN


# faster build
export CMAKE_GENERATOR=Ninja

# note: module "QtQuick" is not installed
#   => GUISupportQtQuick=DONT_WANT

cmake -Wno-dev \
      -DCMAKE_BUILD_TYPE=Release    \
      -DCMAKE_INSTALL_PREFIX=/opt/vtk-9.3.1   \
      -DVTK_GROUP_ENABLE_Qt=WANT \
      -DVTK_MODULE_ENABLE_VTK_GUISupportQtQuick=DONT_WANT \
      -DVTK_WRAP_PYTHON=ON \
      -DPython3_EXECUTABLE=$(which python) \
      -DVTK_WHEEL_BUILD=ON \
      -DVTK_MODULE_ENABLE_VTK_RenderingMatplotlib=WANT \
      -DVTK_GROUP_ENABLE_Rendering=WANT \
      -DVTK_GROUP_ENABLE_Views=WANT \
      -DVTK_GROUP_ENABLE_StandAlone=WANT \
      -DVTK_MODULE_ENABLE_VTK_RenderingOpenGL2=WANT \
      -DVTK_MODULE_ENABLE_VTK_InteractionStyle=WANT \
      ../VTK-9.3.1   | tee cmake-log.txt

# build vtk
ninja | tee build-log.txt

# create wheel (used explictely for "pip install" in venv)
python3 setup.py bdist_wheel | tee wheel-log.txt
