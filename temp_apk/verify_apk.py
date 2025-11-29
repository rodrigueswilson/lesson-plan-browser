import zipfile
with zipfile.ZipFile('temp_apk/installed-base.apk') as z:
    for name in z.namelist():
        if 'index-' in name and name.endswith('.js'):
            print(name)
