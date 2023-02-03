@echo off
REM This script was derived from PythonQwt project
REM ======================================================
REM Test launcher script
REM ======================================================
REM Licensed under the terms of the MIT License
REM Copyright (c) 2020 Pierre Raybaut
REM (see PythonQwt LICENSE file for more details)
REM ======================================================
setlocal
call %~dp0utils GetScriptPath SCRIPTPATH
cd %SCRIPTPATH%\..
%PYTHON% -m pip install --upgrade -r dev\requirements.txt
%PYTHON% -m pip list > dev\pip_list.txt
call %FUNC% EndOfScript