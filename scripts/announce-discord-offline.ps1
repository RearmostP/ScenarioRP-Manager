. "$PSScriptRoot\common.ps1"

$environment = Test-EnvironmentChecks -Checks @(
    @{ Name = "Discord bot Python"; Path = $BotPython },
    @{ Name = "Discord offline announcer"; Path = $BotOfflineAnnouncer }
)
if (-not $environment.Ok) {
    exit 1
}

Write-ManagerLine "INFO" "DiscordBot" "Announcing server offline"
& $BotPython $BotOfflineAnnouncer
if ($LASTEXITCODE -ne 0) {
    Write-ManagerLine "ERROR" "DiscordBot" "Offline announcement failed"
    exit 1
}

Write-ManagerLine "INFO" "DiscordBot" "Offline announcement sent"
exit 0
