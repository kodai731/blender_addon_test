@echo off
setlocal enabledelayedexpansion

set "PROJECT_DIR=%CD%"
set "ADDON_DIR=%AppData%\Blender Foundation\Blender\4.0\scripts\addons"
set "WHEEL_DIR=%CD%\target\wheels"
set "TMP_DIR=%PROJECT_DIR%\TMP"
set "OUTFILE=%TMP_DIR%\maturin_build_output.txt"
set "INSTALL_DIR=%TMP_DIR%\install"

echo shutting down Blender...
taskkill /IM blender.exe /F >nul 2>&1

echo make temp directory
if exist %TMP_DIR% (
    echo Cleaning old temp directory...
    rmdir /S /Q %TMP_DIR%
)
mkdir %TMP_DIR%
if errorlevel 1 (
    echo ❌ Failed to create temp directory: %TMP_DIR%
    exit /b 1
)

echo 🔨 Building wheel with maturin...
maturin build --release > %OUTFILE% 2>&1
if errorlevel 1 (
    echo ❌ maturin build failed. see %OUTFILE%
    type %OUTFILE%
    exit /b 1
)

set "WHEEL_FILE="
for /f "usebackq delims=" %%i in (
    `powershell -NoProfile -Command ^
        "$text = Get-Content -Raw -Encoding UTF8 '%OUTFILE%';" ^
        "$clean = ($text -replace '[^\x20-\x7E]', '');" ^
        "$m = [regex]::Match($clean, 'Built wheel for CPython.*to (.+\.whl)');" ^
        "if ($m.Success) { $m.Groups[1].Value }"`
) do (
    set "WHEEL_FILE=%%i"
)

if not defined WHEEL_FILE (
    echo ❌ Could not find wheel file in maturin output. Dumping output:
    type "%OUTFILE%"
    exit /b 1
)
echo ✅ Found wheel: %WHEEL_FILE%

echo 📦 Installing to temp directory...
pip install %WHEEL_FILE% --target %INSTALL_DIR% --upgrade
if errorlevel 1 (
    echo ❌ pip install failed
    exit /b 1
)

echo 📁 Copying addon to Blender addons folder...
robocopy "%INSTALL_DIR%\blender_addon_core" "%ADDON_DIR%\blender_addon_core" /E /NFL /NDL /NJH /NJS /XO >nul
if errorlevel 8 (
    echo ❌ robocopy failed.
    exit /b 1
)

echo 🧹 Cleaning up...
if exist "%TMP_DIR%" rmdir /S /Q "%TMP_DIR%"

echo ✅ Done! Blender addon updated successfully.

endlocal