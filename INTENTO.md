**Fase:** B — Punto della situazione sul codice
**Ultima cosa fatta:** messo in sicurezza il VPS (Fase A completata: SSH, firewall, code-server non-root, key EODHD ruotata)
**Prossimo passo:** analizzare il repo trading con Claude Code in SOLA LETTURA (vedi §15 del manuale)
**Domande aperte:** FMP API key forse leakata (da verificare); auth FastAPI ancora mancante
**Assistente ultima sessione:** Claude (chat)
**Prossimo passo:** Fase B in sola lettura — quale dashboard è viva (app/ vs dashboard/), quale DB reale, core src/ riusabile?
**Domande aperte:** piano API FastAPI di Kimi pronto ma SOSPESO fino a fine Fase B; alla ripresa correggere porta (≠8000, occupata da trading-brain), confermare dashboard e DB
**Fase:** C — Backend, fetta verticale fatta. Decisione: espandere o no?
**Ultima cosa fatta:** API /health + /api/v1/stocks verificata (dati reali SQLite, porta 8001), committata e pushata (8024274)
**Prossimo passo:** decidere se l'API serve davvero — esiste un Angular che la consuma? Se no, fermarsi qui e non costruire altri endpoint
**Domande aperte:** Angular esiste? ; import core stile vecchio (database.database) = debito noto, non bloccante
