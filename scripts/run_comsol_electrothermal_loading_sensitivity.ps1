param(
    [string]$ComsolRoot = 'D:\Program Files\COMSOL\COMSOL64\Multiphysics',
    [string]$ApplicationDir = "$env:USERPROFILE\.comsol\v64\applications\files\user\dia60al40_loading_sensitivity"
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$stage = Join-Path $repo 'docs\reproduction_goal\04_comsol_electrothermal_field'
$evidence = Join-Path $stage 'evidence\loading_mode_sensitivity'
$planPath = Join-Path $evidence 'comsol_run_plan.json'
$fvmSummaryPath = Join-Path $evidence 'loading_mode_summary.json'
$loadingParameters = Join-Path $stage 'data\source\loading_mode_parameter_set.json'
$singleRun = Join-Path $PSScriptRoot 'run_comsol_electrothermal_mvp.ps1'
$analyzer = Join-Path $PSScriptRoot 'analyze_electrothermal_loading_comsol.py'
$refinementAnalyzer = Join-Path $PSScriptRoot 'analyze_electrothermal_fvm_refinement.py'

foreach ($required in @($planPath, $fvmSummaryPath, $loadingParameters, $singleRun, $analyzer, $refinementAnalyzer)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Required file not found: $required"
    }
}

$fvmSummary = Get-Content -LiteralPath $fvmSummaryPath -Raw | ConvertFrom-Json
if ($fvmSummary.decision -ne 'loading_mode_fvm_pass') {
    throw 'FVM loading-mode gates must pass before licensed COMSOL runs'
}
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if ($plan.cases.Count -ne 6) {
    throw "Expected six COMSOL cases, got $($plan.cases.Count)"
}
if ([bool]$plan.fixed_mesh.repeat_mesh_study) {
    throw 'The loading sensitivity must not repeat the mesh study'
}

foreach ($case in $plan.cases) {
    Write-Host "Running $($case.case_id) at $($case.applied_voltage_v) V"
    & $singleRun `
        -ComsolRoot $ComsolRoot `
        -ApplicationDir $ApplicationDir `
        -MeshHmaxUm ([double]$plan.fixed_mesh.hmax_um) `
        -MeshHminUm ([double]$plan.fixed_mesh.hmin_um) `
        -AppliedVoltageV ([double]$case.applied_voltage_v) `
        -InputSubpath ($case.input_subpath -replace '/', '\') `
        -EvidenceSubpath ($case.evidence_subpath -replace '/', '\')
}

& py -3 $analyzer $evidence $loadingParameters
if ($LASTEXITCODE -ne 0) {
    throw "Loading-mode analyzer failed with exit code $LASTEXITCODE"
}
$comparisonPath = Join-Path $evidence 'comparison\loading_mode_comparison.json'
$comparison = Get-Content -LiteralPath $comparisonPath -Raw | ConvertFrom-Json
$expectedReviewCases = @('fixed_current_multiplier_1', 'fixed_voltage_multiplier_1')
$actualReviewCases = @($comparison.failed_case_ids | Sort-Object)
if ($comparison.decision -ne 'review' -or (Compare-Object $expectedReviewCases $actualReviewCases)) {
    throw "Expected preserved two-case review, got decision=$($comparison.decision) failed=$($actualReviewCases -join ',')"
}

$sourceGrid = Join-Path $stage 'data\prepared\loading_mode_sensitivity\multiplier_1\stage5_contact_property_grid.csv'
$refinedPrepared = Join-Path $stage 'data\prepared\loading_mode_sensitivity\fvm_refinement\multiplier_1'
$refinedEvidence = Join-Path $evidence 'fvm_refinement\multiplier_1'
$referenceComsol = Join-Path $evidence 'comsol\fixed_voltage\multiplier_1'
& py -3 $refinementAnalyzer `
    $sourceGrid `
    $refinedPrepared `
    $refinedEvidence `
    (Join-Path $referenceComsol 'comsol_summary.json') `
    (Join-Path $referenceComsol 'comsol_fields.csv')
if ($LASTEXITCODE -ne 0) {
    throw "FVM refinement analyzer failed with exit code $LASTEXITCODE"
}
$refinementPath = Join-Path $refinedEvidence 'comparison\fvm_refinement_summary.json'
$refinement = Get-Content -LiteralPath $refinementPath -Raw | ConvertFrom-Json
if ($refinement.decision -ne 'fvm_refinement_pass' -or $refinement.original_loading_decision -ne 'review') {
    throw "Expected refinement pass preserving original review, got $($refinement.decision)"
}

Write-Host "Six-case COMSOL review and preregistered FVM refinement were archived to $evidence"
