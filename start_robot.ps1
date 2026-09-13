param(
    [ValidateSet(3,4)][int]$Problem = 4,
    [ValidateSet('rehearsal','formal')][string]$RunKind = 'rehearsal',
    [string]$CaseCode,
    [string]$RobotId,
    [switch]$V8,
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
$runtime = (Get-Command $Python -CommandType Application -ErrorAction Stop).Source
if ([string]::IsNullOrWhiteSpace($CaseCode)) { $CaseCode = Read-Host 'Case code shown in simulator' }
if ([string]::IsNullOrWhiteSpace($CaseCode)) { throw 'Case code required' }
if ([string]::IsNullOrWhiteSpace($RobotId)) { $RobotId = Read-Host 'Team ID currently logged into simulator' }
if ([string]::IsNullOrWhiteSpace($RobotId)) { throw 'Team ID required at runtime' }
Write-Host "Question=$Problem  Run=$RunKind  Team=$RobotId  Case=$CaseCode"
Write-Host 'Policy=20260912-shared-service-r4'
Write-Host 'Start the matching simulator module yourself. This script does not start it.'
$confirmation = Read-Host 'Type CONNECT to send robot commands to the ready local interface'
if ($confirmation -cne 'CONNECT') { Write-Host 'No connection made.'; exit 0 }
& $runtime (Join-Path $PSScriptRoot 'run_robot.py') --problem $Problem --run-kind $RunKind --case-code $CaseCode --robot-id $RobotId --connect
exit $LASTEXITCODE
