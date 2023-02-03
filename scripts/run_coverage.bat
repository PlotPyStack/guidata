@echo off
REM This script was derived from PythonQwt project
REM ======================================================
REM Test launcher script
REM ======================================================
REM Licensed under the terms of the MIT License
REM Copyright (c) 2020 Pierre Raybaut
REM (see PythonQwt LICENSE file for more details)
REM ======================================================
echo %CD%
echo import coverage; coverage.process_startup() > .venv\3.10\Lib\site-packages\temp.pth
%PYTHON% -m coverage run --concurrency=multiprocessing -m %MODULE%
%PYTHON% -m coverage combine
%PYTHON% -m coverage xml --data-file=.coverage
%PYTHON% -m coverage html
start .\htmlcov\index.html

del .venv\3.10\Lib\site-packages\temp.pth