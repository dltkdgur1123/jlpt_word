@echo off
setlocal

set "PROJECT_DIR=D:\backup\jlpt_word"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"

if not exist "%PROJECT_DIR%\streamlit_app.py" (
    echo [ERROR] streamlit_app.py was not found:
    echo %PROJECT_DIR%\streamlit_app.py
    pause
    exit /b 1
)

if not exist "%PROJECT_DIR%\venv\Scripts\pythonw.exe" (
    echo [ERROR] pythonw.exe was not found:
    echo %PROJECT_DIR%\venv\Scripts\pythonw.exe
    pause
    exit /b 1
)

copy /Y "%~dp0streamlit_background.pyw" "%PROJECT_DIR%\streamlit_background.pyw" >nul
if errorlevel 1 goto :copy_error

rem Remove the old startup launchers that can create the tray icon.
if exist "%STARTUP_DIR%\run_streamlit_app.bat" del /Q "%STARTUP_DIR%\run_streamlit_app.bat"
if exist "%STARTUP_DIR%\run_streamlit_app_hidden.vbs" del /Q "%STARTUP_DIR%\run_streamlit_app_hidden.vbs"

copy /Y "%~dp0start_streamlit_hidden.vbs" "%STARTUP_DIR%\start_streamlit_hidden.vbs" >nul
if errorlevel 1 goto :copy_error

copy /Y "%~dp0stop_streamlit_force.vbs" "%DESKTOP_DIR%\stop_streamlit_force.vbs" >nul
if errorlevel 1 goto :copy_error

echo.
echo Installation completed.
echo.
echo Startup launcher:
echo %STARTUP_DIR%\start_streamlit_hidden.vbs
echo.
echo Force-stop launcher:
echo %DESKTOP_DIR%\stop_streamlit_force.vbs
echo.
echo Restart Windows or double-click the startup launcher to test.
pause
exit /b 0

:copy_error
echo.
echo [ERROR] A file could not be copied.
pause
exit /b 1
