. "$PSScriptRoot\common.ps1"

Write-ManagerLine "INFO" "FXServer" "Stopping FXServer"
$fxOk = Stop-ManagedProcess -PidFile $FxPidFile -ExpectedName "FXServer.exe" -ExpectedPath $FxServerExe -Source "FXServer"
$extraFxOk = Stop-ManagedProcessesBySignature -ExpectedName "FXServer.exe" -ExpectedPath $FxServerExe -Source "FXServer"

if ($fxOk -and $extraFxOk) {
    Write-ManagerLine "INFO" "FXServer" "FXServer stopped"
    exit 0
}

Write-ManagerLine "ERROR" "FXServer" "FXServer stop failed"
exit 1
