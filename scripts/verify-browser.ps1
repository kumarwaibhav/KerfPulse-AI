param([int]$Port = 18001)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path $PSScriptRoot -Parent
Set-Location $workspace
if ($Port -lt 1024 -or $Port -gt 65535) { throw 'Use an unprivileged TCP port within 1024..65535' }
$project = 'kerfpulse-browser-' + [Guid]::NewGuid().ToString('N')
$evidence = Join-Path $workspace ('artifacts/browser-verification/' + $project)
New-Item -ItemType Directory -Force $evidence | Out-Null
$previousPort = $env:PDM_HTTP_PORT
$previousUrl = $env:PDM_E2E_URL
$testsPassed = $false
try {
    $env:PDM_HTTP_PORT = [string]$Port
    $env:PDM_E2E_URL = 'http://127.0.0.1:' + $Port
    & docker compose -p $project up -d --no-build --wait --wait-timeout 120
    if ($LASTEXITCODE -ne 0) { throw 'Isolated browser stack did not become healthy' }
    Push-Location (Join-Path $workspace 'web')
    try {
        # Explicit .cmd avoids PowerShell/npm argument forwarding differences.
        & npx.cmd playwright test --workers=1
        if ($LASTEXITCODE -ne 0) { throw 'Browser verification failed; inspect retained test evidence' }
        $testsPassed = $true
    } finally { Pop-Location }
} finally {
    & docker compose -p $project logs --no-color 2>&1 | Set-Content (Join-Path $evidence 'services.log')
    # Only this invocation's random test project and volumes may be removed.
    if ($project -notmatch '^kerfpulse-browser-[0-9a-f]{32}$') { throw 'Unexpected verification project name' }
    & docker compose -p $project down --volumes --remove-orphans
    $cleanupPassed = $LASTEXITCODE -eq 0
    $env:PDM_HTTP_PORT = $previousPort
    $env:PDM_E2E_URL = $previousUrl
    [ordered]@{ project = $project; tested_url = 'http://127.0.0.1:' + $Port; tests_passed = $testsPassed;
        cleanup_passed = $cleanupPassed; isolation = 'Separate Compose network, PostgreSQL volume, broker and workers';
        recorded_at = [DateTime]::UtcNow.ToString('o') } | ConvertTo-Json | Set-Content (Join-Path $evidence 'result.json')
    if (-not $cleanupPassed) { throw "Cleanup failed for test project $project" }
}
