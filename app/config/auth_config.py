from flask import session
from flask_login import LoginManager
from models.model import User
import os

def configure_login(app, ldap_manager):
    """
    Configura Flask-Login con minima integrazione con Flask-LDAP3-Login.
    Solo per verificare se l'autenticazione LDAP è riuscita.
    """
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth_bp.login'
    login_manager.login_message = ""
    
    @login_manager.user_loader
    def load_user(id):
        """
        Carica l'utente dalla sessione.
        """
        if id in session:
            return User.from_json(session[id]) 
        return None

    
    @ldap_manager.save_user
    def save_user(dn, username, data, memberships):
        """
        Salva l'utente autenticato in sessione.
        Controlla anche l'appartenenza al gruppo Docenti.
        """
        target_group = 'CN=Docenti,{},{}'.format(os.getenv('LDAP_GROUP_DN'), os.getenv('LDAP_BASE_DN'))
        
        if target_group not in data.get('memberOf', []):
            return None
        
        user = User(dn, username)
        session[dn] = user.to_json()
        return user