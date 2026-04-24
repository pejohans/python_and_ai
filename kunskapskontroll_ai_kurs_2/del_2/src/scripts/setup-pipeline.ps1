# Azure DevOps Pipeline Setup Script
# Creates the CI/CD pipeline from your azure-pipelines.yml

param(
    [Parameter(Mandatory=$true)]
    [string]$OrganizationUrl,

    [Parameter(Mandatory=$true)]
    [string]$ProjectName,

    [Parameter(Mandatory=$true)]
    [string]$RepositoryUrl
)

Write-Host "Setting up CI/CD pipeline..."

# Configure Azure DevOps
az devops configure --defaults organization=$OrganizationUrl project=$ProjectName

# Create pipeline from YAML
az pipelines create `
    --name "$ProjectName-CICD" `
    --description "CI/CD pipeline for $ProjectName project" `
    --repository $RepositoryUrl `
    --repository-type github `
    --branch main `
    --yml-path azure-pipelines.yml

Write-Host "✅ Pipeline created successfully!"
Write-Host ""
Write-Host "Pipeline details:"
Write-Host "- Name: $ProjectName-CICD"
Write-Host "- Repository: $RepositoryUrl"
Write-Host "- Branch: main"
Write-Host "- YAML: azure-pipelines.yml"