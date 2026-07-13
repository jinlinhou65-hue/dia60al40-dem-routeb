param(
    [string]$ComsolRoot = 'D:\Program Files\COMSOL\COMSOL64\Multiphysics',
    [string]$ApplicationDir = "$env:USERPROFILE\.comsol\v64\applications\files\user\dia60al40_electrothermal_mvp",
    [ValidateRange(0.000001, 1000000.0)]
    [double]$MeshHmaxUm = 8.0,
    [ValidateRange(0.000001, 1000000.0)]
    [double]$MeshHminUm = 1.0,
    [ValidateRange(0.000000001, 1000000.0)]
    [double]$AppliedVoltageV = 0.1,
    [string]$InputSubpath = 'data\prepared',
    [string]$EvidenceSubpath = 'comsol_smoke'
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$stage = Join-Path $repo 'docs\reproduction_goal\04_comsol_electrothermal_field'
$inputRoot = [System.IO.Path]::GetFullPath((Join-Path $stage $InputSubpath))
$evidenceRoot = [System.IO.Path]::GetFullPath((Join-Path $stage 'evidence'))
$evidence = [System.IO.Path]::GetFullPath((Join-Path $evidenceRoot $EvidenceSubpath))
$javaSource = Join-Path $repo 'comsol\Dia60Al40_ElectrothermalMVP.java'
$compile = Join-Path $ComsolRoot 'bin\win64\comsolcompile.exe'
$batch = Join-Path $ComsolRoot 'bin\win64\comsolbatch.exe'

if ($MeshHminUm -gt $MeshHmaxUm) {
    throw 'MeshHminUm must not exceed MeshHmaxUm'
}
$evidencePrefix = $evidenceRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
if (-not $evidence.StartsWith($evidencePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'EvidenceSubpath must resolve inside the stage evidence directory'
}
$stagePrefix = $stage.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
if (-not $inputRoot.StartsWith($stagePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'InputSubpath must resolve inside the Stage 04 directory'
}

foreach ($required in @($javaSource, $compile, $batch, (Join-Path $inputRoot 'stage5_contact_property_grid.csv'), (Join-Path $inputRoot 'stage5_comsol_interpolation.txt'))) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Required file not found: $required"
    }
}

New-Item -ItemType Directory -Force -Path $ApplicationDir, $evidence | Out-Null
$resultDir = Join-Path $ApplicationDir 'result'
New-Item -ItemType Directory -Force -Path $resultDir | Out-Null
Copy-Item -LiteralPath $javaSource -Destination (Join-Path $ApplicationDir 'Dia60Al40_ElectrothermalMVP.java') -Force
Copy-Item -LiteralPath (Join-Path $inputRoot 'stage5_contact_property_grid.csv') -Destination (Join-Path $ApplicationDir 'stage5_contact_property_grid.csv') -Force
Copy-Item -LiteralPath (Join-Path $inputRoot 'stage5_comsol_interpolation.txt') -Destination (Join-Path $ApplicationDir 'stage5_comsol_interpolation.txt') -Force

Push-Location $ApplicationDir
try {
    & $compile 'Dia60Al40_ElectrothermalMVP.java'
    if ($LASTEXITCODE -ne 0) {
        throw "comsolcompile failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

$classFile = Join-Path $ApplicationDir 'Dia60Al40_ElectrothermalMVP.class'
$gridFile = Join-Path $ApplicationDir 'stage5_contact_property_grid.csv'
$logFile = Join-Path $ApplicationDir 'comsol_batch.log'
$runStarted = Get-Date
$batchProcess = Start-Process -FilePath $batch -ArgumentList @(
    '-inputfile', $classFile,
    '-batchlog', $logFile,
    '-stoptime', '180',
    $gridFile,
    $resultDir,
    $MeshHmaxUm.ToString([System.Globalization.CultureInfo]::InvariantCulture),
    $MeshHminUm.ToString([System.Globalization.CultureInfo]::InvariantCulture),
    $AppliedVoltageV.ToString([System.Globalization.CultureInfo]::InvariantCulture)
) -WindowStyle Hidden -Wait -PassThru
if ($batchProcess.ExitCode -ne 0) {
    throw "comsolbatch launcher failed with exit code $($batchProcess.ExitCode)"
}

# COMSOL can return zero for a Java exception, so the log and summary are hard gates.
$summaryPath = Join-Path $resultDir 'comsol_summary.json'
$deadline = $runStarted.AddSeconds(210)
do {
    $summaryIsFresh = (Test-Path -LiteralPath $summaryPath) -and
        ((Get-Item -LiteralPath $summaryPath).LastWriteTime -ge $runStarted)
    $lastLogLine = if (Test-Path -LiteralPath $logFile) {
        Get-Content -LiteralPath $logFile | Where-Object { $_.Trim() } | Select-Object -Last 1
    }
    # COMSOL ends localized batch logs with "<label>: <seconds> s.".
    $logIsComplete = $lastLogLine -match ':\s*\d+\s*s\.\s*$'
    if ($summaryIsFresh -and $logIsComplete) {
        break
    }
    Start-Sleep -Seconds 2
} while ((Get-Date) -lt $deadline)

if (-not $summaryIsFresh -or -not $logIsComplete) {
    throw "COMSOL batch evidence timeout: summaryFresh=$summaryIsFresh logComplete=$logIsComplete"
}

$logText = Get-Content -LiteralPath $logFile -Raw
if ($logText -match '运行 Java 类时出错|Error running Java class|\bException\b|\*\*\*\*\*错误') {
    throw 'COMSOL batch log contains a Java/model error block'
}
if (-not (Test-Path -LiteralPath $summaryPath)) {
    throw 'COMSOL summary was not generated'
}
$summary = Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json
$maxTemperature = [double]$summary.max_temperature_k
$summaryVoltage = [double]$summary.applied_voltage_v
$summaryCurrent = [double]$summary.top_current_a_per_m_depth
if (
    $summary.solve_status -ne 'success' -or
    [double]::IsNaN($maxTemperature) -or
    [double]::IsInfinity($maxTemperature) -or
    [double]::IsNaN($summaryCurrent) -or
    [double]::IsInfinity($summaryCurrent) -or
    [math]::Abs($summaryVoltage - $AppliedVoltageV) -gt 1.0e-10
) {
    throw 'COMSOL summary did not pass the finite successful-solve gate'
}

Copy-Item -LiteralPath $logFile -Destination (Join-Path $evidence 'comsol_batch.log') -Force
foreach ($name in @(
    'comsol_fields.csv',
    'comsol_joule_heat.png',
    'comsol_potential.png',
    'comsol_summary.json',
    'comsol_temperature.png',
    'Dia60Al40_ElectrothermalMVP.mph'
)) {
    Copy-Item -LiteralPath (Join-Path $resultDir $name) -Destination (Join-Path $evidence $name) -Force
}

Write-Host "COMSOL electrothermal MVP passed at $AppliedVoltageV V and was archived to $evidence"
