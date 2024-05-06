@echo off
REM This script was copied from PythonQwt project
REM ======================================================
REM Package build script
REM ======================================================
REM Licensed under the terms of the MIT License
REM Copyright (c) 2020 Pierre Raybaut
REM (see PythonQwt LICENSE file for more details)
REM ======================================================
call %~dp0utils GetScriptPath SCRIPTPATH
call %FUNC% GetLibName LIBNAME
call %FUNC% GetModName MODNAME
call %FUNC% SetPythonPath
call %FUNC% UsePython
call %FUNC% GetVersion VERSION

set REPODIR=%SCRIPTPATH%\..

@REM Clone repository in a temporary directory
set CLONEDIR=%REPODIR%\..\%LIBNAME%-tempdir
if exist %CLONEDIR% ( rmdir /s /q %CLONEDIR% )
git clone -l -s . %CLONEDIR%

@REM Build distribution files
pushd %CLONEDIR%
%PYTHON% -m build
popd

@REM Copy distribution files to the repository
set DISTDIR=%REPODIR%\dist
if not exist %DISTDIR% ( mkdir %DISTDIR% )
copy /y %CLONEDIR%\dist\%MODNAME%-%VERSION%*.whl %DISTDIR%
copy /y %CLONEDIR%\dist\%MODNAME%-%VERSION%*.tar.gz %DISTDIR%

@REM Clean up
rmdir /s /q %CLONEDIR%
call %FUNC% EndOfScript