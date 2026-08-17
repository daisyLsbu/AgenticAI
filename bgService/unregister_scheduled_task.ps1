# Removes the scheduled task. Run this if you want to stop auto-starting
# the Slack bot, or before re-registering it after making changes.

$taskName = "LocalAgentSlackBot"

Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

Write-Host "Task '$taskName' removed."
Write-Host "If slack_bot.py / python.exe is still running, stop it manually, e.g.:"
Write-Host "    Get-Process python | Stop-Process"
