import os
from flask import Flask 
from dotenv import load_dotenv
from flask_ldap3_login import LDAP3LoginManager 
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from models.conn import db
from config.ldap_config import configure_ldap
from config.log_config import configure_logging
from config.auth_config import configure_login
from config.mqtt_config import configure_mqtt

from routes.auth import auth_bp
from routes.logs import logs_bp


def create_app():
    """
    Crea e configura l'istanza dell'applicazione Flask.
    """
    
    load_dotenv()

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'devsecretkey')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inizializza CSRF protection
    CSRFProtect(app)
   
    # Inizializza il database
    db.init_app(app)
    Migrate(app, db)

    # Configurazione LDAP
    configure_ldap(app)

    #Configurazione MQTT
    configure_mqtt(app)
    
    # Serve initializzazione del gestore MQTT
    from routes.modules import modules_bp

    # Configurazioni del gestore di login
    ldap_manager = LDAP3LoginManager(app)
    configure_login(app, ldap_manager)

    # Configurazione del logging
    configure_logging(app)

    # Registrazione dei Blueprint
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(modules_bp, url_prefix='/')
    app.register_blueprint(logs_bp, url_prefix='/logs')

    with app.app_context():
        db.create_all()  # Crea le tabelle del database se non esistono

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=False)
