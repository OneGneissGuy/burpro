@echo off
@echo Starting BurPro...
@echo.

cd /d "%~dp0"
python ..\burpro.py "%*"

@echo.
@echo Press any key to close...
@echo off
pause > nul
exit /b

