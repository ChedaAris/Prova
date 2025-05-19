from models.conn import db
from sqlalchemy import DateTime, Enum
from flask_login import UserMixin
import json

class Module(db.Model):
    """
    Modello per la gestione dei moduli, aggiornato secondo lo schema ER.
    """
    id = db.Column(db.Integer, primary_key=True)
    mac = db.Column(db.String(17), unique=True, nullable=False)  # MAC (XX:XX:XX:XX:XX:XX)
    type = db.Column(Enum('numeric', 'arrow', name='module_type_enum'), nullable=True) # Campo per il tipo di modulo: 'numeric' o 'arrow'
    number = db.Column(db.Integer, nullable=True)
    last_seen = db.Column(DateTime, nullable=True)
    last_update = db.Column(DateTime, nullable=True)
    animation = db.Column(db.String(20), nullable=True)
    color = db.Column(db.String(7), nullable=True)  # Colore esadecimale (es. #RRGGBB)
    place = db.Column(db.String(100), nullable=True)
    on = db.Column(db.Boolean, nullable=True, default=False)  # Stato di accensione del modulo (True/False)
    online = db.Column(db.Boolean, nullable=True, default=False)  # Stato di connessione del modulo (True/False)

    
    @staticmethod
    def get_all():
        stmt = db.select(Module)
        items = db.session.execute(stmt)
        
        return [item for item in items.scalars()]
    
    @staticmethod
    def get_one(id):
        stmt = db.select(Module).where(Module.id == id)
        item = db.session.execute(stmt).scalar()
        
        if item:
            return item
        else:
            return None
    
    @staticmethod
    def get_from_mac(mac):
        stmt = db.select(Module).where(Module.mac == mac)
        item = db.session.execute(stmt).scalar()
        
        if item:
            return item
        else:
            return None
    
    @staticmethod
    def get_count_by_type(module_type):
        """
        Restituisce il numero di moduli di un certo tipo.
        """
        stmt = db.select(Module).where(Module.type == module_type)
        items = db.session.execute(stmt).scalars().all()

        return len(items)

    def __repr__(self):
        return f'<Module {self.mac}>'


class User(UserMixin):
    def __init__(self, dn, username):
        self.dn = dn
        self.username = username

    def __repr__(self):
        return self.dn

    def get_id(self):
        return self.dn
        
    def to_json(self):
        """
        Converte l'oggetto User in un dizionario JSON-serializzabile.
        """
        return {
            'dn': self.dn,
            'username': self.username,
        }
        
    @classmethod
    def from_json(cls, data):
        """
        Crea un oggetto User da un dizionario JSON.
        """
        if data.get('dn') and data.get('username'):
            return cls(data['dn'], data['username'])
        return None