
# StockML MVP (OMX30) – Azure Container Apps + Azure Functions + Blob Storage

Det här repot är en **deploy-redo MVP** för din idé:
- **Azure Function (Timer Trigger)** kör nattligt och **precomputar features** + tränar en **7-dagars modell**.
- **Azure Container App (FastAPI)** exponerar ett **/predict** API som Android-appen kan anropa.
- **Azure Blob Storage** är single source of truth för `/raw`, `/curated` och `/models`.
- **Bicep + Azure DevOps Pipeline** provisionerar och deployar.

> ⚠️ OBS: Funktionen innehåller en *bootstrap*-väg som skapar en första baseline-modell om det inte finns någon modell i Blob ännu.
> Den är avsedd för att få en fungerande end-to-end-deploy direkt. Byt sedan datakällor/featurelogik till riktiga källor.

## Repo-struktur
- `src/api/` – FastAPI inference API (containeriserad)
- `src/functions/` – Azure Functions (Python v2 model) timer-trigger pipeline
- `infra/bicep/` – Bicep för Storage + ACR + Container Apps + Function App + RBAC
- `pipelines/azure-pipelines.yml` – CI/CD (infra + api + functions + bootstrap)
- `tools/bootstrap_model.py` – skapar initial modell/artefakter lokalt för uppladdning

## Lokalt (snabbtest)
### API
```bash
cd src/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Functions (lokalt)
För lokal körning krävs Azure Functions Core Tools.
```bash
cd src/functions
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
func start
```

## Deployment (Azure DevOps)
1. Skapa en Azure Resource Manager service connection i Azure DevOps.
2. Sätt pipeline-variabler (se `pipelines/azure-pipelines.yml`).
3. Kör pipeline. Den:
   - Deployar infra via Bicep
   - Bygger och deployar API:t till Container Apps
   - Packar och deployar Functions
   - Bootstrapp: laddar upp initial modell + tomma mappar

## Konfiguration
All runtime-konfig är via **App Settings / env vars** i Function App och Container App:
- `STORAGE_ACCOUNT_NAME`
- `BLOB_CONTAINER_NAME` (default `stockml`)
- `FEATURES_PATH_PREFIX` (default `curated/omx30/features/horizon=7`)
- `MODELS_PATH_PREFIX` (default `models/omx30/horizon=7`)
- `OMX30_SYMBOLS` (comma-separated)
- `TIMER_SCHEDULE` (t.ex. `0 0 1 * * *` = 01:00 UTC varje dag)

Lycka till – och säg till om du vill att jag även genererar en CAF-style arkitekturdiagram eller en Android-klientmall.
