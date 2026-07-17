# Registers a Windows Task Scheduler job that runs the minute-check every 1 minute.
# Run from PowerShell:  powershell -ExecutionPolicy Bypass -File scripts/setup_task.ps1
# Re-run after moving the repo. Remove with: Unregister-ScheduledTask -TaskName "RemindMeMinuteCheck"

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$Uv = (Get-Command uv).Source
$TaskName = "RemindMeMinuteCheck"

$Action = New-ScheduledTaskAction `
    -Execute $Uv `
    -Argument "run --project `"$RepoRoot`" src/main.py" `
    -WorkingDirectory $RepoRoot

# Every 1 minute, indefinitely.
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 1)

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 2)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
    -Settings $Settings -Description "GCal -> Twilio 1-minute meeting call reminders" -Force

Write-Host "Task '$TaskName' registered (every 1 min). Repo: $RepoRoot"
Write-Host "NOTE: the PC must be awake for calls to fire. Test with: uv run src/main.py --dry-run"
