; Tally Sync Agent - Inno Setup Script
; Produces: TallySyncAgent-Setup-{version}.exe
;
; Prerequisites:
;   1. pyinstaller TallySyncAgent.spec --clean --noconfirm
;   2. pyinstaller TallySyncService.spec --clean --noconfirm
;   3. pyinstaller RegistrationWizard.spec --clean --noconfirm
;   4. "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\TallySyncAgent.iss

#define AppName    "Tally Sync Agent"
#define AppVersion "0.5.0"
#define AppPublisher "Tally Sync Platform"
#define AppURL      "https://tallysync.io"
#define AppExeName  "TallySyncAgent.exe"
#define ServiceExe  "TallySyncService.exe"
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
Name: "installservice"; Description: "Install as Windows service (starts automatically with Windows)"; GroupDescription: "Service options:"; Flags: checkedonce
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional options:"

[Files]
; Main agent (console-less, for manual runs and tray icon)
Source: "..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Service exe (console, for SCM integration)
Source: "..\dist\{#ServiceExe}"; DestDir: "{app}"; Flags: ignoreversion
; Registration wizard
Source: "..\dist\{#WizardExe}"; DestDir: "{app}"; Flags: ignoreversion
; Service management script
Source: ".\service\install_service.ps1"; DestDir: "{app}\tools"; Flags: ignoreversion
; Tally API Connector (bundled)
Source: "D:\Downloads\integration-setup-lite\integration-setup-lite\TallyAPIConnectorV2.0.exe"; DestDir: "{app}\connector"; Flags: ignoreversion
; Config template
Source: ".\config\agent.env.example"; DestDir: "{app}\config"; DestName: "agent.env"; Flags: onlyifdoesntexist

[Dirs]
Name: "{app}\logs"; Permissions: everyone-modify

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Registration Wizard"; Filename: "{app}\{#WizardExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Run registration wizard after install
Filename: "{app}\{#WizardExe}"; Description: "Register this device with the Tally Sync platform"; Flags: nowait postinstall skipifsilent

; Install as Windows service (if task selected)
Filename: "{app}\{#ServiceExe}"; Parameters: "--startup auto install"; StatusMsg: "Installing Windows service..."; Flags: runhidden waituntilterminated; Tasks: installservice
Filename: "{app}\{#ServiceExe}"; Parameters: "start"; StatusMsg: "Starting Tally Sync Agent service..."; Flags: runhidden waituntilterminated; Tasks: installservice

[UninstallRun]
; Stop and remove the service on uninstall
Filename: "{app}\{#ServiceExe}"; Parameters: "stop"; Flags: runhidden waituntilterminated; RunOnceId: "StopService"
Filename: "{app}\{#ServiceExe}"; Parameters: "remove"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveService"
; Clean up credentials from Windows Credential Manager
Filename: "{sys}\cmdkey.exe"; Parameters: "/delete:TallySyncAgent"; Flags: runhidden waituntilterminated; RunOnceId: "DeleteCreds"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\*.db"

[Code]

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

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then begin
    if MsgBox(
      'Do you want to delete all Tally Sync Agent log files?' + #13#10 +
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
