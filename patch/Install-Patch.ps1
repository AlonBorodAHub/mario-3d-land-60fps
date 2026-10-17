param(
    [ValidateSet('Install','Check','Uninstall')][string]$Mode = 'Install',
    [string]$RomPath,
    [string]$AzaharUserDirectory
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try {
    . (Join-Path $PSScriptRoot 'Patch-Tools.ps1')
    $manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
    [byte[]]$patch = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'code.ips'))
    if ((Get-ByteHash $patch) -ne $manifest.patch_sha256) { throw 'Package patch checksum failed. Extract the ZIP again.' }
    if ($Mode -ne 'Uninstall') {
        if (-not $RomPath) { $RomPath = (Read-Host 'Path to your USA Rev 1 .3ds file OR its folder').Trim().Trim('"') }
        [byte[]]$header = Get-GameHeader $RomPath $manifest
        if ($Mode -eq 'Check') { Write-Host 'ROM, patch and generated header verified. No files installed.'; exit 0 }
    }
    if (@(Get-Process -Name azahar -ErrorAction SilentlyContinue).Count -gt 0) { throw 'Close Azahar before installing or uninstalling.' }
    if (-not $AzaharUserDirectory) {
        Write-Host 'Enter the Azahar USER directory containing config, load and sdmc (portable installs usually use a folder named user).'
        $AzaharUserDirectory = (Read-Host 'Azahar user directory').Trim().Trim('"')
    }
    if ($Mode -eq 'Uninstall') { Uninstall-PatchFiles $AzaharUserDirectory $manifest }
    else { Install-PatchFiles $AzaharUserDirectory $patch $header $manifest }
    exit 0
} catch { Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red; exit 1 }
