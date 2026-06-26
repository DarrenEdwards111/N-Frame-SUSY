param(
    [int]$Batches = 10,
    [int]$ChunkSize = 10,
    [string]$Records = "63102,63118,63126,72753,75592"
)

$ErrorActionPreference = "Stop"
$project = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $project "outputs_remote_opq_sm_background_build\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "exact_sumweight_campaign.log"

for ($batch = 1; $batch -le $Batches; $batch++) {
    "[$(Get-Date -Format s)] Starting exact sumweight batch $batch of $Batches" | Tee-Object -FilePath $log -Append
    $env:NFRAME_SUMWEIGHT_RECORDS = $Records
    $env:NFRAME_SUMWEIGHT_CHUNK_SIZE = "$ChunkSize"
    $env:NFRAME_SUMWEIGHT_MAX_CHUNKS = "1"
    & python (Join-Path $project "scripts\262_run_exact_sumweight_chunks.py") 2>&1 | Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -ne 0) { throw "Exact sumweight batch $batch failed with exit code $LASTEXITCODE" }
    & python (Join-Path $project "scripts\263_build_exact_hybrid_sm_normalisation_tiers.py") 2>&1 | Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -ne 0) { throw "Normalisation ledger update after batch $batch failed with exit code $LASTEXITCODE" }
}

"[$(Get-Date -Format s)] Exact sumweight campaign completed" | Tee-Object -FilePath $log -Append
