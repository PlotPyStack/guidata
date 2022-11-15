sphinx-build -b htmlhelp doc doctmp
"C:\Program Files\HTML Help Workshop\hhc.exe" doctmp\guidata.hhp
"C:\Program Files (x86)\HTML Help Workshop\hhc.exe" doctmp\guidata.hhp
copy doctmp\guidata.chm .
"C:\Program Files\7-Zip\7z.exe" a guidata.chm.zip guidata.chm
del doctmp\guidata.chm
del doc.zip
sphinx-build -b html doc doctmp
cd doctmp
"C:\Program Files\7-Zip\7z.exe" a -r ..\doc.zip *.*
cd ..
rmdir /S /Q doctmp
del guidata.chm.zip