# Streamlit Cloud Secrets Setup

## 🔐 Configurazione Autenticazione su Streamlit Cloud

Questo progetto usa **streamlit-authenticator** per proteggere l'accesso all'applicazione.

### Step 1: Accedi a Streamlit Cloud Dashboard

1. Vai su https://share.streamlit.io/
2. Seleziona la tua app "dividend-recovery-system"
3. Clicca su **Settings** (⚙️) → **Secrets**

### Step 2: Copia il Contenuto dei Secrets

Copia e incolla il seguente contenuto nel campo "Secrets" su Streamlit Cloud:

```toml
# Streamlit Authentication Secrets

# Configurazione autenticazione
[credentials]

  [credentials.usernames.maxdany]
  name = "Max Dany"
  password = "$2b$12$rGscnH3/qFK6GA8ZPwl5JOQLJ8M6ZUQ9TH7VRDM9Of30JDMssw30W"

# Cookie configuration
cookie_name = "dividend_recovery_auth"
cookie_key = "746d6fa00a86627481a7648b9174310ebf2b4e37955d7b660e7c1c3546d8f488"
cookie_expiry_days = 30

# Preauthorized users (opzionale - per future registrazioni)
preauthorized = []
```

### Step 3: Salva e Riavvia

1. Clicca su **Save**
2. L'app si riavvierà automaticamente
3. Al prossimo accesso vedrai la pagina di login

---

## 🔑 Credenziali di Accesso

- **Username**: `maxdany`
- **Password**: `ognibattitodicuore01!`

---

## 🛡️ Sicurezza

- ✅ La password è **hashata con bcrypt** (non salvata in chiaro)
- ✅ I secrets sono **criptati** su Streamlit Cloud (non visibili pubblicamente)
- ✅ Il file `.streamlit/secrets.toml` è **ignorato da git** (non committato)
- ✅ Cookie con **scadenza 30 giorni** (logout automatico)

---

## 📝 Note

### Per Eseguire in Locale

Se vuoi testare l'app in locale, il file `.streamlit/secrets.toml` è già presente nella tua directory locale.

**IMPORTANTE**: NON committare mai questo file su GitHub!

### Per Aggiungere Nuovi Utenti

1. Genera l'hash della nuova password:
   ```python
   import bcrypt
   password = "nuova_password"
   hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
   print(hashed.decode('utf-8'))
   ```

2. Aggiungi il nuovo utente ai secrets:
   ```toml
   [credentials.usernames.nuovo_user]
   name = "Nome Completo"
   password = "$2b$12$hash_generato..."
   ```

3. Aggiorna i secrets su Streamlit Cloud

---

## 🚨 Troubleshooting

### "Configurazione autenticazione mancante!"
- Verifica che i secrets siano configurati correttamente su Streamlit Cloud
- Controlla che il formato TOML sia corretto (nessun errore di sintassi)

### "Username o password errati"
- Ricontrolla username: `maxdany` (minuscolo)
- Ricontrolla password: `ognibattitodicuore01!` (case-sensitive)

### App non si avvia dopo aver aggiunto secrets
- Controlla i log dell'app su Streamlit Cloud
- Verifica che `streamlit-authenticator>=0.2.3` sia in `requirements.txt`
