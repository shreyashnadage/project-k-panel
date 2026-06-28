; Tally Sync Agent — Inno Setup Script
; Produces: TallySyncAgent-Setup-{version}.exe
;
; Prerequisites before compiling:
;   1. Install Inno Setup 6: https://jrsoftware.org/isdl.php
;   2. Build PyInstaller bundle: make build-agent
;   3. Optional: signtool.exe in PATH for code signing
;
; Compile:
;   iscc installer\TallySyncAgent.iss

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
; Require admin so we can install a Windows service
PrivilegesRequired=admin
OutputDir=dist\installer
OutputBaseFilename=TallySyncAgent-Setup-{#AppVersion}
SetupIconFile=installer\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Code-sign the installer output (requires signtool + EV cert)
; SignTool=signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a $f
UninstallDisplayIcon={app}\{#AppExeName}
; Show a license (optional)
; LicenseFile=LICENSE.txt
; Don't allow downgrade installs
VersionInfoVersion={#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "autostart"; Description: "Start Tally Sync Agent automatically with Windows"; \
  GroupDescription: "Additional options:"; Flags: checked

[Files]
; Main agent executable (built by PyInstaller)
Source: "..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Registration wizard executable (built by PyInstaller)
Source: "..\dist\{#WizardExe}"; DestDir: "{app}"; Flags: ignoreversion

; NSSM (Non-Sucking Service Manager) bundled for service install
Source: ".\vendor\nssm.exe"; DestDir: "{app}\vendor"; Flags: ignoreversion

; Default config (user-editable, does NOT overwrite on upgrade)
Source: ".\config\agent.env.example"; DestDir: "{app}\config"; \
  DestName: "agent.env"; Flags: onlyifdoesntexist

; Icon
Source: ".\assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Registration Wizard"; Filename: "{app}\{#WizardExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; \
  Tasks: autostart

[Run]
; Step 1: Launch registration wizard so user can enter their installation key.
; /wizard flag tells it to run in installer context (no "Back" button shown).
Filename: "{app}\{#WizardExe}"; \
  Description: "Register this device with the Tally Sync platform"; \
  Flags: nowait postinstall skipifsilent; \
  Parameters: "/wizard"

; Step 2: Install Windows Service via NSSM (runs silently)
Filename: "{app}\vendor\nssm.exe"; \
  Parameters: "install ""{#ServiceName}"" ""{app}\{#AppExeName}"""; \
  Flags: runhidden waituntilterminated

; Step 3: Configure service environment (reads agent.env)
Filename: "{app}\vendor\nssm.exe"; \
  Parameters: "set ""{#ServiceName}"" AppParameters """"""; \
  Flags: runhidden waituntilterminated

Filename: "{app}\vendor\nssm.exe"; \
  Parameters: "set ""{#ServiceName}"" AppDirectory ""{app}"""; \
  Flags: runhidden waituntilterminated

Filename: "{app}\vendor\nssm.exe"; \
  Parameters: "set ""{#ServiceName}"" AppStdout ""{app}\logs\service.log"""; \
  Flags: runhidden waituntilterminated

Filename: "{app}\vendor\nssm.exe"; \
  Parameters: "set ""{#ServiceName}"" AppStderr ""{app}\logs\service-error.log"""; \
  Flags: runhidden waituntilterminated

Filename: "{app}\vendor\nssm.exe"; \
  Parameters: "set ""{#ServiceName}"" Start SERVICE_AUTO_START"; \
  Flags: runhidden waituntilterminated

; Step 4: Start the service
Filename: "{app}\vendor\nssm.exe"; \
  Parameters: "start ""{#ServiceName}"""; \
  Flags: runhidden waituntilterminated; \
  StatusMsg: "Starting Tally Sync Agent service..."

[UninstallRun]
; Step 1: Stop the Windows service
Filename: "{app}\vendor\nssm.exe"; \
  Parameters: "stop ""{#ServiceName}"""; \
  Flags: runhidden waituntilterminated; RunOnceId: "StopService"

; Step 2: Remove the Windows service registration
Filename: "{app}\vendor\nssm.exe"; \
  Parameters: "remove ""{#ServiceName}"" confirm"; \
  Flags: runhidden waituntilterminated; RunOnceId: "RemoveService"

; Step 3: Remove OTA scheduled task (created by updater on restart)
Filename: "{sys}\schtasks.exe"; \
  Parameters: "/delete /tn ""TallySyncAgent_Restart"" /f"; \
  Flags: runhidden waituntilterminated; RunOnceId: "RemoveOTATask"

; Step 4: Remove credentials from Windows Credential Manager
Filename: "{app}\vendor\nssm.exe"; \
  Description: "Removing stored credentials..."; \
  Parameters: ""; \
  Flags: runhidden waituntilterminated; RunOnceId: "RemoveCredentials"

[UninstallDelete]
; Delete log files (Inno Setup won't remove dirs containing unlisted files)
Type: filesandordirs; Name: "{app}\logs"
; Delete any leftover OTA download temp files
Type: filesandordirs; Name: "{app}\.update.lock"
Type: files;          Name: "{app}\*.backup.exe"
Type: files;          Name: "{app}\*.new.exe"

[Code]
{ -----------------------------------------------------------------------
  Pascal script: runs before install to check prerequisites
  ----------------------------------------------------------------------- }

function InitializeSetup(): Boolean;
begin
  Result := True;

  { Check Windows 10 or later (version 10.0) }
  if not (GetWindowsVersion >= $0A000000) then begin
    MsgBox(
      'Tally Sync Agent requires Windows 10 or later.' + #13#10 +
      'Please upgrade your OS before installing.',
      mbError, MB_OK
    );
    Result := False;
    Exit;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  LogDir: String;
begin
  if CurStep = ssPostInstall then begin
    { Create logs directory so the service can write to it immediately }
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
    { Remove credentials from Windows Credential Manager via cmdkey }
    Exec(ExpandConstant('{sys}\cmdkey.exe'),
         '/delete:TallySyncAgent',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

    { Ask user whether to keep or delete their sync logs }
    if MsgBox(
      'Do you want to delete all Tally Sync log files?' + #13#10 +
      '(Stored in ' + ExpandConstant('{app}\logs') + ')',
      mbConfirmation, MB_YESNO
    ) = IDNO then begin
      { User chose to keep logs — remove the [UninstallDelete] entry by
        moving logs out of the app dir into the user''s Documents }
      CreateDir(ExpandConstant('{userdocs}\TallySyncAgent'));
      Exec(ExpandConstant('{sys}\robocopy.exe'),
           ExpandConstant('"{app}\logs" "{userdocs}\TallySyncAgent\logs" /MOVE /E /NFL /NDL'),
           '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
