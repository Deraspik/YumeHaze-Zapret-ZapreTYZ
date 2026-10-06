; Inno Setup 6 — установщик ZapreTYZ (интерфейс + Zapret + TG WS Proxy)
#define AppName "Yume Haze Zapret"
#define AppVersion "1.0.2"
#define AppExe "ZapreTYZ.exe"

[Setup]
AppId={{7C1B7E2A-5A1D-4E7B-9C1E-7A2B3C4D5E6F}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Yume Haze (Zapret by Flowseal)
DefaultDirName={autopf}\YumeHazeZapret
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir=..\release
OutputBaseFilename=YumeHazeZapret_Setup_{#AppVersion}
SetupIconFile=..\assets\setup.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/ultra64
LZMAUseSeparateProcess=yes
LZMADictionarySize=65536
SolidCompression=yes
WizardStyle=modern
CloseApplications=force

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart"; Description: "Запускать Yume Haze Zapret вместе с Windows"; Flags: unchecked

[Files]
Source: "..\dist\ZapreTYZ\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; компоненты: пользовательские списки не перезаписываем при переустановке
Source: "..\components\zapret\*"; DestDir: "{app}\components\zapret"; Excludes: "*-user.txt,game_filter.enabled"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\components\tgproxy\*"; DestDir: "{app}\components\tgproxy"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Удалить {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "schtasks"; Parameters: "/Create /F /TN ""ZapreTYZ Autostart"" /SC ONLOGON /RL HIGHEST /DELAY 0000:10 /TR """"""{app}\{#AppExe}"""" --minimized"""; Flags: runhidden; Tasks: autostart
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent shellexec

[UninstallRun]
Filename: "taskkill"; Parameters: "/F /IM ZapreTYZ.exe"; Flags: runhidden; RunOnceId: "killapp"
Filename: "taskkill"; Parameters: "/F /IM winws.exe"; Flags: runhidden; RunOnceId: "killwinws"
Filename: "schtasks"; Parameters: "/Delete /F /TN ""ZapreTYZ Autostart"""; Flags: runhidden; RunOnceId: "deltask"
Filename: "sc"; Parameters: "stop WinDivert"; Flags: runhidden; RunOnceId: "stopwd"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\components"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var R: Integer;
begin
  if CurStep = ssInstall then begin
    Exec('taskkill', '/F /IM ZapreTYZ.exe', '', SW_HIDE, ewWaitUntilTerminated, R);
    Exec('taskkill', '/F /IM winws.exe', '', SW_HIDE, ewWaitUntilTerminated, R);
  end;
end;
