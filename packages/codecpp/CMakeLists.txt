cmake_minimum_required(VERSION 3.24)
project(codecpp LANGUAGES CXX)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(SWIG REQUIRED)
include(UseSWIG)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_SWIG_OUTDIR "${CMAKE_CURRENT_BINARY_DIR}/python/codecpp")
file(MAKE_DIRECTORY "${CMAKE_SWIG_OUTDIR}")

find_package(VTK 9.3.1 CONFIG REQUIRED COMPONENTS
  CommonCore
  FiltersSources
)

set(vtk_link_targets
  VTK::CommonCore
  VTK::FiltersSources
)

set_property(SOURCE swig/codecpp.i PROPERTY CPLUSPLUS ON)
set_property(SOURCE swig/codecpp.i PROPERTY USE_TARGET_INCLUDE_DIRECTORIES TRUE)

swig_add_library(_codecpp
  TYPE MODULE
  LANGUAGE python
  SOURCES
    swig/codecpp.i
    cpp/codecpp_api.cpp
)

target_include_directories(_codecpp PRIVATE cpp)
target_link_libraries(_codecpp PRIVATE Python3::Module ${vtk_link_targets})

if(COMMAND vtk_module_autoinit)
  vtk_module_autoinit(
    TARGETS _codecpp
    MODULES ${vtk_link_targets}
  )
endif()

if(UNIX AND NOT APPLE)
  set_target_properties(_codecpp PROPERTIES
    BUILD_WITH_INSTALL_RPATH ON
    INSTALL_RPATH "$ORIGIN;$ORIGIN/..;$ORIGIN/../vtkmodules;$ORIGIN/../vtk.libs"
  )
endif()

install(
  TARGETS _codecpp
  LIBRARY DESTINATION codecpp
  RUNTIME DESTINATION codecpp
  ARCHIVE DESTINATION codecpp
)

install(
  FILES
    "${CMAKE_SWIG_OUTDIR}/codecpp.py"
    src/codecpp/__init__.py
    src/codecpp/_runtime.py
    src/codecpp/_version.py
  DESTINATION codecpp
)
