. "$PSScriptRoot\common.ps1"

Write-ManagerLine "INFO" "Manager" "Restarting ScenarioRP"
& "$PSScriptRoot\stop-all.ps1"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Start-Sleep -Seconds 1
& "$PSScriptRoot\start-all.ps1"
exit $LASTEXITCODE
