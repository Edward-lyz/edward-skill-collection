@echo off
setlocal
rem Print the platform, the Nsys CLI, and the bundled Python interpreter

for %%I in ("%~dp0..\..\..") do set "ROOT=%%~fI"

rem 1. The host-<platform> directory names the platform authoritatively
set "PLATFORM="
for /d %%I in ("%ROOT%\host-*") do (
    if not defined PLATFORM set "PLATFORM=%%~nxI"
)
if defined PLATFORM set "PLATFORM=%PLATFORM:host-=%"
rem 2. Else derive from this host's architecture (the OS is Windows here)
if defined PLATFORM goto :have_platform
set "PLATFORM=windows-x64"
if /i "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "PLATFORM=windows-armv8"
:have_platform
echo Platform: %PLATFORM%


rem CLI: NSYS_PATH when set, else the target tree for that platform, then PATH
set "NSYS=%NSYS_PATH%"
if not defined NSYS set "NSYS=%ROOT%\target-%PLATFORM%\nsys.exe"
if not defined NSYS_PATH if not exist "%NSYS%" (
    for /f "delims=" %%I in ('where nsys 2^>nul') do set "NSYS=%%I"
)
if not exist "%NSYS%" (
    echo ERROR: Could not resolve the Nsys CLI path on this platform.
    exit /b 1
)
echo Nsys CLI: "%NSYS%"

for %%I in ("%NSYS%") do set "PY=%%~dpIpython\bin\python.exe"
if not exist "%PY%" (
    echo ERROR: Could not find the bundled Nsys Python interpreter.
    exit /b 1
)
echo Nsys Python interpreter: "%PY%"

rem No bundled Python in test environment.  Skip.
if defined NSYS_SKILL_UNIT_TEST exit /b 0

rem Report any packaged report dependencies missing from the bundled Python
"%PY%" "%~dp0_core\check_report_dependencies.py" >nul 2>nul || (
    echo ERROR: Failed to validate bundled Nsys Python dependencies.
    exit /b 1
)
setlocal enabledelayedexpansion
set "MISSING="
for /f "delims=" %%I in ('""!PY!" "%~dp0_core\check_report_dependencies.py" 2^>nul"') do set "MISSING=%%I"
if defined MISSING (
    echo ERROR: Bundled Nsys Python is missing dependencies: %MISSING%.
    exit /b 1
)

rem Leave the resolved path where the packaged Python tools pick it up
set "CACHE=%NSYS_TMPDIR%"
if not defined CACHE set "CACHE=%USERPROFILE%\AppData\Local\Temp"
set "CACHE=%CACHE%\nvidia\nsight_systems\nsys-skill-cache"
if not exist "%CACHE%" mkdir "%CACHE%" >nul 2>nul
if not exist "%CACHE%" exit /b 0
setlocal enabledelayedexpansion
>"%CACHE%\NSYS_PATH" echo !NSYS!