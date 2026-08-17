# Registers "LocalAgentSlackBot" as a Windows scheduled task that starts
# automatically when you log on, and restarts itself if it ever crashes.
# Run this once, in a normal (non-admin) PowerShell window.

$taskName = "LocalAgentSlackBot"
$root = $PSScriptRoot
$script = Join-Path $root "run_slack_bot.ps1"

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`"" `
    -WorkingDirectory $root

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Settings $settings -Description "Runs the local Ollama Slack bot at logon" -Force

Write-Host "Task '$taskName' registered - it will start automatically next time you log on."
Write-Host "To start it right now without logging off/on:"
Write-Host "    Start-ScheduledTask -TaskName '$taskName'"
Write-Host "Then check logs\slack_bot.log for confirmation (nothing prints to screen, it runs hidden)."
