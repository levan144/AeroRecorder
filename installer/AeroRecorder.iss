#define MyAppName "AeroRecorder"
#ifndef MyAppVersion
  #error MyAppVersion was not supplied. Run ISCC with /DMyAppVersion=x.y.z
#endif
#define MyAppPublisher "AeroRecorder"
#define MyAppExeName "AeroRecorder.exe"

[Setup]
AppId={{9E453BAB-F930-4A35-9C93-4C115AB8A9E2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=AeroRecorder-Setup-{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName}
; "force" rather than "yes": AeroRecorder runs a windowless audio-meter helper
; from the same executable. Restart Manager can only close processes that own
; a window, so with "yes" that helper blocks the install and Setup reports
; that it could not close all applications. Setup still lists what it will
; close on the Preparing page, so nothing happens without the user seeing it.
CloseApplications=force
RestartApplications=no
; Only ever run one Setup at a time.
SetupMutex=AeroRecorderSetup-b7f3a1c94e2d
SetupIconFile=..\assets\AeroRecorder.ico
LicenseFile=..\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\AeroRecorder\*"; DestDir: "{app}"; Excludes: "portable.flag,data\*"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
