param(
    [string]$ComsolRoot = 'D:\Program Files\COMSOL\COMSOL64\Multiphysics',
    [string]$ApplicationRoot = "$env:USERPROFILE\.comsol\v64\applications\files\user\dia60al40_electrothermal_mesh_study"
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runner = Join-Path $PSScriptRoot 'run_comsol_electrothermal_mvp.ps1'
$evidenceRoot = Join-Path $repo 'docs\reproduction_goal\04_comsol_electrothermal_field\evidence\mesh_convergence'
$analyzer = Join-Path $PSScriptRoot 'analyze_comsol_mesh_convergence.py'
$levels = @(
    [pscustomobject]@{ Name = 'coarse'; Hmax = 12.0; Hmin = 1.5 },
    [pscustomobject]@{ Name = 'medium'; Hmax = 8.0; Hmin = 1.0 },
    [pscustomobject]@{ Name = 'fine'; Hmax = 5.0; Hmin = 0.625 }
)

foreach ($level in $levels) {
    Write-Host "Running COMSOL mesh level $($level.Name): hmax=$($level.Hmax) um, hmin=$($level.Hmin) um"
    & $runner `
        -ComsolRoot $ComsolRoot `
        -ApplicationDir (Join-Path $ApplicationRoot $level.Name) `
        -MeshHmaxUm $level.Hmax `
        -MeshHminUm $level.Hmin `
        -EvidenceSubpath (Join-Path 'mesh_convergence' $level.Name)
}

py $analyzer $evidenceRoot (Join-Path $evidenceRoot 'comparison')
if ($LASTEXITCODE -ne 0) {
    throw "Mesh convergence analyzer failed with exit code $LASTEXITCODE"
}
$summary = Get-Content -Raw (Join-Path $evidenceRoot 'comparison\mesh_convergence_summary.json') | ConvertFrom-Json
if ($summary.decision -ne 'mesh_pass') {
    throw "COMSOL mesh convergence decision is $($summary.decision)"
}

Write-Host "COMSOL mesh convergence passed and was archived to $evidenceRoot"
