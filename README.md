# AI DM Discord bot

Ez a projekt egy AI-alapú Dungeon Master (DM) bot Discordhoz. A bot a discord.py-t használja, helyi SQLite perzisztenciát, és LLM-integrációt (alapértelmezett: Gemini, opcionálisan Ollama) a narratív és játékmenet vezérléséhez.

Röviden: a main.py indítja a környezetet, az app/bootstrap.py összerakja a RuntimeContainer-t (repository-k, service-ek, LLM adapterek, event bus), és a bot/bot_core.py-vel történik a Discord-üzenetek és parancsok kezelése.

Főbb lépések a futtatáshoz

1) Virtuális környezet létrehozása és aktiválása

- Unix / macOS:
  python -m venv venv
  source venv/bin/activate

- Windows (PowerShell):
  python -m venv venv
  .\venv\Scripts\Activate.ps1

2) Függőségek telepítése

pip install -r requirements.txt

3) Környezeti változók (.env fájl):

- DISCORD_TOKEN (kötelező)
- (opcionális) DISCORD_COMMAND_PREFIX, AI_DM_DATABASE_FILE, GEMINI_API_KEYS, LLM_ENABLE_OLLAMA_FALLBACK, OLLAMA_BASE_URL, OLLAMA_MODEL, AI_DM_LOG_LEVEL, AI_DM_LOG_FILE

Példa .env:

DISCORD_TOKEN=your_token_here
GEMINI_API_KEYS=key1,key2

4) Indítás

python main.py

Megjegyzések
- A működő Discord-bot logikája a bot/bot_core.py alatt található. A repó gyökerében korábban volt egy régebbi bot_core.py; azt a refaktor során a legacy/ mappába helyeztük át.
- A projekt komplex LLM- és perzisztencia-wiringet tartalmaz. Ha további, LLM-hez kapcsolódó függőségek szükségesek, frissíteni fogjuk a requirements.txt-t.

Contributing / Fejlesztés
- Hozd létre a saját branch-ed (pl. feature/x), teszteld és küldj PR-t a main felé.

License
- Nincs explicit licenc fájl — ha szeretnéd, hozzáadok egyet (pl. MIT).