from flask import Blueprint, render_template, redirect, flash, current_app, request, url_for, session
from flask_ldap3_login.forms import LDAPLoginForm
from flask_ldap3_login import LDAP3LoginManager
from flask_login import login_user, logout_user, current_user, login_required
import logging

auth_logger = logging.getLogger('auth')

"""
Gestione delle route per l'autenticazione degli utenti.
"""

auth_bp = Blueprint('auth_bp', __name__)

def _check_ldap_server_connectivity():
    """
    Verifica la connettività del server LDAP e mostra un messaggio flash in caso di problemi.
    """
    # LDAP3LoginManager, current_app, session, flash sono accessibili qui.
    # Viene creata una nuova istanza di LDAP3LoginManager per questo controllo.
    ldap_manager_check = LDAP3LoginManager()
    try:
        conn = ldap_manager_check.connection
        if not conn.strategy.sync:
            conn.open()
        if not conn.bound:
            conn.bind()
    except Exception as e:
        current_app.logger.error(f"TITLE: LDAP Connection Error | DESC: LDAP server unreachable. Error: {e}")
        # Rimuove i messaggi di errore precedenti, ovvero quelli di autenticazione fallita
        session.pop('_flashes', None) 
        flash('LDAP server is currently unreachable. Please try again later.', 'danger')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Gestisce il login dell'utente tramite LDAP.
    Verifica solo l'autenticazione senza salvare dati dell'utente.
    
    Returns:
        Response: Redirect alla pagina dei moduli in caso di login riuscito,
                 o risposta JSON con errori in caso di fallimento.
    """
    if current_user.is_authenticated:
        return redirect('/')

    # Usa il form di login fornito da flask-ldap3-login
    form = LDAPLoginForm()

    if form.validate_on_submit():

        user = form.user
        if user is None: #Significa che l'utente non è nel gruppo Docenti
            auth_logger.warning(f"TITLE: LDAP Auth Failed (Access Denied) | DESC: User '{form.username.data}' not in allowed group or invalid credentials.") # Changed
            flash('Access Denied', 'danger')
            return redirect(url_for('auth_bp.login'))
        
        login_user(user)

        auth_logger.info(f"TITLE: LDAP Auth Success | DESC: User '{user.username}' logged in successfully.")
        flash('Login successful!', 'success')

        return redirect(url_for('modules_bp.index'))
        
            
    if request.method == 'POST':
        if not form.user: # Log only if it wasn't the 'Access Denied' case from above
            auth_logger.warning(f"TITLE: Login Attempt Failed | DESC: Invalid username or password for user '{form.username.data}'.")
        flash('Invalid username or password', 'danger')
    
    _check_ldap_server_connectivity()

    return render_template('auth/login.html', form=form)
    

@auth_bp.route('/logout')
@login_required
def logout():
    """
    Gestisce il logout dell'utente.
    """
    username = current_user.username
    logout_user()
    auth_logger.info(f"TITLE: User Logout | DESC: User '{username}' logged out successfully.")
    
    return redirect(url_for('auth_bp.login'))
