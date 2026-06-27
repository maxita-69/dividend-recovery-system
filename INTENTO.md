**Ultima cosa fatta:** servizi API+Streamlit resi persistenti (systemd user), bind corretto a 127.0.0.1, esposizione pubblica esclusa (curl da casa = timeout). Angular in frontend/ confermato VIVO.
**Prossimo passo:** lavorare sull'Angular (frontend/) — verificare proxy.conf.json punti a :8001, poi npm start e accesso via tunnel SSH con -L 4200:localhost:4200
**Domande aperte:** abilitare loginctl enable-linger per avvio al boot? ; API senza auth (ok solo finché localhost) ; accesso remoto = SEMPRE tunnel SSH, MAI esposizione pubblica
