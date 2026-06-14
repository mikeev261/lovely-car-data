# Local Checking Script - DO NOT COMMIT
Write-Host "--- Running Python Schema Checks ---"
# Assuming the same scripts exist in the fork, or just running pre-commit
pre-commit run --all-files

if ($LASTEXITCODE -ne 0) {
    Write-Error "Checks failed! Do not push."
    exit 1
} else {
    Write-Host "All checks passed! Safe to commit and push."
}
