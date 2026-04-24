# Tenant-specific cleanup wrapper for Pejohans
# Update the values below with your Azure DevOps organization and project,
# then execute this script from the repository root.

$OrganizationUrl = "https://dev.azure.com/pejohans"
$ProjectName = "kunskapskontroll_ai_kurs_2"

Write-Host "Running tenant-specific cleanup for $OrganizationUrl" -ForegroundColor Cyan
Write-Host "Project: $ProjectName" -ForegroundColor Cyan
Write-Host ""

.\cleanup-infrastructure.ps1 `
    -OrganizationUrl $OrganizationUrl `
    -ProjectName $ProjectName
