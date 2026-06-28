; Tally Sync Agent - Inno Setup Script
; Produces: TallySyncAgent-Setup-{version}.exe
;
; Prerequisites:
;   1. pyinstaller TallySyncAgent.spec --clean   (builds dist\TallySyncAgent.exe + dist\registration_wizard.exe)
;   2. Download nssm.exe from https://nssm.cc/download -> installer\vendor\nssm.exe
;   3. iscc installer\TallySyncAgent.iss

#define AppName    "Tally Sync Agent"
#define AppVersion "0.4.0"
#define AppPublisher "Tally Sync Platform"
#define AppURL      "http://15.206.90.21:8000"
#define AppExeName  "TallySyncAgent.exe"
#define ServiceName "TallySyncAgent"
#define WizardExe   "registration_wizard.exe"

[Setup]
AppId={{8C4F3A2B-1D6E-4A7F-B9C2-3E5F8D1A6B4C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
PrivilegesRequired=admin
OutputDir=dist\installer
OutputBaseFilename=TallySyncAgent-Setup-{#AppVersion}
; SetupIconFile=installer\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExeName}
VersionInfoVersion={#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "autostart"; Description: "Start Tally Sync Agent automatically with Windows"; GroupDescription: "Additional options:"

[Files]
Source: "..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\{#WizardExe}"; DestDir: "{app}"; Flags: ignoreversion
; Source: ".\vendor\nssm.exe"; DestDir: "{app}\vendor"; Flags: ignoreversion
; ^ uncomment after downloading nssm.exe from https://nssm.cc/download
Source: ".\config\agent.env.example"; DestDir: "{app}\config"; DestName: "agent.env"; Flags: onlyifdoesntexist

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Registration Wizard"; Filename: "{app}\{#WizardExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: autostart

[Run]
Filename: "{app}\{#WizardExe}"; Description: "Register this device with the Tally Sync platform"; Parameters: "/wizard"; Flags: nowait postinstall skipifsilent
Filename: "{app}\vendor\nssm.exe"; Parameters: "install ""{#ServiceName}"" ""{app}\{#AppExeName}"""; Flags: runhidden waituntilterminated; Check: NssmExists
Filename: "{app}\vendor\nssm.exe"; Parameters: "set ""{#ServiceName}"" AppDirectory ""{app}"""; Flags: runhidden waituntilterminated; Check: NssmExists
Filename: "{app}\vendor\nssm.exe"; Parameters: "set ""{#ServiceName}"" AppStdout ""{app}\logs\service.log"""; Flags: runhidden waituntilterminated; Check: NssmExists
Filename: "{app}\vendor\nssm.exe"; Parameters: "set ""{#ServiceName}"" AppStderr ""{app}\logs\service-error.log"""; Flags: runhidden waituntilterminated; Check: NssmExists
Filename: "{app}\vendor\nssm.exe"; Parameters: "set ""{#ServiceName}"" Start SERVICE_AUTO_START"; Flags: runhidden waituntilterminated; Check: NssmExists
Filename: "{app}\vendor\nssm.exe"; Parameters: "start ""{#ServiceName}"""; StatusMsg: "Starting Tally Sync Agent service..."; Flags: runhidden waituntilterminated; Check: NssmExists

[UninstallRun]
Filename: "{app}\vendor\nssm.exe"; Parameters: "stop ""{#ServiceName}"""; Flags: runhidden waituntilterminated; RunOnceId: "StopService"; Check: NssmExists
Filename: "{app}\vendor\nssm.exe"; Parameters: "remove ""{#ServiceName}"" confirm"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveService"; Check: NssmExists
Filename: "{sys}\schtasks.exe"; Parameters: "/delete /tn ""TallySyncAgent_Restart"" /f"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveOTATask"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\.update.lock"
Type: files; Name: "{app}\*.backup.exe"
Type: files; Name: "{app}\*.new.exe"

[Code]

function NssmExists(): Boolean;
begin
  Result := FileExists(ExpandConstant('{app}\vendor\nssm.exe'));
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if not (GetWindowsVersion >= $0A000000) then begin
    MsgBox(
      'Tally Sync Agent requires Windows 10 or later.' + #13#10 +
      'Please upgrade your OS before installing.',
      mbError, MB_OK
    );
    Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  LogDir: String;
begin
  if CurStep = ssPostInstall then begin
    LogDir := ExpandConstant('{app}\logs');
    if not DirExists(LogDir) then
      CreateDir(LogDir);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then begin
    Exec(ExpandConstant('{sys}\cmdkey.exe'), '/delete:TallySyncAgent',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

    if MsgBox(
      'Do you want to delete all Tally Sync log files?' + #13#10 +
      '(Stored in ' + ExpandConstant('{app}\logs') + ')',
      mbConfirmation, MB_YESNO
    ) = IDNO then begin
      CreateDir(ExpandConstant('{userdocs}\TallySyncAgent'));
      Exec(ExpandConstant('{sys}\robocopy.exe'),
           ExpandConstant('"{app}\logs" "{userdocs}\TallySyncAgent\logs" /MOVE /E /NFL /NDL'),
           '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
