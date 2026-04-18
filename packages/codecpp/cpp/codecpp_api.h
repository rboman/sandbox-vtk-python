#pragma once

#include <string>

namespace codecpp {

std::string vtk_version();
int sphere_point_count(int theta_resolution = 8, int phi_resolution = 8);

}  // namespace codecpp
