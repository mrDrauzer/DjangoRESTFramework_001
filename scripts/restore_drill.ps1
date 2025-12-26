Param(
  [Parameter(Mandatory=$false)]
  [string]$DumpFile
)

function Fail($msg) {
  Write-Error $msg
  exit 1
}

Write-Host "[restore-drill] Starting restore verification..."

# Resolve dump file
if (-not $DumpFile -or $DumpFile -eq '') {
  $latest = Get-ChildItem -Path "backups" -Filter "*.dump" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
  if (-not $latest) { Fail "No dump file found in backups/. Provide -DumpFile backups/<file>.dump" }
  $DumpFile = $latest.FullName
}
if (-not (Test-Path -Path $DumpFile)) { Fail "Dump file not found: $DumpFile" }

$ts = Get-Date -Format yyyyMMdd_HHmmss
$TmpDb = "restore_drill_$ts"
Write-Host "[restore-drill] Temporary DB: $TmpDb"
Write-Host "[restore-drill] Using dump: $DumpFile"

# Create temp database
Write-Host "[restore-drill] Creating database..."
$createCmd = "createdb -U '$env:POSTGRES_USER' '$TmpDb'"
docker compose exec -T db sh -lc $createCmd | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "Failed to create DB $TmpDb" }

try {
  # Restore
  Write-Host "[restore-drill] Restoring dump into $TmpDb ... this may take a while"
  Get-Content -Encoding Byte $DumpFile |
    docker compose exec -T db sh -lc "pg_restore -U '$env:POSTGRES_USER' -d '$TmpDb' --clean --if-exists -v" | Out-Host
  if ($LASTEXITCODE -ne 0) { throw "Restore failed" }

  # Basic checks
  Write-Host "[restore-drill] Basic checks ..."
  docker compose exec -T db sh -lc "psql -U '$env:POSTGRES_USER' -d '$TmpDb' -c 'SELECT 1;'" | Out-Host
  # Try to query django_migrations if exists
  docker compose exec -T db sh -lc "psql -U '$env:POSTGRES_USER' -d '$TmpDb' -c 'SELECT count(*) AS django_migrations FROM django_migrations;'" | Out-Host
} catch {
  Write-Warning "[restore-drill] Error: $_"
} finally {
  Write-Host "[restore-drill] Dropping temporary database ..."
  docker compose exec -T db sh -lc "dropdb -U '$env:POSTGRES_USER' '$TmpDb'" | Out-Null
}

Write-Host "[restore-drill] Done"
