@echo off
chcp 65001 >nul
set STAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set STAMP=%STAMP: =0%
set DST=D:\村务系统\backup\%STAMP%
if not exist "%DST%" mkdir "%DST%"
xcopy /E /I /Y "D:\村务系统\data" "%DST%" >nul
echo 备份完成：%DST%
pause
