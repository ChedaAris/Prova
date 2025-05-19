import os

def configure_ldap(app):
    """
    Configura le impostazioni LDAP essenziali per l'autenticazione.
    """
    # Impostazioni minime necessarie per l'autenticazione LDAP
    app.config['LDAP_HOST'] = os.getenv('LDAP_HOST')
    app.config['LDAP_PORT'] = int(os.getenv('LDAP_PORT', 389))

    app.config['LDAP_BASE_DN'] = os.getenv('LDAP_BASE_DN')
    app.config['LDAP_USER_DN'] = os.getenv('LDAP_USER_DN')
    app.config['LDAP_GROUP_DN'] = os.getenv('LDAP_GROUP_DN')

    app.config['LDAP_USER_RDN_ATTR'] = os.getenv('LDAP_USER_RDN_ATTR', 'cn')
    app.config['LDAP_USER_LOGIN_ATTR'] = os.getenv('LDAP_USER_LOGIN_ATTR', 'sAMAccountName')
    
    # Opzionali per una connessione autenticata al server LDAP (se necessario)
    if os.getenv('LDAP_BIND_USER_DN'):
        app.config['LDAP_BIND_USER_DN'] = os.getenv('LDAP_BIND_USER_DN')
        app.config['LDAP_BIND_USER_PASSWORD'] = os.getenv('LDAP_BIND_USER_PASSWORD')