$ErrorActionPreference = 'Stop'
$workspace = Split-Path $PSScriptRoot -Parent
Set-Location $workspace
$suffix = [Guid]::NewGuid().ToString('N')
$fixture = 'kerfpulse-restore-' + $suffix
$dumpName = 'kerfpulse-' + $suffix + '.dump'
$private = Join-Path $workspace 'artifacts/private-backup'
New-Item -ItemType Directory -Force $private | Out-Null
$dumpPath = Join-Path $private $dumpName
$rowsPath = Join-Path $private ($suffix + '-rows.json')
$startedAt = Get-Date

function Check-Exit([string] $step) {
    if ($LASTEXITCODE -ne 0) { throw "$step failed with exit $LASTEXITCODE" }
}

try {
    # Consistent pg_dump snapshot. No project service or existing volume is stopped or removed.
    docker compose exec -T postgres pg_dump -U kerfpulse -d kerfpulse -Fc -f "/tmp/$dumpName"
    Check-Exit 'Backup'
    docker compose cp "postgres:/tmp/$dumpName" $dumpPath | Out-Null
    Check-Exit 'Backup copy'
    docker run --detach --network none --name $fixture --memory 512m --cpus 1 -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=kerfpulse postgres:17-alpine | Out-Null
    Check-Exit 'Isolated restore fixture'
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        docker exec $fixture pg_isready -U postgres -d kerfpulse *> $null
        if ($LASTEXITCODE -eq 0) { $ready = $true; break }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) { throw 'Restore fixture did not become ready' }
    docker cp $dumpPath "${fixture}:/tmp/backup.dump"
    Check-Exit 'Fixture copy'
    docker exec $fixture pg_restore -U postgres -d kerfpulse --no-owner --no-privileges --exit-on-error /tmp/backup.dump
    Check-Exit 'Restore'
    $counts = docker exec $fixture psql -U postgres -d kerfpulse -At -c "SELECT json_build_object('assessments',(SELECT count(*) FROM fresh_assessments),'sessions',(SELECT count(*) FROM sessions),'readings',(SELECT count(*) FROM readings),'conflicts',(SELECT count(*) FROM fresh_conflicts),'orphan_assessments',(SELECT count(*) FROM fresh_assessments WHERE owner NOT IN (SELECT id FROM sessions)))"
    Check-Exit 'Restored counts'
    docker exec $fixture psql -U postgres -d kerfpulse -At -c "SELECT coalesce(json_agg(json_build_object('digest',digest,'evidence',evidence::json,'assessment',payload::json)),'[]'::json) FROM fresh_assessments" | Set-Content -Encoding utf8 $rowsPath
    Check-Exit 'Restored evidence'
    $env:KERFPULSE_RESTORE_ROWS = $rowsPath
    $verified = @'
import hashlib, json, os
from pathlib import Path
rows = json.loads(Path(os.environ['KERFPULSE_RESTORE_ROWS']).read_text(encoding='utf-8-sig'))
for row in rows:
    digest = hashlib.sha256(json.dumps(row['evidence'], sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    assert digest == row['digest'] == row['assessment']['evidence_digest']
print(len(rows))
'@ | .venv/Scripts/python.exe -
    Check-Exit 'Evidence hash verification'
    $summary = [ordered]@{
        at = (Get-Date).ToUniversalTime().ToString('o')
        method = 'Consistent pg_dump; isolated PostgreSQL restore, no network or published ports'
        duration_seconds = [Math]::Round(((Get-Date)-$startedAt).TotalSeconds, 3)
        backup_sha256 = (Get-FileHash -LiteralPath $dumpPath -Algorithm SHA256).Hash
        counts = ($counts | ConvertFrom-Json)
        verified_evidence_digests = [int]$verified
        limitations = 'Local unencrypted private backup rehearsal; not production encryption, identity restoration, full application recovery, or cloud RPO/RTO acceptance'
    }
    if ($summary.counts.orphan_assessments -ne 0) { throw 'Restored orphan assessment found' }
    $summary | ConvertTo-Json -Depth 5 | Set-Content 'artifacts/restore-verification.json'
    $summary | ConvertTo-Json -Depth 5
} finally {
    # Only this script's randomly named fixture and its anonymous volumes may be removed.
    if ($fixture -notmatch '^kerfpulse-restore-[0-9a-f]{32}$') { throw 'Unexpected fixture name' }
    docker rm --force --volumes $fixture 2>$null | Out-Null
    docker compose exec -T postgres rm -f "/tmp/$dumpName"
    Remove-Item Env:KERFPULSE_RESTORE_ROWS -ErrorAction SilentlyContinue
}
