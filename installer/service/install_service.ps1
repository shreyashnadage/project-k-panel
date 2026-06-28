# Tally Sync Agent — Windows Service installer
# Uses sc.exe (built-in) to register the agent as a Windows service.
# Must be run as Administrator.
#
# Usage:
#   .\install_service.ps1 -Action install   # Register + start
#   .\install_service.ps1 -Action uninstall # Stop + remove
#   .\install_service.ps1 -Action status    # Show service state

param(
    [ValidateSet("install", "uninstall", "status", "start", "stop", "restart")]
    [string]$Action = "status"
)

$ServiceName = "TallySyncAgent"
$DisplayName = "Tally Sync Agent"
$Description = "Extracts accounting data from TallyPrime and syncs to cloud platform"
$ExePath = Join-Path $PSScriptRoot "..\dist\TallySyncAgent.exe"

# Resolve to absolute path
if (Test-Path $ExePath) {
    $ExePath = (Resolve-Path $ExePath).Path
} else {
    # Try alongside installer
    $ExePath = Join-Path $PSScriptRoot "TallySyncAgent.exe"
    if (-not (Test-Path $ExePath)) {
        Write-Host "ERROR: TallySyncAgent.exe not found" -ForegroundColor Red
        exit 1
    }
    $ExePath = (Resolve-Path $ExePath).Path
}

$LogDir = Join-Path (Split-Path $ExePath) "logs"

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-ServiceStatus {
    $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($svc) {
        Write-Host "Service: $DisplayName" -ForegroundColor Cyan
        Write-Host "  Status:  $($svc.Status)"
        Write-Host "  Startup: $($svc.StartType)"
        Write-Host "  Path:    $ExePath"
    } else {
        Write-Host "Service '$ServiceName' is not installed" -ForegroundColor Yellow
    }
}

function Install-AgentService {
    if (-not (Test-Administrator)) {
        Write-Host "ERROR: Run as Administrator to install the service" -ForegroundColor Red
        exit 1
    }

    $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "Service already installed (status: $($existing.Status))" -ForegroundColor Yellow
        Write-Host "Run with -Action uninstall first to re-install"
        return
    }

    # Create logs directory
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }

    # Create the service
    Write-Host "Installing service..." -ForegroundColor Cyan
    $binPath = "`"$ExePath`""
    sc.exe create $ServiceName binPath= $binPath start= auto DisplayName= "$DisplayName"
    sc.exe description $ServiceName "$Description"
    sc.exe failure $ServiceName reset= 86400 actions= restart/5000/restart/10000/restart/30000

    Write-Host "Service installed successfully" -ForegroundColor Green

    # Start it
    Write-Host "Starting service..." -ForegroundColor Cyan
    sc.exe start $ServiceName
    Start-Sleep -Seconds 2

    Get-ServiceStatus
}

function Uninstall-AgentService {
    if (-not (Test-Administrator)) {
        Write-Host "ERROR: Run as Administrator to uninstall the service" -ForegroundColor Red
        exit 1
    }

    $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $existing) {
        Write-Host "Service is not installed" -ForegroundColor Yellow
        return
    }

    if ($existing.Status -eq "Running") {
        Write-Host "Stopping service..." -ForegroundColor Cyan
        sc.exe stop $ServiceName
        Start-Sleep -Seconds 3
    }

    Write-Host "Removing service..." -ForegroundColor Cyan
    sc.exe delete $ServiceName

    Write-Host "Service removed" -ForegroundColor Green
}

function Start-AgentService {
    if (-not (Test-Administrator)) {
        Write-Host "ERROR: Run as Administrator" -ForegroundColor Red; exit 1
    }
    sc.exe start $ServiceName
    Start-Sleep -Seconds 2
    Get-ServiceStatus
}

function Stop-AgentService {
    if (-not (Test-Administrator)) {
        Write-Host "ERROR: Run as Administrator" -ForegroundColor Red; exit 1
    }
    sc.exe stop $ServiceName
    Start-Sleep -Seconds 2
    Get-ServiceStatus
}

function Restart-AgentService {
    Stop-AgentService
    Start-Sleep -Seconds 1
    Start-AgentService
}

switch ($Action) {
    "install"   { Install-AgentService }
    "uninstall" { Uninstall-AgentService }
    "status"    { Get-ServiceStatus }
    "start"     { Start-AgentService }
    "stop"      { Stop-AgentService }
    "restart"   { Restart-AgentService }
}
