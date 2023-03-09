# -*- coding: utf-8 -*-


def pytest_addoption(parser):
    parser.addoption("--mode", action="store", default="unattended")
