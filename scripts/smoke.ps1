Param(
  [Parameter(Mandatory=$false)]
  [string]$BaseUrl = "http://localhost:8000"
)

Write-Host "[smoke] Checking base URL: $BaseUrl"

function Test-Url {
  param([string]$Url)
  Write-Host "[smoke] GET $Url"
  try {
    $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
    if ($resp.StatusCode -lt 200 -or $resp.StatusCode -ge 400) {
      throw "StatusCode=$($resp.StatusCode)"
    }
  } catch {
    Write-Error "[smoke] Failed: $Url :: $_"
    exit 1
  }
}

Test-Url "$BaseUrl/"
Test-Url "$BaseUrl/api/docs/"

Write-Host "[smoke] OK: $BaseUrl is responsive"
