# Build the Windows -> macOS transport package. Copies only; it deletes nothing and pushes nothing.
#
#   powershell -File migration\package_for_mac.ps1 -Mode Report     # sizes only, copy nothing
#   powershell -File migration\package_for_mac.ps1 -Mode Manifests  # manifests + bundle + docs
#   powershell -File migration\package_for_mac.ps1 -Mode Full       # the above plus repo and data
#
# -Mode Full duplicates about 385 MB. Use it for the external-SSD route. For a network transfer,
# use -Mode Manifests and rsync the original directories directly (see README_MAC_MIGRATION.md).
#
# The repository copy deliberately keeps .git, untracked files and ignored research files, and
# deliberately excludes .venv, __pycache__ and the JIT/lint caches: those are rebuilt on the Mac.
#
# The copied tracked files carry this machine's CRLF line endings (system-wide core.autocrlf=true)
# in 12 of the 16 production modules, while the committed blobs and the release archive are LF.
# After copying, the Mac MUST re-materialise the working tree from the blobs:
#     git config --local core.autocrlf false && git checkout-index -a -f
# bootstrap_mac.sh does this in step 10b. See README_MAC_MIGRATION.md section 3a.

param(
    [ValidateSet("Report", "Manifests", "Full")] [string]$Mode = "Report",
    [string]$Repo = "C:\Users\epick\Documents\ClaudeShark",
    [string]$DataRoot = "C:\Users\epick\Documents\ClaudeShark-data",
    [string]$Twic = "C:\Users\epick\engines\twic",
    [string]$Out = "C:\Users\epick\Documents\ClaudeShark-Mac-Migration"
)

$ErrorActionPreference = "Stop"

function Measure-Tree($path, $excludeVenv = $false) {
    if (-not (Test-Path $path)) { return [pscustomobject]@{ MB = 0; Files = 0; Missing = $true } }
    $files = Get-ChildItem $path -Recurse -File -Force -ErrorAction SilentlyContinue
    if ($excludeVenv) {
        $files = $files | Where-Object { $_.FullName -notmatch '\\\.venv\\' -and $_.FullName -notmatch '\\__pycache__\\' }
    }
    $m = $files | Measure-Object -Property Length -Sum
    [pscustomobject]@{ MB = [math]::Round($m.Sum / 1MB, 1); Files = $m.Count; Missing = $false }
}

Write-Host "=== sizes ===" -ForegroundColor Cyan
# Local names must not collide with the parameters: PowerShell variables are case-insensitive, so
# a local $twic would overwrite the $Twic parameter and robocopy would be handed an object.
$sizeRepoAll = Measure-Tree $Repo
$sizeRepoNet = Measure-Tree $Repo $true
$sizeData = Measure-Tree $DataRoot
$sizeTwic = Measure-Tree $Twic
"{0,-42} {1,9} MB {2,7} files" -f "repository (everything)", $sizeRepoAll.MB, $sizeRepoAll.Files
"{0,-42} {1,9} MB {2,7} files" -f "repository (transferred: no .venv/pycache)", $sizeRepoNet.MB, $sizeRepoNet.Files
"{0,-42} {1,9} MB {2,7} files" -f "external data (ClaudeShark-data)", $sizeData.MB, $sizeData.Files
"{0,-42} {1,9} MB {2,7} files" -f "TWIC PGN issues", $sizeTwic.MB, $sizeTwic.Files
"{0,-42} {1,9} MB" -f "TRANSFER TOTAL", ($sizeRepoNet.MB + $sizeData.MB + $sizeTwic.MB)
if ($sizeTwic.Missing) { Write-Warning "TWIC source not found at $Twic" }
""

if ($Mode -eq "Report") { Write-Host "Report only; nothing copied." -ForegroundColor Yellow; exit 0 }

New-Item -ItemType Directory -Force -Path $Out, "$Out\manifests", "$Out\bootstrap" | Out-Null

Write-Host "=== manifests and bootstrap ===" -ForegroundColor Cyan
foreach ($f in @("MIGRATION_MAC_MANIFEST.json", "reference_windows.json", "README_MAC_MIGRATION.md",
                 "bootstrap_mac.sh", "verify_mac_port.py", "make_reference.py", "make_manifest.py",
                 "package_for_mac.ps1")) {
    $src = Join-Path $Repo "migration\$f"
    if (Test-Path $src) {
        $dest = if ($f -like "*.json" -or $f -like "*.md") { "$Out\manifests" } else { "$Out\bootstrap" }
        Copy-Item $src $dest -Force
        "  copied $f"
    } else { Write-Warning "  missing $f" }
}
if (-not (Test-Path "$Out\manifests\claudeshark-all-refs.bundle")) {
    Push-Location $Repo; git bundle create "$Out\manifests\claudeshark-all-refs.bundle" --all; Pop-Location
}

if ($Mode -eq "Full") {
    Write-Host "=== repository copy (keeps .git, untracked and ignored research files) ===" -ForegroundColor Cyan
    robocopy $Repo "$Out\repo" /MIR /XD ".venv" "__pycache__" ".pytest_cache" ".ruff_cache" ".mypy_cache" ".numba_cache" /XF "*.pyc" "*.nbi" "*.nbc" /NFL /NDL /NJH /NP /R:1 /W:1 | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed for the repository (exit $LASTEXITCODE)" }
    "  repo -> $Out\repo"
    Write-Host "=== external data copy ===" -ForegroundColor Cyan
    robocopy $DataRoot "$Out\external-data\ClaudeShark-data" /MIR /XD "__pycache__" /XF "*.pyc" /NFL /NDL /NJH /NP /R:1 /W:1 | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed for the external data (exit $LASTEXITCODE)" }
    robocopy $Twic "$Out\external-data\twic" /MIR /NFL /NDL /NJH /NP /R:1 /W:1 | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed for TWIC (exit $LASTEXITCODE)" }
    "  data -> $Out\external-data"
}

Write-Host "=== checksums ===" -ForegroundColor Cyan
$sums = Join-Path $Out "SHA256SUMS.txt"
# -Force is required: .git is a hidden directory, and without it the 1,715 object and ref files
# that carry the unpushed commits would be left out of the integrity check entirely.
Get-ChildItem $Out -Recurse -File -Force | Where-Object { $_.Name -ne "SHA256SUMS.txt" } | ForEach-Object {
    $rel = $_.FullName.Substring($Out.Length + 1).Replace("\", "/")
    "{0}  {1}" -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(), $rel
} | Set-Content -Path $sums -Encoding utf8
"  $((Get-Content $sums | Measure-Object -Line).Lines) entries -> $sums"

$final = Measure-Tree $Out
Write-Host ""
Write-Host ("package at {0}: {1} MB, {2} files" -f $Out, $final.MB, $final.Files) -ForegroundColor Green
Write-Host "Originals are untouched. Verify on the Mac with: shasum -a 256 -c SHA256SUMS.txt" -ForegroundColor Green
