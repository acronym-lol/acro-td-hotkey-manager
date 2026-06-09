$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
[System.Environment]::SetEnvironmentVariable('ACRO_TD_HOTKEY_MANAGER', $ScriptDir, 'User')
$env:ACRO_TD_HOTKEY_MANAGER = $ScriptDir
Write-Host "ACRO_TD_HOTKEY_MANAGER set to $ScriptDir"
