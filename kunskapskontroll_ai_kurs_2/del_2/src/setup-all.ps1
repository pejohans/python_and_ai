# Complete Infrastructure Setup Script
# Run this to set up everything from scratch

param(
    [Parameter(Mandatory=$true)]
    [string]$OrganizationUrl = "",  # e.g., "https://dev.azure.com/your-org"
    
    [Parameter(Mandatory=$true)]
    [string]$ProjectName = "",      
    
    [Parameter(Mandatory=$true)]
    [string]$RepositoryUrl = "",   
    
    [Parameter(Mandatory=$true)]
    [string]$AzureSubscriptionId = "",
    
    [Parameter(Mandatory=$true)]
    [string]$AzureSubscriptionName = "",
    
    [Parameter(Mandatory=$true)]
    [string]$AzureTenantId = "",
    
    [string]$Location = "Sweden Central"
)

Write-Host "🚀 Starting complete infrastructure setup..."
Write-Host ""

# Run infrastructure setup
Write-Host "Step 1: Setting up Azure DevOps infrastructure..."
& ".\setup-infrastructure.ps1" `
    -OrganizationUrl $OrganizationUrl `
    -ProjectName $ProjectName `
    -AzureSubscriptionId $AzureSubscriptionId `
    -AzureSubscriptionName $AzureSubscriptionName `
    -AzureTenantId $AzureTenantId `
    -Location $Location

Write-Host ""
Write-Host "Step 2: Creating CI/CD pipeline..."
& ".\setup-pipeline.ps1" `
    -OrganizationUrl $OrganizationUrl `
    -ProjectName $ProjectName `
    -RepositoryUrl $RepositoryUrl

Write-Host ""
Write-Host "🎉 Complete setup finished!"
Write-Host ""
Write-Host "Ready to deploy:"
Write-Host "1. Push your code to the main branch"
Write-Host "2. Run the pipeline with targetEnvironment=dev"
Write-Host "3. Verify resources in Azure Portal"
Write-Host "4. Promote to test/prod as needed"