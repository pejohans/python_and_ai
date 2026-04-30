# Tenant-specific setup wrapper for Pejohans
# Update the values below with your actual Azure DevOps and Azure subscription settings,
# then execute this script from the repository root.

$OrganizationUrl = "https://dev.azure.com/pejohans"
$ProjectName = "kunskapskontroll_ai_kurs_2"
$RepositoryUrl = "pejohans/python_and_ai"
$AzureSubscriptionId = "3a369e7b-d227-4230-8129-7f490c05a663"
$AzureSubscriptionName = "Visual Studio Premium med MSDN"
$AzureTenantId = "b52ca394-3243-4498-ae53-64327da47493"
$Location = "swedencentral"

Write-Host "Running tenant-specific setup for $OrganizationUrl" -ForegroundColor Cyan
Write-Host "Project: $ProjectName" -ForegroundColor Cyan
Write-Host "Subscription: $AzureSubscriptionName ($AzureSubscriptionId)" -ForegroundColor Cyan
Write-Host "Tenant: $AzureTenantId" -ForegroundColor Cyan
Write-Host "Location: $Location" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANT: You will be prompted to authenticate with Azure DevOps" -ForegroundColor Yellow
Write-Host "   Use your Azure DevOps credentials or a Personal Access Token" -ForegroundColor Yellow
Write-Host ""

.\setup-all.ps1 `
    -OrganizationUrl $OrganizationUrl `
    -ProjectName $ProjectName `
    -RepositoryUrl $RepositoryUrl `
    -AzureSubscriptionId $AzureSubscriptionId `
    -AzureSubscriptionName $AzureSubscriptionName `
    -AzureTenantId $AzureTenantId `
    -Location $Location
