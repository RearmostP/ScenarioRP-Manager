. "$PSScriptRoot\common.ps1"

Write-ManagerLine "INFO" "FXServer" "Close Shell requested"

$serverEndpoint = Get-ServerEndpoint
if (Test-TcpPort -HostName $serverEndpoint.Host -Port $serverEndpoint.Port) {
    Write-ManagerLine "ERROR" "FXServer" "Server shell can be closed only after the server port is offline: $($serverEndpoint.Host):$($serverEndpoint.Port)"
    exit 1
}

$fxOk = Stop-ManagedProcess -PidFile $FxPidFile -ExpectedName "FXServer.exe" -ExpectedPath $FxServerExe -Source "FXServer" -Context "server shell PID"
$extraFxOk = Stop-ManagedProcessesBySignature -ExpectedName "FXServer.exe" -ExpectedPath $FxServerExe -Source "FXServer"

if ($fxOk -and $extraFxOk) {
    Write-ManagerLine "INFO" "FXServer" "Server shell closed"
    & "$PSScriptRoot\stop-discord-bot.ps1"
    $botCode = $LASTEXITCODE

    if ($botCode -eq 0) {
        Write-ManagerLine "INFO" "Manager" "Server shell and Discord Bot closed"
        exit 0
    }

    Write-ManagerLine "ERROR" "DiscordBot" "Server shell closed, but Discord Bot stop failed"
    exit 1
}

Write-ManagerLine "ERROR" "FXServer" "Server shell close failed"
exit 1
