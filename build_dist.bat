del MANIFEST
rmdir /S /Q build
rmdir /S /Q dist
python setup.py sdist bdist_wheel
python setup.py build sdist