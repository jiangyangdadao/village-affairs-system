@echo off
chcp 65001 >nul
set DEST=D:\村务系统
if not exist "%DEST%" mkdir "%DEST%"
xcopy /E /Y /I "%~dp0*" "%DEST%" >nul
powershell -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\村务系统.lnk');$s.TargetPath='%DEST%\村务系统.exe';$s.WorkingDirectory='%DEST%';$s.Save()"
copy "%USERPROFILE%\Desktop\村务系统.lnk" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\" >nul
netsh advfirewall firewall add rule name="村务系统8080" dir=in action=allow protocol=TCP localport=8080 >nul 2>&1
start "" "%DEST%\村务系统.exe"
echo.
echo 安装完成！稍等几秒后在浏览器打开 http://127.0.0.1:8080
echo 手机连村WiFi，打开电脑上「使用海报.pdf」所示地址即可使用。
pause
