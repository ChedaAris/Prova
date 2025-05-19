from config.mqtt_config import get_mqtt, NEW_CONNECTION_TOPIC, ON_MODULE_UPDATE_TOPIC, LAST_WILL_TOPIC
from config.mqtt_config import app_ref as app
from models.model import Module
from models.conn import db
from datetime import datetime
import json
import logging

microcontrollers_logger = logging.getLogger('microcontrollers')

"""
Modulo per l'interazione con il broker MQTT.
Questo modulo gestisce l'invio e la ricezione di messaggi MQTT per il controllo dei moduli.
"""

mqtt = get_mqtt()

@mqtt.on_message()
def handle_message(client, userdata, message):
    """
    Callback per la ricezione di tutti i messaggi MQTT.
    Viene scatenata quando un messaggio arriva su un topic sottoscritto.
    """
    with app.app_context():
        topic = message.topic
        payload_raw = message.payload.decode()
        microcontrollers_logger.debug(f"TITLE: Raw MQTT Message Received | DESC: Topic: '{topic}', Raw Payload: '{payload_raw}'")

        try:
            payload = json.loads(payload_raw)
        except json.JSONDecodeError as e:
            # Registra un errore se il payload JSON non è valido
            microcontrollers_logger.error(f"TITLE: MQTT Payload JSON Error | DESC: Failed to decode JSON from topic '{topic}'. Error: {e}. Raw Payload: '{payload_raw}'")
            return

        # Chiama la funzione di gestione appropriata in base al topic del messaggio
        if topic == NEW_CONNECTION_TOPIC:
            _handle_new_connection(payload)
        elif topic == LAST_WILL_TOPIC:
            _handle_last_will(payload)
        else:
            # Registra un'informazione se il topic non è gestito
            microcontrollers_logger.info(f"TITLE: Unhandled MQTT Topic | DESC: Received message on unhandled topic: '{topic}'. Payload: {payload}")


def _handle_new_connection(data):
    """
    Gestisce i messaggi relativi a una nuova connessione di un modulo.
    Registra un nuovo modulo o aggiorna lo stato di uno esistente.
    """
    mac = data.get('mac')
    module_type = data.get('type') # Tipo del modulo (es. 'numeric', 'arrow')

    if not mac or not module_type:
        microcontrollers_logger.warning(f"TITLE: Invalid New Connection Payload | DESC: Missing 'mac' or 'type' in payload: {data}")
        return False
    
    if module_type not in ['numeric', 'arrow']:
        microcontrollers_logger.warning(f"TITLE: Invalid Module Type | DESC: Received invalid module type '{module_type}' for MAC '{mac}'. Payload: {data}")
        return False
    
    microcontrollers_logger.debug(f"TITLE: New Module Connection Attempt | DESC: Module MAC '{mac}', Type '{module_type}' attempting connection.")
    
    module = Module.get_from_mac(mac)
    
    # Se il modulo non esiste, lo crea
    if not module:
        module = Module(mac=mac)
        module.place = 'NEW MODULE' # Posizione di default per i nuovi moduli
        module.online = True # Imposta lo stato online
        module.type = module_type
        module.animation = 'none' # Animazione di default
        module.on = False # Stato di accensione di default
        if module.type == 'numeric':
            module.number = 0
        module.last_seen = datetime.now()
        module.last_update = datetime.now()
        db.session.add(module)
        db.session.commit()
        microcontrollers_logger.info(f"TITLE: New Module Created | DESC: New module MAC '{mac}', Type '{module_type}' created in database.")
    else:
        # Se il modulo esiste, aggiorna il suo stato
        module.online = True
        module.type = module_type # Aggiorna il tipo, potrebbe essere cambiato
        module.last_seen = datetime.now()
        db.session.commit()
        microcontrollers_logger.info(f"TITLE: Existing Module Reconnected | DESC: Module MAC '{mac}', Type '{module_type}' marked as online. Last seen updated.")
    
    # Pubblica la configurazione corrente al modulo appena connesso/riconnesso
    publish_new_configuration(module)

    return True

def _handle_last_will(data):
    """
    Gestisce i messaggi di "last will", inviati quando un modulo si disconnette inaspettatamente.
    Imposta il modulo come offline.
    """
    mac = data.get('mac')
    
    if not mac:
        microcontrollers_logger.warning(f"TITLE: Invalid Last Will Payload | DESC: Missing 'mac' in last will payload: {data}")
        return False
    
    module = Module.get_from_mac(mac)

    if module:
        module.online = False
        db.session.commit()
        microcontrollers_logger.info(f"TITLE: Module Disconnected (Last Will) | DESC: Module MAC '{mac}' ('{module.place}') marked as offline due to last will testament.")
    else:
        microcontrollers_logger.warning(f"TITLE: Unknown Module Disconnected (Last Will) | DESC: Received last will for unknown MAC '{mac}'.")
    
    return True

def publish_new_configuration(module):
    """
    Pubblica la configurazione aggiornata a un modulo specifico via MQTT.
    Utilizzato quando le impostazioni di un modulo vengono modificate dall'interfaccia web.
    """
    topic = f"{ON_MODULE_UPDATE_TOPIC}/{module.mac}"
    payload = {
        'on': module.on,
        'color': module.color,
        'animation': module.animation,
        'number': module.number,
    }
    
    # Pubblica il messaggio MQTT con la configurazione, con QoS 1 per garantire la consegna
    mqtt.publish(topic, json.dumps(payload), qos=1)
    
    microcontrollers_logger.info(f"TITLE: MQTT Config Published | DESC: Configuration sent to module MAC '{module.mac}' ('{module.place}') on topic '{topic}'. Payload: {payload}")
    return True