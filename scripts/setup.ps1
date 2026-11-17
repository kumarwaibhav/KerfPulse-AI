$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path '.venv/Scripts/python.exe')) { python -m venv .venv }
& .venv/Scripts/python.exe -m pip install --upgrade 'pip>=26.2'
if ($LASTEXITCODE -ne 0) { throw 'Python installer upgrade failed' }
& .venv/Scripts/python.exe -m pip install -r requirements-test.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed' }
& .venv/Scripts/python.exe -m pdm.dataset fetch
if ($LASTEXITCODE -ne 0) { throw 'Dataset verification failed' }
& .venv/Scripts/python.exe -m pdm.release_model
if ($LASTEXITCODE -ne 0) { throw 'Engineering model release failed' }
& .venv/Scripts/python.exe -m pdm.validation --output artifacts/nested-workpiece
if ($LASTEXITCODE -ne 0) { throw 'Model validation failed' }
& .venv/Scripts/python.exe -m pdm.benchmark --artifacts artifacts/nested-workpiece
if ($LASTEXITCODE -ne 0) { throw 'Policy benchmark failed' }
& npm.cmd --prefix web ci
if ($LASTEXITCODE -ne 0) { throw 'Web dependency installation failed' }
& npm.cmd --prefix web run build
if ($LASTEXITCODE -ne 0) { throw 'Web build failed' }
if (-not (Test-Path '.env')) {
    $bytes = New-Object byte[] 24
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $password = [Convert]::ToHexString($bytes)
    Set-Content .env "POSTGRES_PASSWORD=$password"
}
Write-Output 'Setup complete. Run docker compose up --build -d'
