; 村务系统 Windows 客户安装程序脚本（Inno Setup 6）
; 用法：iscc "deploy\windows\村务系统_installer.iss"
; 输入：dist\ 目录下的 4 个文件；输出：installer\村务系统_安装程序.exe

#define MyAppName "村务系统"
#define MyAppVersion "1.0.0"
#define MyAppExeName "村务系统.exe"
#define MyAppDir "D:\村务系统"

[Setup]
AppId={{98978B43-7637-42FE-B8CC-96852D2BC3AC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=村务
DefaultDirName={#MyAppDir}
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=admin
; 固定安装目录 D:\村务系统（与备份.bat 及"数据跟随程序目录"模型保持一致）
OutputDir=..\..\installer
OutputBaseFilename=村务系统_安装程序_v1.0.1
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableWelcomePage=no
; 重装/升级时自动先关闭正在运行的村务系统，避免文件被占用导致替换失败
CloseApplications=yes
CloseApplicationsFilter=村务系统.exe
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
MinVersion=6.1sp1

; 中文界面通过下方 [Messages] 覆盖实现（内置 Default.isl 为英文底稿）

[Tasks]
Name: "autostart"; Description: "开机自动启动村务系统"; GroupDescription: "附加任务:"; Flags: unchecked

[Messages]
; 中文界面文案覆盖
SetupWindowTitle=村务系统 安装程序
WelcomeLabel1=欢迎使用村务系统安装程序
WelcomeLabel2=本程序将把村务系统安装到您的电脑。%n%n建议先关闭正在运行的其他程序，然后点击“下一步”继续。
ButtonNext=下一步(&N)
ButtonBack=上一步(&B)
ButtonInstall=安装(&I)
ButtonFinish=完成(&F)
ButtonCancel=取消
ButtonWizardBrowse=浏览(&B)...
ButtonYes=是(&Y)
ButtonNo=否(&N)
ClickNext=点击“下一步”继续安装，或点击“取消”退出安装程序。
ReadyLabel1=安装程序已准备好将村务系统安装到您的电脑。
ReadyLabel2a=点击“安装”开始安装。
ReadyLabel2b=点击“安装”开始安装。如果您需要查看或更改任何设置，请点击“上一步”。
ReadyMemoTasks=附加任务：
ReadyMemoDir=安装到：
ReadyMemoUserInfo=用户信息：
FinishedHeadingLabel=村务系统安装完成
FinishedLabel=村务系统已成功安装到您的电脑。
FinishedLabelNoIcons=村务系统已成功安装。
UninstallAppFullTitle=卸载 村务系统
UninstallAppTitle=卸载 村务系统

[Files]
Source: "..\..\dist\村务系统.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\dist\安装.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\dist\备份.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\dist\使用说明.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{commonstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: autostart

[Run]
Filename: "netsh.exe"; Parameters: "advfirewall firewall add rule name=""村务系统8080"" dir=in action=allow protocol=TCP localport=8080"; Flags: runhidden; StatusMsg: "正在放行 8080 端口..."
Filename: "{app}\{#MyAppExeName}"; Description: "立即启动村务系统"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "netsh.exe"; Parameters: "advfirewall firewall delete rule name=""村务系统8080"""; Flags: runhidden; RunOnceId: "DelFirewallRule"

[UninstallDelete]
; 保留 {app}\data 用户数据，卸载不删除数据
