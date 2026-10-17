Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Get-ByteHash([byte[]]$Data) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($algorithm.ComputeHash($Data))).Replace('-','').ToLowerInvariant() }
    finally { $algorithm.Dispose() }
}
function Get-PathHash([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $algorithm.Dispose(); $stream.Dispose() }
}
function Get-GameHeader([string]$RomPath, $Manifest) {
    $RomPath = $RomPath.Trim().Trim('"')
    if (-not $RomPath -or -not (Test-Path -LiteralPath $RomPath)) { throw 'ROM path not found. Choose the .3ds file or the folder containing it.' }
    $rom = Get-Item -LiteralPath $RomPath
    $romHash = $null
    if ($rom -is [IO.DirectoryInfo]) {
        Write-Host 'Folder selected. Looking for the matching USA Rev 1 .3ds file...'
        $candidates = @(Get-ChildItem -LiteralPath $rom.FullName -File -Filter '*.3ds' | Where-Object { $_.Length -eq $Manifest.rom_bytes } | Sort-Object @{Expression = { $_.Name -like '*Mario*3D*Land*' }; Descending = $true},Name)
        $match = $null
        foreach ($candidate in $candidates) {
            $candidateHash = Get-PathHash $candidate.FullName
            if ($candidateHash -eq $Manifest.rom_sha256) { $match = $candidate; $romHash = $candidateHash; break }
        }
        if ($null -eq $match) { throw 'No matching USA Rev 1 .3ds file found directly in this folder. Choose the exact ROM file or its immediate folder. European ROMs and other dumps are not supported by this package.' }
        $rom = $match
        Write-Host ('Found: ' + $rom.Name)
    }
    if ($rom -isnot [IO.FileInfo]) { throw 'Choose a .3ds file or the folder containing it.' }
    if ($rom.Length -ne $Manifest.rom_bytes) { throw 'This ROM size is not the supported USA Rev 1 dump.' }
    Write-Host 'Checking ROM SHA-256...'
    if ($null -eq $romHash) { $romHash = Get-PathHash $rom.FullName }
    if ($romHash -ne $Manifest.rom_sha256) {
        throw 'ROM does not match the tested USA Rev 1 dump. No installation was made. EUR/CHN, other revisions, and encrypted dumps require separate support.'
    }
    $stream = [IO.File]::OpenRead($rom.FullName)
    $reader = New-Object IO.BinaryReader($stream)
    try {
        $stream.Position = 0x120
        $partitionOffset = [long]$reader.ReadUInt32() * 512
        if ($partitionOffset -lt 512 -or $partitionOffset + 0xA00 -gt $stream.Length) { throw 'Invalid NCSD partition.' }
        $stream.Position = $partitionOffset + 0x200
        [byte[]]$header = $reader.ReadBytes(0x800)
        if ($header.Length -ne 0x800 -or (Get-ByteHash $header) -ne $Manifest.original_exheader_sha256) { throw 'Original executable header does not match.' }
    } finally { $reader.Dispose(); $stream.Dispose() }
    [Array]::Copy([BitConverter]::GetBytes([uint32]0x7e684),0,$header,0x3c,4)
    if ((Get-ByteHash $header) -ne $Manifest.patched_exheader_sha256) { throw 'Generated header checksum failed.' }
    return ,$header
}
function Install-PatchFiles([string]$UserDirectory, [byte[]]$Patch, [byte[]]$Header, $Manifest) {
    $root = [IO.Path]::GetFullPath($UserDirectory)
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'Azahar user directory does not exist.' }
    $target = Join-Path $root ('load\mods\' + $Manifest.title_id)
    $stateFile = Join-Path $target 'mario60-installation.json'
    if (Test-Path -LiteralPath $stateFile) { throw 'A Mario 60 FPS installation record already exists. Uninstall that package first.' }
    $backup = Join-Path $target ('mario60-backups\' + [Guid]::NewGuid().ToString('N'))
    [IO.Directory]::CreateDirectory($backup) | Out-Null
    $files = @(
        @{ Relative = 'exheader.bin'; Data = $Header; Hash = $Manifest.patched_exheader_sha256 },
        @{ Relative = 'exefs\code.ips'; Data = $Patch; Hash = $Manifest.patch_sha256 }
    )
    $records = @()
    foreach ($file in $files) {
        $destination = Join-Path $target $file.Relative
        $saved = Join-Path $backup ([IO.Path]::GetFileName($file.Relative))
        $exists = Test-Path -LiteralPath $destination -PathType Leaf
        $previousHash = $null
        if ($exists) { [IO.File]::Copy($destination,$saved,$false); $previousHash = Get-PathHash $saved }
        $records += @{ relative = $file.Relative; backup = [IO.Path]::GetFileName($saved); existed = $exists; previous_sha256 = $previousHash; installed_sha256 = $file.Hash }
    }
    $state = @{ format = 1; title_id = $Manifest.title_id; backup_name = [IO.Path]::GetFileName($backup); files = $records; installed = $false }
    [IO.File]::WriteAllText($stateFile,($state | ConvertTo-Json -Depth 6))
    try {
        foreach ($file in $files) {
            $destination = Join-Path $target $file.Relative
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination)) | Out-Null
            [IO.File]::WriteAllBytes($destination,$file.Data)
            if ((Get-PathHash $destination) -ne $file.Hash) { throw 'Installed file checksum failed.' }
        }
        $state.installed = $true
        [IO.File]::WriteAllText($stateFile,($state | ConvertTo-Json -Depth 6))
    } catch {
        foreach ($record in $records) {
            $destination = Join-Path $target $record.relative
            if ($record.existed) { [IO.File]::Copy((Join-Path $backup $record.backup),$destination,$true) }
            elseif (Test-Path -LiteralPath $destination) { Remove-Item -LiteralPath $destination }
        }
        Remove-Item -LiteralPath $stateFile
        throw
    }
    Write-Host ('Installed in: ' + $target)
    Write-Host 'Existing patch files are backed up. Your ROM and saves were not modified.'
}
function Uninstall-PatchFiles([string]$UserDirectory, $Manifest) {
    $target = Join-Path ([IO.Path]::GetFullPath($UserDirectory)) ('load\mods\' + $Manifest.title_id)
    $stateFile = Join-Path $target 'mario60-installation.json'
    if (-not (Test-Path -LiteralPath $stateFile -PathType Leaf)) { throw 'No installation record found in this Azahar user directory.' }
    $state = Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json
    if ($state.format -ne 1 -or $state.title_id -ne $Manifest.title_id -or $state.backup_name -notmatch '^[a-f0-9]{32}$' -or @($state.files).Count -ne 2) { throw 'Invalid backup record.' }
    $backup = Join-Path $target ('mario60-backups\' + $state.backup_name)
    $expectedNames = @('exheader.bin','exefs\code.ips')
    foreach ($record in $state.files) {
        if ($record.relative -notin $expectedNames -or $record.backup -ne [IO.Path]::GetFileName($record.relative)) { throw 'Invalid backup file path.' }
        $destination = Join-Path $target $record.relative
        if (-not (Test-Path -LiteralPath $destination -PathType Leaf) -or (Get-PathHash $destination) -ne $record.installed_sha256) { throw 'Installed files have changed since installation. Review them before restoring a backup.' }
        if ($record.existed -and (Get-PathHash (Join-Path $backup $record.backup)) -ne $record.previous_sha256) { throw 'Backup checksum failed.' }
    }
    foreach ($record in $state.files) {
        $destination = Join-Path $target $record.relative
        if ($record.existed) { [IO.File]::Copy((Join-Path $backup $record.backup),$destination,$true) }
        else { Remove-Item -LiteralPath $destination }
    }
    Remove-Item -LiteralPath $stateFile
    Write-Host 'Patch removed; previous patch files restored. Backup folder retained.'
}
