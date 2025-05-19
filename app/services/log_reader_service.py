from flask import current_app
import re
import os

LOG_FILES_CONFIG = {
    'app': 'app.log',
    'auth': 'auth.log',
    'api': 'api.log',
    'microcontrollers': 'microcontrollers.log',
}

# Regex per analizzare le righe di log basate sul formato:
# %(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]
LOG_LINE_REGEX = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+"
    r"(?P<severity>DEBUG|INFO|WARNING|ERROR|CRITICAL):\s+"
    r"(?P<message_content>.*?)\s+"
    r"\[in (?P<file>.*?):(?P<line>\d+)\]$"
)

# Regex per analizzare la struttura "TITLE: ... | DESC: ..." dal contenuto del messaggio
MESSAGE_DETAIL_REGEX = re.compile(
    r"TITLE:\s*(?P<title>.*?)\s*\|\s*DESC:\s*(?P<description>.*)"
)


def parse_log_file(log_file_path):
    """
    Analizza un file di log e restituisce una lista di voci di log strutturate.

    Args:
        log_file_path (str): Il percorso del file di log da analizzare.

    Returns:
        list: Una lista di dizionari, dove ogni dizionario rappresenta una voce di log.
              Restituisce una lista vuota se il file non esiste o si verifica un errore.
    """
    parsed_logs = []
    if not os.path.exists(log_file_path):
        current_app.logger.warning(f"TITLE: File di Log Non Trovato | DESC: Il file di log specificato per la visualizzazione non esiste: {log_file_path}")
        return []
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line_number, line_content in enumerate(f, 1):
                line_content = line_content.strip()
                if not line_content:
                    continue
                
                match = LOG_LINE_REGEX.match(line_content)
                if match:
                    log_data = match.groupdict()
                    
                    # Estrae il contenuto del messaggio originale per un'ulteriore analisi
                    message_content = log_data.pop('message_content') 
                    
                    message_detail_match = MESSAGE_DETAIL_REGEX.match(message_content)
                    if message_detail_match:
                        details = message_detail_match.groupdict()
                        log_data['title'] = details['title'].strip()
                        log_data['description'] = details['description'].strip()
                    else:
                        # Se il formato TITLE/DESC non è presente, usa un titolo generico
                        # e il contenuto completo del messaggio come descrizione
                        log_data['title'] = "Unknown Log" 
                        log_data['description'] = message_content
                    
                    log_data['severity'] = log_data['severity'].lower()
                    parsed_logs.append(log_data)
                else:
                    # Registra un debug per le righe che non corrispondono al formato atteso
                    # Queste righe vengono attualmente ignorate per mantenere la coerenza dei dati analizzati
                    current_app.logger.debug(f"TITLE: Salto Analisi Riga di Log | DESC: Saltata l'analisi della riga di log {line_number} in {os.path.basename(log_file_path)} a causa di un formato non valido: {line_content[:150]}")
                    pass
    except Exception as e:
        # Registra un errore se si verifica un problema durante la lettura o l'analisi del file
        current_app.logger.error(f"TITLE: Errore Lettura File di Log | DESC: Errore durante la lettura o l'analisi del file di log {log_file_path}. Errore: {str(e)}")
        return [] # Restituisci una lista vuota in caso di errore
    
    parsed_logs.reverse() # Inverte la lista per mostrare i log più recenti per primi
    return parsed_logs[:50] # Restituisce al massimo le prime 50 voci di log più recenti