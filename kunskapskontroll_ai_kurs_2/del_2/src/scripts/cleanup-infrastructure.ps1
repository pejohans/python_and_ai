# Infrastructure Teardown Script
# Use this to clean up all resources when done testing

param(
    [Parameter(Mandatory=$true)]
    [string]$OrganizationUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$ProjectName
)

Write-Host "🧹 Starting infrastructure cleanup..."
Write-Host ""

# Configure Azure DevOps
az devops configure --defaults organization=$OrganizationUrl project=$ProjectName

# Delete variable groups
$variableGroups = @("dev-vars", "test-vars", "prod-vars")
foreach ($vg in $variableGroups) {
    Write-Host "Deleting variable group: $vg"
    $vgList = az pipelines variable-group list -o json | ConvertFrom-Json
    $vgObject = $vgList | Where-Object { $_.name -ieq $vg }
    if (-not $vgObject) {
        Write-Host "Variable group '$vg' not found, skipping." -ForegroundColor Yellow
        continue
    }
    az pipelines variable-group delete --id $vgObject.id --yes
}

# Delete environments
$environments = @("dev", "test", "prod")
foreach ($env in $environments) {
    Write-Host "Deleting environment: $env"
    try {
        # Get environment ID
        $envList = az devops invoke `
            --area distributedtask `
            --resource environments `
            --route-parameters project=$ProjectName `
            --http-method GET `
            --query "value[?name=='$env'].id" -o tsv 2>$null

        if ([string]::IsNullOrEmpty($envList)) {
            Write-Host "Environment '$env' not found, skipping." -ForegroundColor Yellow
            continue
        }

        # Delete environment using REST API
        $result = az devops invoke `
            --area distributedtask `
            --resource environments `
            --route-parameters project=$ProjectName environmentId=$envList `
            --http-method DELETE `
            --query "name" -o tsv 2>$null

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Environment '$env' deleted successfully"
        } else {
            Write-Host "⚠️  Environment '$env' deletion failed. Delete manually in Azure DevOps UI if needed." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Environment deletion failed. Delete manually in Azure DevOps UI if needed." -ForegroundColor Yellow
    }
}

# Delete service connections
$serviceConnections = @("Azure-Subscription-dev-ai", "Azure-Subscription-test-ai", "Azure-Subscription-prod-ai")
foreach ($sc in $serviceConnections) {
    Write-Host "Deleting service connection: $sc"
    $endpointList = az devops service-endpoint list -o json | ConvertFrom-Json
    $endpoint = $endpointList | Where-Object { $_.name -ieq $sc }
    if (-not $endpoint) {
        Write-Host "Service connection '$sc' not found, skipping." -ForegroundColor Yellow
        continue
    }
    az devops service-endpoint delete --id $endpoint.id --yes
}

# Delete Azure resource groups (WARNING: This deletes all resources!)
$resourceGroups = @("rg-kunskapskontroll-ai-kurs-2-dev", "rg-kunskapskontroll-ai-kurs-2-test", "rg-kunskapskontroll-ai-kurs-2-prod")
foreach ($rg in $resourceGroups) {
    Write-Host "Deleting resource group: $rg (this will delete all resources!)"
    $exists = az group exists --name $rg
    if ($exists -ne 'true') {
        Write-Host "Resource group '$rg' not found, skipping." -ForegroundColor Yellow
        continue
    }
    az group delete --name $rg --yes --no-wait
}

Write-Host ""
Write-Host "🗑️ Cleanup complete!"
Write-Host ""
Write-Host "Deleted resources:"
Write-Host "- Variable groups: dev-vars, test-vars, prod-vars"
Write-Host "- Environments: dev, test, prod"
Write-Host "- Service connections: Azure-Subscription-dev-ai, Azure-Subscription-test-ai, Azure-Subscription-prod-ai"
Write-Host "- Resource groups: rg-kunskapskontroll-ai-kurs-2-dev, rg-kunskapskontroll-ai-kurs-2-test, rg-kunskapskontroll-ai-kurs-2-prod"