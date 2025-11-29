@echo off
echo ========================================
echo Android App Installation Diagnostic
echo ========================================
echo.

echo Step 1: Checking device connection...
adb devices
echo.

echo Step 2: Checking tablet architecture...
adb shell getprop ro.product.cpu.abi
echo.

echo Step 3: Checking if app is already installed...
adb shell pm list packages | findstr /i "lesson bilingual"
echo.

echo Step 4: Checking APK file...
if exist "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk" (
    echo APK file EXISTS
    dir "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"
) else (
    echo ERROR: APK file NOT FOUND!
)
echo.

echo Step 5: Attempting installation...
adb uninstall com.lessonplanner.bilingual
adb install -r -d "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"
echo.

echo Step 6: Verifying installation...
adb shell pm list packages | findstr /i "lesson bilingual"
echo.

echo Step 7: Attempting to launch app...
adb shell am start -n com.lessonplanner.bilingual/.MainActivity
echo.

echo ========================================
echo Diagnostic complete!
echo Check the output above for any errors.
echo ========================================
pause

