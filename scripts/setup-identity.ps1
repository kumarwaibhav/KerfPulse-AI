$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$identityEnv = Join-Path $PWD 'artifacts/private-identity/local.env'
& .venv/Scripts/python.exe -m scripts.provision_identity --prepare
if ($LASTEXITCODE -ne 0) { throw 'Private identity configuration failed' }
& docker compose --env-file .env --env-file $identityEnv -f compose.yaml -f deploy/compose.identity.yaml --profile identity up -d identity api
if ($LASTEXITCODE -ne 0) { throw 'Local identity profile startup failed' }
& .venv/Scripts/python.exe -m scripts.provision_identity
if ($LASTEXITCODE -ne 0) { throw 'Named local account provisioning failed' }
Write-Output 'Open http://localhost:8000/?workspace=operations. Private credentials: artifacts/private-identity/engineer.json'
Write-Output 'This is a loopback development identity provider, not a public production identity deployment.'
