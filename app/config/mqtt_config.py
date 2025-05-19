import os
import ssl
from flask_mqtt import Mqtt

mqtt = None

app_ref = None

# Definizione dei topic MQTT
# Questi devono essere gli stessi definiti sul microcontrollore
NEW_CONNECTION_TOPIC = 'new_connection'
ON_MODULE_UPDATE_TOPIC = 'on_module_update'
LAST_WILL_TOPIC = 'last_will'


def configure_mqtt(app):
    """
    Configura le impostazioni MQTT per l'interazione con il broker.
    """
    global mqtt, app_ref
    
    app.config['MQTT_BROKER_URL'] = os.getenv('MQTT_BROKER_URL')
    app.config['MQTT_BROKER_PORT'] = int(os.getenv('MQTT_BROKER_PORT', 1883))
    app.config['MQTT_USERNAME'] = os.getenv('MQTT_USERNAME')
    app.config['MQTT_PASSWORD'] = os.getenv('MQTT_PASSWORD')
    app.config['MQTT_KEEP_ALIVE'] = int(os.getenv('MQTT_KEEP_ALIVE', 60))
    app.config['MQTT_TLS_ENABLED'] = os.getenv("MQTT_TLS_ENABLED", 'False').lower() in ('true', '1', 't')
    if app.config['MQTT_TLS_ENABLED']:
        app.config['MQTT_TLS_INSECURE'] = os.getenv("MQTT_TLS_INSECURE", 'False').lower() in ('true', '1', 't')
        app.config['MQTT_TLS_CA_CERTS'] = os.getenv('MQTT_TLS_CA_CERTS', '')
        app.config['MQTT_TLS_VERSION'] = ssl.PROTOCOL_TLSv1_2

    mqtt = Mqtt(app)
    app_ref = app

    @mqtt.on_connect()
    def handle_connect(client, userdata, flags, rc):
        """
        Callback per la connessione al broker MQTT.
        """
        mqtt.subscribe(NEW_CONNECTION_TOPIC)
        mqtt.subscribe(LAST_WILL_TOPIC)

        print("MQTT configurato con successo.")

def get_mqtt():
    """
    Restituisce l'istanza di Mqtt configurata.
    """
    global mqtt
    if mqtt is None:
        raise ValueError("MQTT non configurato. Assicurati di chiamare configure_mqtt(app) prima.")
    
    return mqtt