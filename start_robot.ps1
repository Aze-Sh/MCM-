param(
    [ValidateSet(3,4)][int]$problem = 4,
    [ValidateSet('rehearsal','formal')][string]$runkind = 'rehearsal',
    [string]$casecode,
    [string]$robotid,
    [switch]$v8,
    [string]$python = 'python'
)
$ErrorActionPreference = 'Stop'
$runtime = (Get-Command $python -CommandType Application -ErrorAction Stop).Source
if ([string]::IsNullOrWhiteSpace($casecode)) { $casecode = Read-Host 'Case code shown in simulator' }
if ([string]::IsNullOrWhiteSpace($casecode)) { throw 'Case code required' }
if ([string]::IsNullOrWhiteSpace($robotid)) { $robotid = Read-Host 'Team ID currently logged into simulator' }
if ([string]::IsNullOrWhiteSpace($robotid)) { throw 'Team ID required at runtime' }
Write-Host "Question=$problem  Run=$runkind  Team=$robotid  Case=$casecode"
Write-Host 'Policy=20260912-shared-service-r4'
Write-Host 'Start the matching simulator module yourself. This script does not start it.'
$confirmation = Read-Host 'Type CONNECT to send robot commands to the ready local interface'
if ($confirmation -cne 'CONNECT') { Write-Host 'No connection made.'; exit 0 }
& $runtime (Join-Path $PSScriptRoot 'run_robot.py') --problem $problem --run-kind $runkind --case-code $casecode --robot-id $robotid --connect
exit $LASTEXITCODE
