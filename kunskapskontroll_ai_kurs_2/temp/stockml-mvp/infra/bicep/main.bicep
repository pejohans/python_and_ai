
targetScope = 'resourceGroup'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Base name/prefix for resources (lowercase, letters+numbers)')
param namePrefix string = 'stockml'

@description('Blob container name for data/model storage')
param blobContainerName string = 'stockml'

@description('Container App name for inference API')
param apiAppName string = '${namePrefix}-api'

@description('Container App Environment name')
param acaEnvName string = '${namePrefix}-acaenv'

@description('Azure Container Registry name (must be globally unique)')
param acrName string

@description('Azure Function App name (must be globally unique)')
param functionAppName string

@description('Storage account name (must be globally unique)')
param storageAccountName string

@description('OMX30 symbols, comma-separated')
param omx30Symbols string = 'ERIC-B,VOLV-B,ATCO-A,ATCO-B,SAND,SEB-A,SWED-A,SHB-A,NDA-SE,TELIA'

@description('Timer schedule NCRONTAB 6-field format. Default 01:00 UTC daily')
param timerSchedule string = '0 0 1 * * *'

// Log Analytics
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${namePrefix}-logs'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

// Storage account
resource stg 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    accessTier: 'Hot'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2022-09-01' = {
  name: 'default'
  parent: stg
}

resource dataContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-09-01' = {
  name: blobContainerName
  parent: blobService
  properties: {
    publicAccess: 'None'
  }
}

// ACR
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: acrName
  location: location
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: true
  }
}

// Container Apps Environment
resource acaEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: acaEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// Container App (FastAPI)
resource api 'Microsoft.App/containerApps@2023-05-01' = {
  name: apiAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: acaEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: acr.properties.loginServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-pwd'
        }
      ]
      secrets: [
        {
          name: 'acr-pwd'
          value: acr.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: '${acr.properties.loginServer}/${namePrefix}-api:bootstrap'
          env: [
            { name: 'STORAGE_ACCOUNT_NAME', value: storageAccountName }
            { name: 'BLOB_CONTAINER_NAME', value: blobContainerName }
            { name: 'FEATURES_PATH_PREFIX', value: 'curated/omx30/features/horizon=7' }
            { name: 'MODELS_PATH_PREFIX', value: 'models/omx30/horizon=7' }
            { name: 'HORIZON_DAYS', value: '7' }
            { name: 'OMX30_SYMBOLS', value: omx30Symbols }
          ]
          resources: {
            cpu: 0.5
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 2
      }
    }
  }
}

// Function App (Linux Consumption) + Managed Identity
resource funcPlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${namePrefix}-funcplan'
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  kind: 'functionapp'
}

resource funcApp 'Microsoft.Web/sites@2022-03-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: funcPlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'AzureWebJobsStorage', value: stg.listKeys().keys[0].value }
        { name: 'STORAGE_ACCOUNT_NAME', value: storageAccountName }
        { name: 'BLOB_CONTAINER_NAME', value: blobContainerName }
        { name: 'FEATURES_PATH_PREFIX', value: 'curated/omx30/features/horizon=7' }
        { name: 'TRAINSET_PATH_PREFIX', value: 'curated/omx30/trainset/horizon=7' }
        { name: 'MODELS_PATH_PREFIX', value: 'models/omx30/horizon=7' }
        { name: 'HORIZON_DAYS', value: '7' }
        { name: 'OMX30_SYMBOLS', value: omx30Symbols }
        { name: 'TIMER_SCHEDULE', value: timerSchedule }
      ]
    }
  }
}

// RBAC role assignments (Storage Blob Data Reader/Contributor)
resource storageBlobDataReader 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: subscription()
  name: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1' // Storage Blob Data Reader
}

resource storageBlobDataContributor 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: subscription()
  name: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe' // Storage Blob Data Contributor
}

resource apiBlobReaderAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, api.id, storageBlobDataReader.id)
  scope: stg
  properties: {
    principalId: api.identity.principalId
    roleDefinitionId: storageBlobDataReader.id
    principalType: 'ServicePrincipal'
  }
}

resource funcBlobContributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, funcApp.id, storageBlobDataContributor.id)
  scope: stg
  properties: {
    principalId: funcApp.identity.principalId
    roleDefinitionId: storageBlobDataContributor.id
    principalType: 'ServicePrincipal'
  }
}

output containerAppName string = api.name
output containerAppFqdn string = api.properties.configuration.ingress.fqdn
output functionAppName string = funcApp.name
output acrLoginServer string = acr.properties.loginServer
output storageAccountName string = stg.name
output blobContainerName string = blobContainerName
