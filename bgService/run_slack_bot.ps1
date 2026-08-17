# Wrapper used by the scheduled task: waits for Ollama to be reachable,
# then runs slack_bot.py, restarting it automatically if it ever crashes.
# All output goes to logs\slack_bot.log (nothing shows on screen since the
# scheduled task runs hidden).

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$logDir = Join-Path $root 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir 'slack_bot.log'

function Log($msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Add-Content -Path $logFile -Value $line
}

Log "=== run_slack_bot.ps1 starting ==="

# Ollama may still be starting up at the same logon moment - wait up to 2 minutes.
$ollamaReady = $false
for ($i = 0; $i -lt 24; $i++) {
    try {
        Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5 | Out-Null
        $ollamaReady = $true
        break
    } catch {
        Start-Sleep -Seconds 5
    }
}
if (-not $ollamaReady) {
    Log "WARNING: Ollama not reachable after waiting ~2 min. Starting the bot anyway."
} else {
    Log "Ollama is reachable."
}

& "$root\.venv\Scripts\Activate.ps1"

while ($true) {
    Log "Starting slack_bot.py"
    python "$root\slack_bot.py" *>> $logFile
    Log "slack_bot.py exited (crash or stop) - restarting in 10s"
    Start-Sleep -Seconds 10
}
