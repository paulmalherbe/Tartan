; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "Tartan"
#define MyAppVersion "6"
#define MyAppPublisher "Tartan Systems"
#define MyAppURL "http://www.tartan.co.za"
#define MyAppExeName "ms0000.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppCopyright=Paul Malherbe
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DisableDirPage=no
DefaultDirName={sd}\{#MyAppName}\prg
DisableProgramGroupPage=yes
DefaultGroupName={#MyAppName}
OutputBaseFilename={#MyAppName}
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; NOTE: Don't use "Flags: ignoreversion" on any shared system files
Source: "C:\Tartan\prg\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Code]
var
  ResultCode: Integer;

procedure DoPreInstall();
begin
  if FileExists(ExpandConstant('{app}\unins002.exe')) then begin
    Exec(ExpandConstant('{app}\unins002.exe'), '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end else if FileExists(ExpandConstant('{app}\unins001.exe')) then begin
    Exec(ExpandConstant('{app}\unins001.exe'), '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end else if FileExists(ExpandConstant('{app}\unins000.exe')) then begin
    Exec(ExpandConstant('{app}\unins000.exe'), '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;

procedure DoPostInstall();
begin
  if FileExists(ExpandConstant('{app}\ms0000.exe.log')) then begin
    DeleteFile(ExpandConstant('{app}\ms0000.exe.log'));
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then begin
    DoPreInstall();
  end else if CurStep = ssPostInstall then begin
    DoPostInstall();
  end;
end;

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFileName: "{sd}\{#MyAppName}\prg\tartan.ico"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFileName: "{sd}\{#MyAppName}\prg\tartan.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, "&", "&&")}}"; Flags: nowait postinstall skipifsilent
