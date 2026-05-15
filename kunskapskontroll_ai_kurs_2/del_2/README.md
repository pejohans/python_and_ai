## Inledning
I denna fil beskrivs repo-strukturen för det AI Ticker-system som är byggt.
Lösningen består av flera delar:
1. Ett FastAPI (skriven in Python) som klienter kan ställa frågor mot för att få en prediktion för en aktie. Själva Api:et läser upp en redan tränad modell (från blob storage)
för att snabbt kunna göra en prediktion och skicka tillbaka ett svar till användaren.

2. Azure funktion (skriven i Python) som körs varje natt för att hämta data och träna modellen

3. Skript - Det finns ett antal PowerShell skript som man kör igång lokalt. 
Dessa skript kopplar upp sig mot min Azure tenant (behövs dock en token för att få behörighet) och skapar upp vissa förutsättningar i både Azure och AzureDevOps så att den pipeline som också skapas av skriptet kan köras. Så,
det är lite av en tvåstegs-raket skulle man kunna säga innan allt är uppe och rullar. Du ser nedan i repo-strukturen där vi både har scripts, infra, pipelines och tools-kataloger som alla kommer i spel när man kör igång 
PowerShell-skriptet setup-all.ps1

## Repo-struktur
- `src/api/` – FastAPI inference API (containeriserad)
- `src/functions/` – Azure Functions (Python v2 model) timer-trigger pipeline
- `src/infra/bicep/` – Bicep för Storage + ACR + Container Apps + Function App + RBAC
- `src/infra/bicep/environments` - Innehåller json-filer för specifika parametrar beroende på vilken miljö man deployar till, dev/test eller prod
- `src/pipelines/azure-pipelines.yml` – CI/CD (infra + api + functions + bootstrap)
- `tools/bootstrap_model.py` – skapar initial modell/artefakter lokalt för uppladdning
- `src/scripts` – Innehåller PowerShell-skript som deployar hela lösningen till Azure. Både infrastruktur och kod samt den Azure DevOps pipeline som 
deployar själva lösningen till Azure. Dvs. Först skapar vi upp förutsättningarna i Azure (infrastrukturen) för att sedan kunna deploya själva lösningen med FastAPI appen, Azure Funktionen för att hämta data och träna modellen osv.

## Deploy
1. Gå till katalogen src/scripts
2. Kör filen setup-all.ps1
2:1. Denna fil förväntar sig x antal parametrar, därav har jag skapat filen pejohans-setup-all.ps1 med just mina inställningar för min tenant. Man kan dock enkelt skapa en ny sådan fil för en annan Azure tenant för att deploya på en helt annan Azure Tenant, t ex för en kund. 
3. När du kör filen setup-all.ps1 så förväntar sig den en Token för att köra vidare. Denna token behöver man generera i Azure DevOps
4. Efter att skriptet kört klart så kommer det finnas:
4:1. 3 resursgrupper i Azure
4:2. Ett container registry
4:3. En DevOps pipeline
4:4. X antal beroenden till DevOps pipeline som Service Connections, variabler och environments som behövs för att pipeline ska kunna koppla upp sig och fortsätta deploya lösningen till Azure. 