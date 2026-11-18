param([switch]$IncludeAssets)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path $PSScriptRoot -Parent
Set-Location $workspace
$release = Join-Path $workspace 'release'
New-Item -ItemType Directory -Force $release | Out-Null
$archive = Join-Path $release $(if ($IncludeAssets) { 'kerfpulse-ai-showcase.zip' } else { 'kerfpulse-ai.zip' })
# Explicit allowlist keeps local credentials, databases and dependency caches out.
$items = @('pdm', 'web/src', 'web/index.html', 'web/package.json',
    'web/package-lock.json', 'web/tsconfig.json', 'web/vite.config.ts',
    'web/playwright.config.ts', 'web/tests', 'pytest.ini',
    'docs', 'tests', 'scripts', 'schemas', 'deploy', 'Dockerfile', 'compose.yaml',
    'requirements.txt', 'requirements-train.txt', 'requirements-test.txt', 'requirements-gpu.txt',
    '.dockerignore', '.gitignore', '.gitattributes', '.github', 'README.md', 'NOTICE.md', '.env.example')
if ($IncludeAssets) {
    $items += @('data/FeatureAndMetadata_Milling.csv', 'artifacts/nested-workpiece', 'artifacts/engineering-release')
}
$stage = Join-Path $release ('stage-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $stage | Out-Null
foreach ($item in $items) {
    if (-not (Test-Path -LiteralPath $item)) { throw "Missing package input $item" }
    $destination = Join-Path $stage $item
    New-Item -ItemType Directory -Force (Split-Path $destination -Parent) | Out-Null
    Copy-Item -LiteralPath $item -Destination $destination -Recurse
}
Get-ChildItem -LiteralPath $stage -Filter '*.pyc' -Recurse | Remove-Item
Get-ChildItem -LiteralPath $stage -Directory -Filter '__pycache__' -Recurse |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName }
Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $archive -Force
$resolvedStage = (Resolve-Path -LiteralPath $stage).Path
$resolvedRelease = (Resolve-Path -LiteralPath $release).Path
if ([IO.Path]::GetDirectoryName($resolvedStage) -ne $resolvedRelease -or
    [IO.Path]::GetFileName($resolvedStage) -notmatch '^stage-[0-9a-f]{32}$') {
    throw 'Unexpected package staging path'
}
Remove-Item -LiteralPath $resolvedStage -Recurse -Force
Get-FileHash -Algorithm SHA256 -LiteralPath $archive |
    Select-Object Algorithm, Hash | ConvertTo-Json | Set-Content ($archive + '.sha256.json')
Write-Output "Engineering package saved at $archive"
if ($IncludeAssets) {
    Write-Output 'Verified benchmark and engineering model assets included. Configure .env from .env.example, then docker compose up --build -d --wait.'
} else {
    Write-Output 'Run scripts/setup.ps1 after extraction to fetch verified data and reproduce models.'
}
