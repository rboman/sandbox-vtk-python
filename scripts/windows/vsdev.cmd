@echo off
setlocal

set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" (
  echo [vsdev] vswhere.exe not found: "%VSWHERE%"
  echo [vsdev] Install Visual Studio 2022 with C++ workload.
  exit /b 1
)

for /f "usebackq delims=" %%I in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSINSTALL=%%I"

if "%VSINSTALL%"=="" (
  echo [vsdev] No Visual Studio installation with MSVC tools was found.
  exit /b 1
)

set "VSDEVCMD=%VSINSTALL%\Common7\Tools\VsDevCmd.bat"
if not exist "%VSDEVCMD%" (
  echo [vsdev] VsDevCmd.bat not found: "%VSDEVCMD%"
  exit /b 1
)

echo [vsdev] Activating MSVC developer environment from:
echo [vsdev] %VSINSTALL%

endlocal & call "%VSDEVCMD%" -arch=x64 -host_arch=x64 %*
