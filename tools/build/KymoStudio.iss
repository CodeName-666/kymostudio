; SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
; Copyright (c) 2026 Christof Seidel
;
; KymoStudio Inno Setup installer script.
; Expects the PyInstaller onedir build in build/dist/KymoStudio/.
;
;     bash tools/build/build-installer.sh
; or  ISCC.exe /DAppVersion=1.2.3 tools\build\KymoStudio.iss

#define AppName "KymoStudio"
; Version comes from python/Core/version.py via /DAppVersion=...
; A local build without a version must not look like a release.
#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif
#define AppPublisher "Christof Seidel"
#define AppURL "https://github.com/CodeName-666/kymostudio"
#define ExeName "KymoStudio.exe"
; Paths are relative to this file (tools/build/).
#define SourceRoot "..\..\build\dist\KymoStudio"
#define OutputDirectory "..\..\build\installer"
#define LicensePath "..\..\LICENSE"
#define IconPath "..\..\resources\icons\kymotrace.ico"

[Setup]
; AppId must never change, otherwise Windows treats updates as a different product.
AppId={{15E8B55A-0CBC-4898-9427-F59B3662E325}}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\Kymotrace\{#AppName}
DefaultGroupName=Kymotrace
DisableProgramGroupPage=yes
LicenseFile={#LicensePath}
OutputDir={#OutputDirectory}
OutputBaseFilename={#AppName}_{#AppVersion}_Setup
SetupIconFile={#IconPath}
UninstallDisplayIcon={app}\{#ExeName}
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern

; --- Code signing (enable later) ---
; SignTool=signtool
; SignedUninstaller=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
; Remove the previous runtime before copying: [Files] never deletes orphaned
; modules or DLLs from older builds.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "{#SourceRoot}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#ExeName}"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
