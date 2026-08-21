# Reflektionsdokument – obligatorisk leverabel

1. Varför ska sensorerna kommunicera med ett API i stället för direkt med PostgreSQL?
    Ett API fungerar som ett kontrollerande lager mellan sersorerna och databasen. Det ger ger möjlighet att validera både avsändaren och datat innan något sparas i databasen eller cachen. Det minskar också exponeringen av databasen utåt vilket ökar säkerheten. Man har möjlighet att hantera och logga felaktiga
    mätningar utan att det blandas med korrekt data i databasen 

2. Varför ska felaktig sensordata stoppas innan den sparas?
    Man vill inte spara fel meddelanden och invalid data med övrig korrekt data, i detta fall mätvärden då det kan skapa felaktigheter när datan skall hämtas och analyseras. I projektet valideras därför data innan det skciaks vidare till PostgreSQL
3. Varför passar PostgreSQL för historiska mätvärden?
    I Labben består datat av tydligt strukturerade data vilket lämpar sig väl för en relationsdatabas. Det är enkelt att lagra all data och att hämta samtlig eller specifik data senare, expelvis för individuel sensor. 
4. Vad händer med lösningen om Redis försvinner?
    Redis används endast som cache. Cachen inehåller bara en kopia av enheternas senaste mätvärde för snabb åtkomst. Den permanenta datan finns fortfarande i PostgreSQL så om Redis försvinner kan APIet fortfarande kämta data men om man bara vill ha det senaste värdet so blir det en lkad belastning på databasen.  
5. Vad händer med lösningen om PostgreSQL försvinner?
    PostgreSQL är projektets persistant lagring och single sorce of trurh. Om databadsen försvinner tappar vi möjligheten att hämta historisk data samt ta fram statistik över tid. Vi skulle med hjälp av cachen kunna se de aktuella värderna men inget annat då de skrivs över efter varje godkänd mätnin. 
6. Varför används Docker Compose lokalt?
    Docker compose används för att enkelt kunna starta och köra systemets olika tjänster samtidigt. I detta projekt så hanterar Docker Compose API, POstgreSQL, Redis samt våra simulerade sensorer. Det gör också utväcklingsmiljön enklare att återskapa eftersom tjänster och deras konfiguration startas på samma sätt väarje gång.  
7. Vad automatiserar din CI-pipeline?
    CI-piplelinen körs automatiskt vid push/pull requests. Den checkar ut APi beroenden, kör pytest testerna och om allt är godkänt så byggs Docker image för APIet. Det gör det möjlighet att upptäcka fel tidigt och eller validera att aplikationen går att bygga. 
8. Vad observerade du när du tog bort en Kubernetes Pod?
    Jag observerade att poden termineras och en ny pod automatiskt skapas. Konfigurationen anger antal poddar som ska köras (i detta fall 3). Kubernetes kontrollerar kontinuerligt av antal poddar som körs och skapar automatiskt en ny pod om en en försvinner.Detta är ett exempel på så kallad self-healing. 
9. Varför kan flera repliker ge högre tillgänglighet?
    I och med att det finns flera repliker (podar) som kör samma tjänst så kan de andra poddarna hantera trafiken om en pod går ner medans Kubernetes startar upp en ny pod. Det gör att ett fel i en enskild pod inte gör att hela APIet blir otillgängligt.
10. När hade Kubernetes varit overkill för en lösning?
    Kubernetes blir overkill näör du inte har höga krav på tillgänglighet, låg trafik och får tjänster som ska hanteras. Om man till exempel kan köra hela systemet med Docker compose kan Kubernetes inebärrra mer komplexitet än nödvändigt. 

Spara svaren i denna fil. Arkitekturdiagrammet lämnas separat enligt `docs/architecture.md`.
