param(
    [ValidateSet(3,4)][int]$Problem = 4,
    [ValidateSet('rehearsal','formal')][string]$RunKind = 'rehearsal',
    [string]$CaseCode,
    [string]$RobotId = '202612001024',
    [switch]$Baseline,
    [switch]$V3,
    [switch]$V4,
    [switch]$V5,
    [switch]$V6
)
$ErrorActionPreference = 'Stop'
$runtime = 'C:\Users\74299\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $runtime)) { $runtime = 'python' }
if ([string]::IsNullOrWhiteSpace($CaseCode)) { $CaseCode = Read-Host 'Case code shown in simulator' }
if ([string]::IsNullOrWhiteSpace($CaseCode)) { throw 'Case code required' }
Write-Host "Question=$Problem  Run=$RunKind  Team=$RobotId  Case=$CaseCode"
$strategyLabel = if ($Baseline) { 'midpoint-v1' } elseif ($V3) { 'annular-history-route-v3' } elseif ($V4) { 'certified-cooperative-v4' } elseif ($V5) { 'joint-outcome-lookahead-v5' } elseif ($V6) { 'residual-committed-policy-v6' } else { 'obligation-service-interception-v7' }
Write-Host "Strategy=$strategyLabel"
Write-Host 'Start the matching simulator module yourself. This script does not start it.'
$confirmation = Read-Host 'Type CONNECT to send robot commands to the ready local interface'
if ($confirmation -cne 'CONNECT') { Write-Host 'No connection made.'; exit 0 }
$strategyArgs = @()
if ($Baseline) { $strategyArgs += '--baseline' }
if ($V3) { $strategyArgs += '--v3' }
if ($V4) { $strategyArgs += '--v4' }
if ($V5) { $strategyArgs += '--v5' }
if ($V6) { $strategyArgs += '--v6' }
& $runtime (Join-Path $PSScriptRoot 'run_robot.py') --problem $Problem --run-kind $RunKind --case-code $CaseCode --robot-id $RobotId --connect @strategyArgs
exit $LASTEXITCODE
