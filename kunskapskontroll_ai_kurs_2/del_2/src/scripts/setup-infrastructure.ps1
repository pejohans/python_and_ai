# Azure DevOps Infrastructure as Code Setup
# This script sets up all Azure DevOps resources using Infrastructure as Code principles

param(
    [Parameter(Mandatory=$true)]
    [string]$OrganizationUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$ProjectName,
    
    [Parameter(Mandatory=$true)]
    [string]$AzureSubscriptionId,
    
    [Parameter(Mandatory=$true)]
    [string]$AzureSubscriptionName,
    
    [Parameter(Mandatory=$true)]
    [string]$AzureTenantId,
    
    [string]$Location = "Sweden Central"
)

# Ensure Azure CLI and Azure DevOps extension are available
Write-Host "Checking prerequisites..."
if (!(Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI is not installed. Please install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
}

az extension add --name azure-devops --upgrade --yes

# Login and configure
Write-Host "Authenticating with Azure DevOps..."
Write-Host "Note: You may need to authenticate interactively. If prompted, use your Azure DevOps credentials or a Personal Access Token."

# Try to login - this may require interactive authentication
try {
    az devops login 2>$null
} catch {
    Write-Warning "Interactive login failed. Please ensure you're authenticated with Azure DevOps."
    Write-Host "You can authenticate manually by running: az devops login"
    Write-Host "Or create a Personal Access Token and set it as an environment variable: AZURE_DEVOPS_EXT_PAT"
}

az devops configure --defaults organization=$OrganizationUrl project=$ProjectName

# Verify authentication
Write-Host "Verifying Azure DevOps authentication..."
try {
    az devops project show --project $ProjectName --query "name" -o tsv | Out-Null
    Write-Host "✅ Azure DevOps authentication successful"
} catch {
    Write-Error "Azure DevOps authentication failed. Please run 'az devops login' manually and try again."
    exit 1
}

# Create variable groups with proper structure
$variableGroups = @(
    @{
        Name = "dev-vars"
        Variables = @{
            "location" = $Location
            "resourceGroupName" = "rg-kunskapskontroll-ai-kurs-2-dev"
            "functionAppName" = "func-nightly-pipeline-dev"
            "azureServiceConnection" = "Azure-Subscription-dev-ai"
        }
    },
    @{
        Name = "test-vars"
        Variables = @{
            "location" = $Location
            "resourceGroupName" = "rg-kunskapskontroll-ai-kurs-2-test"
            "functionAppName" = "func-nightly-pipeline-test"
            "azureServiceConnection" = "Azure-Subscription-test-ai"

        }
    },
    @{
        Name = "prod-vars"
        Variables = @{
            "location" = $Location
            "resourceGroupName" = "rg-kunskapskontroll-ai-kurs-2-prod"
            "functionAppName" = "func-nightly-pipeline-prod"
            "azureServiceConnection" = "Azure-Subscription-prod-ai"
        }
    }
)

foreach ($vg in $variableGroups) {
    Write-Host "Creating variable group: $($vg.Name)"
    $varString = ($vg.Variables.GetEnumerator() | ForEach-Object { "$($_.Key)='$($_.Value)'" }) -join " "
    Invoke-Expression "az pipelines variable-group create --name '$($vg.Name)' --variables $varString"
}

# Create environments
Write-Host "Creating environments via REST API..."
Write-Host ""

$environments = @("dev", "test", "prod")
foreach ($env in $environments) {
    Write-Host "Creating environment: $env"

    try {
        # Create environment using REST API
        $envBody = @{
            name = $env
            description = "Environment for $env deployment"
        } | ConvertTo-Json -Compress

        # Write JSON to temp file
        $tempFile = [System.IO.Path]::GetTempFileName()
        #$envBody | Out-File -FilePath $tempFile -Encoding UTF8
        [System.IO.File]::WriteAllText($tempFile, $envBody, (New-Object System.Text.UTF8Encoding($false)))

        Write-Host "  Invoking DevOps API..."
        $result = az devops invoke `
            --area distributedtask `
            --resource environments `
            --route-parameters "project=$ProjectName" `
            --http-method POST `
            --in-file $tempFile `
            --query "name" -o tsv

        # Clean up temp file
        Remove-Item $tempFile -ErrorAction SilentlyContinue

        if ($LASTEXITCODE -eq 0 -and $result) {
            Write-Host "✅ Environment '$env' created successfully"
        } else {
            Write-Warning "Could not create environment '$env' via REST API"
            if ($result) {
                Write-Host "  Response: $result" -ForegroundColor Yellow
            }
            Write-Host "  Please create it manually in Azure DevOps:" -ForegroundColor Yellow
            Write-Host "  Go to Pipelines → Environments → + New environment → Name: $env" -ForegroundColor Yellow
        }
    } catch {
        Write-Warning "Could not create environment '$env'. Error: $_"
        Write-Host "  Please create it manually in Azure DevOps:" -ForegroundColor Yellow
        Write-Host "  Go to Pipelines → Environments → + New environment → Name: $env" -ForegroundColor Yellow
    }
}

# Create service connections
Write-Host "Note: Service connections require service principals. Creating them now..."
Write-Host ""

$serviceConnections = @("dev-ai", "test-ai", "prod-ai")
foreach ($sc in $serviceConnections) {
    Write-Host "Creating service principal and connection: Azure-Subscription-$sc"

    try {
        # Create service principal
        $spName = "AzureDevOps-SP-$sc"
        Write-Host "  Creating service principal: $spName"
        $sp = az ad sp create-for-rbac --name $spName --role contributor --scopes "/subscriptions/$AzureSubscriptionId" --query "{appId:appId,password:password}" | ConvertFrom-Json
        
        if (-not $sp.appId) {
            throw "Failed to create service principal - appId is empty"
        }
        
        Write-Host "  Service principal created with appId: $($sp.appId)"

        # Create service connection using the service principal
        # The password/key must be provided via environment variable per Azure CLI requirements
        Write-Host "  Creating service connection..."
        $env:AZURE_DEVOPS_EXT_AZURE_RM_SERVICE_PRINCIPAL_KEY = $sp.password
        
        az devops service-endpoint azurerm create `
            --name "Azure-Subscription-$sc" `
            --azure-rm-service-principal-id $sp.appId `
            --azure-rm-subscription-id $AzureSubscriptionId `
            --azure-rm-subscription-name $AzureSubscriptionName `
            --azure-rm-tenant-id $AzureTenantId

        # Clear the environment variable
        Remove-Item env:AZURE_DEVOPS_EXT_AZURE_RM_SERVICE_PRINCIPAL_KEY -ErrorAction SilentlyContinue

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Service connection 'Azure-Subscription-$sc' created successfully"
        } else {
            throw "Service endpoint creation failed with exit code: $LASTEXITCODE"
        }
    } catch {
        Write-Warning "Could not create service connection '$sc' automatically."
        Write-Host "Error: $_" -ForegroundColor Yellow
        Write-Host "Please create it manually in Azure DevOps:" -ForegroundColor Yellow
        Write-Host "  Go to Project Settings → Service connections → New service connection → Azure Resource Manager" -ForegroundColor Yellow
        Write-Host "  Select 'Service principal (automatic)' and choose resource group 'rg-localad-$sc'" -ForegroundColor Yellow
    }
}

# Create Azure resource groups
$resourceGroups = @("rg-kunskapskontroll-ai-kurs-2-dev", "rg-kunskapskontroll-ai-kurs-2-test", "rg-kunskapskontroll-ai-kurs-2-prod")
foreach ($rg in $resourceGroups) {
    Write-Host "Creating resource group: $rg"
    az group create --name $rg --location $Location
}

Write-Host ""
Write-Host "🎉 Infrastructure setup complete!"
Write-Host ""
Write-Host "✅ Created resources:"
Write-Host "   - Variable groups: dev-vars, test-vars, prod-vars"
Write-Host "   - Environments: dev, test, prod (attempted via REST API)"
Write-Host "   - Service connections: Azure-Subscription-dev, Azure-Subscription-test, Azure-Subscription-prod"
Write-Host "   - Resource groups: rg-localad-dev, rg-localad-test, rg-localad-prod"
Write-Host ""
Write-Host "⚠️  If environment creation failed:"
Write-Host "   - Create environments manually in Azure DevOps web UI"
Write-Host "   - Go to Pipelines → Environments → + New environment"
Write-Host ""
Write-Host "Next: Push code and create pipeline in Azure DevOps"