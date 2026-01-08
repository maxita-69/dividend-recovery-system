"""
Authentication module for Dividend Recovery System
Provides login/logout functionality for all pages
"""

import streamlit as st
import streamlit_authenticator as stauth


def check_authentication():
    """
    Check if user is authenticated and show login form if not.

    Returns:
        tuple: (name, authentication_status, username) or stops execution if not authenticated

    Usage in pages:
        from auth import check_authentication
        name, authentication_status, username = check_authentication()
    """

    # Carica configurazione da secrets
    try:
        credentials = {
            'usernames': {}
        }

        # Converti secrets in formato richiesto da authenticator
        for username, user_data in st.secrets["credentials"]["usernames"].items():
            credentials['usernames'][username] = {
                'name': user_data['name'],
                'password': user_data['password']
            }

        cookie_name = st.secrets.get("cookie_name", "dividend_recovery_auth")
        cookie_key = st.secrets.get("cookie_key", "default_key")
        cookie_expiry_days = st.secrets.get("cookie_expiry_days", 30)

    except KeyError:
        st.error("""
        ⚠️ **Configurazione autenticazione mancante!**

        Secrets non trovati. Per eseguire in locale, crea il file `.streamlit/secrets.toml`
        con le credenziali. Per Streamlit Cloud, configura i secrets nella dashboard.
        """)
        st.stop()

    # Crea authenticator
    authenticator = stauth.Authenticate(
        credentials=credentials,
        cookie_name=cookie_name,
        key=cookie_key,
        cookie_expiry_days=cookie_expiry_days
    )

    # Mostra form di login
    name, authentication_status, username = authenticator.login(
        location='main',
        fields={
            'Form name': '🔐 Login - Dividend Recovery System',
            'Username': 'Username',
            'Password': 'Password',
            'Login': 'Accedi'
        }
    )

    # Gestisci stati di autenticazione
    if authentication_status:
        # Utente autenticato
        # Mostra bottone logout nella sidebar
        with st.sidebar:
            st.write(f'👤 **Benvenuto {name}**')
            authenticator.logout('Logout', 'main')

        return name, authentication_status, username

    elif authentication_status == False:
        st.error('❌ **Username o password errati**')
        st.info("""
        💡 **Hai dimenticato le credenziali?**

        Contatta l'amministratore del sistema per il reset della password.
        """)
        st.stop()

    elif authentication_status == None:
        st.warning('⚠️ **Inserisci username e password per accedere**')
        st.info("""
        🔒 **Accesso Protetto**

        Questa applicazione richiede autenticazione.
        Se non hai un account, contatta l'amministratore.
        """)
        st.stop()


def require_authentication():
    """
    Decorator-style helper che ferma l'esecuzione se l'utente non è autenticato.
    Versione semplificata di check_authentication per un uso più rapido.

    Usage in pages:
        from auth import require_authentication
        require_authentication()
        # Il codice dopo questa riga esegue solo se autenticato
    """
    check_authentication()
