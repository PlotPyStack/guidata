sphinx-build -b htmlhelp doc doctmp
"C:\Program Files\HTML Help Workshop\hhc.exe" doctmp\guidatadoc.hhp
"C:\Program Files (x86)\HTML Help Workshop\hhc.exe" doctmp\guidatadoc.hhp
copy doctmp\guidatadoc.chm .
rmdir /S /Q doctmp
pause