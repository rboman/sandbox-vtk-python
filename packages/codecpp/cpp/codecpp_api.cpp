#include "codecpp_api.h"

#include <vtkNew.h>
#include <vtkSphereSource.h>
#include <vtkVersion.h>

namespace codecpp {

std::string vtk_version() {
    return vtkVersion::GetVTKVersion();
}

int sphere_point_count(int theta_resolution, int phi_resolution) {
    vtkNew<vtkSphereSource> sphere;
    sphere->SetThetaResolution(theta_resolution);
    sphere->SetPhiResolution(phi_resolution);
    sphere->Update();
    return sphere->GetOutput()->GetNumberOfPoints();
}

}  // namespace codecpp
