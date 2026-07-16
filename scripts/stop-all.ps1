. "$PSScriptRoot\common.ps1"

Write-ManagerLine "INFO" "Manager" "Stopping ScenarioRP"
& "$PSScriptRoot\stop-server.ps1"
$serverCode = $LASTEXITCODE

if ($serverCode -eq 0) {
    & "$PSScriptRoot\announce-discord-offline.ps1"
    $announceCode = $LASTEXITCODE
}
else {
    $announceCode = 1
}

& "$PSScriptRoot\stop-discord-bot.ps1"
$botCode = $LASTEXITCODE

if ($serverCode -eq 0 -and $announceCode -eq 0 -and $botCode -eq 0) {
    Write-ManagerLine "INFO" "Manager" "ScenarioRP stopped"
    exit 0
}

Write-ManagerLine "ERROR" "Manager" "ScenarioRP stop failed"
exit 1
