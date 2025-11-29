import zipfile
with zipfile.ZipFile('temp_apk/installed-base.apk') as z:
    for name in z.namelist():
        print(name)
