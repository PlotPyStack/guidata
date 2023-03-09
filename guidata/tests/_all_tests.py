# -*- coding: utf-8 -*-

"""
Run all tests in unattended mode
"""

import argparse
import os
import os.path as osp

import guidata
from guidata import __version__
from guidata.guitest import get_tests

TST_PATH = []  # type: ignore


def run_all_tests(args="", contains="", timeout=None):
    """Run all guidata tests"""
    testmodules = [
        tmod
        for tmod in get_tests(guidata)
        if not osp.samefile(tmod.path, __file__) and contains in tmod.path
    ]
    tnb = len(testmodules)
    print("*** guidata automatic unit tests ***")
    print("")
    print("Test parameters:")
    print(f"  Selected {tnb} tests ({len(get_tests(guidata)) - 1} total available)")
    print("  Test data path:")
    for path in TST_PATH:
        print(f"    {path}")
    print("  Environment:")
    for vname in ("DATA_GUIDATA", "PYTHONPATH", "DEBUG"):
        print(f"    {vname}={os.environ.get(vname, '')}")
    print("")
    print("Please wait while test scripts are executed (a few minutes).")
    print("Only error messages will be printed out (no message = test OK).")
    print("")
    for idx, testmodule in enumerate(testmodules):
        rpath = osp.relpath(testmodule.path, osp.dirname(guidata.__file__))
        print(f"===[{(idx+1):02d}/{tnb:02d}]=== 🍺 Running test [{rpath}]")
        testmodule.run(args=args, timeout=timeout)


def run():
    """Parse arguments and run tests"""
    parser = argparse.ArgumentParser(description="Run all test in unattended mode")
    parser.add_argument("--contains", default="")
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()
    run_all_tests("--mode unattended --verbose quiet", args.contains, args.timeout)


if __name__ == "__main__":
    run()
