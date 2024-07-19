@echo off

REM Define source and destination directories
set SOURCE=Z:\E\OSCP-Toolchain
set DESTINATION=%USERPROFILE%\Desktop\OSCP-Toolchain

REM Create destination directory if it doesn't exist
if not exist "%DESTINATION%" (
    mkdir "%DESTINATION%"
)

REM Sync directories while excluding the .venv and .git directories
robocopy "%SOURCE%" "%DESTINATION%" /MIR /XD ".venv" ".git" ".idea"

REM Print completion message
echo Sync completed from %SOURCE% to %DESTINATION%

pause
