## Inledning
Detta är ett system för att predikera ett tänkt pris-spann för en aktie. Det är aldrig tänkt att försöka pricka exakta aktiepriser då det är näst intill omöjligt med tanke på alla de variabler som kan påverka en akties pris. Detta är också en första version, en MVP för att ge användare av systemet en indikation om vart en aktie är påväg och inom vilket pris-spann en aktie kan tänkas landa om 7 dagar. En vekas tid är inte lång tid vilket betyder att mer tekniska variabler har större betydelse än mer långsiktiga variabler såsom analytikers rekommendationer, bolagsrapporter och sentiment samt icke att förglömma omvärldsbevakning. 
Du hittar mer detaljerad information i den EDA som också finns att tillgå i jypiter-filen analys.ipynb.


Lösningen består av flera delar:
1. Ett FastAPI (skriven in Python) som klienter kan ställa frågor mot för att få en prediktion för en aktie. Själva Api:et läser upp en redan tränad modell (från blob storage)
för att snabbt kunna göra en prediktion och skicka tillbaka ett svar till användaren.

2. Azure funktion (skriven i Python) som körs varje natt för att hämta data och träna modellen

3. Skript - Det finns ett antal PowerShell skript som man kör igång lokalt. 
Dessa skript kopplar upp sig mot min Azure tenant (behövs dock en token för att få behörighet) och skapar upp vissa förutsättningar i både Azure och AzureDevOps så att den pipeline som också skapas av skriptet kan köras. Så,
det är lite av en tvåstegs-raket skulle man kunna säga innan allt är uppe och rullar. Du ser nedan i repo-strukturen där vi både har scripts, infra, pipelines och tools-kataloger som alla kommer i spel när man kör igång 
PowerShell-skriptet setup-all.ps1

## Signifikanta delar/komponenter
1. Analys.ipynb - Denna del innehåller min EDA för AI Ticker systemet
2. src/api/app/main.py - Denna komponent är den app (FastAPI) som tar emot en aktie och tidshorisont för att göra en prediktion. 
3. src/api/app/feature_loader.py - Ansvarig för att ladda våra features
4. src/api/app/model_loader.py - Ansvarig för att ladda upp vår tränade modell
5. src/functions/function_app.py - Azure function som körs varje natt kl. 01:00
6. src/functions/stockml_pipeline/pipeline.py - Från vår Azure function (function_app.py) anropar vi vår pipeline som är ansvarig för att coordinera feature engineering, träning och att spara undan vår modell för att från vår app kunna läsa upp modellen och genomföra predikeringar. 
7. src/functions/stockml_pipeline/training.py - Ansvarig för att träna vår modell på data från yfinance (fungerar ej just nu så alternativ källa behövs.)
8. src/functions/stockml_pipeline/feature_engineering.py - Ansvarig för att bygga ihop och returnera våra features.

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

5. Gå till Azure DevOps för din tenant och kör igång pipeline 
5:1. Gå till projektet kunskapskontroll_ai_kurs_2 och klicka på Pipelines
5:2. Klicka på pipeline kunskapskontroll_ai_kurs_2-CICD
5:3. Pipeline skall i detta läge redan ha startat men väntar på behörigheter till din Azure Tenant så att den kan börja skapa artefakter som t ex Azure functions, FastAPI container app, storage accounts osv. 


## Undeploy
1. Gå till katalogen src/scripts
2. Kör filen pejohans-cleanup-all.ps1
3. Efter att skriptet är klart så kommer det ta en stund innan alla artefakter och resurser i Azure och Azure DevOps är borttagna.
4. Pipeline kunskapskontroll_ai_kurs_2-CICD tas idag bort manuellt i Azure DevOps portalen.


## Front-end
Denna ligger i ett annat repo eftersom man inte ska blanda front-end med back-end, på detta vis håller man det rent och enkelt vid deploy.

# Förkrav
Installera node version manager (nvm), detta är rekommenderat för att hålla isär olika node-versioner för olika miljöer.

Använd korrekt node-version genom att köra följande kommandon.
- nvm install 22.12.0
- nvm use 22.12.0


1. Gå till repo https://github.com/pejohans/ai_ticker_fe
2. Clona projektet och öppna i visual studio code
3. Kör igång front-end genom att i terminalen köra "npm run dev"