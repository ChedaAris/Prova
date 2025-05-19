import logging
from logging.handlers import TimedRotatingFileHandler 
import pathlib

# Standard log format to be used by all handlers
LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
log_formatter = logging.Formatter(LOG_FORMAT)

def _setup_specific_logger(name, log_dir, filename, when='D', backup_count=1, level=logging.INFO):
    """Funzione di supporto per configurare un logger specifico con TimedRotatingFileHandler.""" 
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Impedisce ai messaggi di propagarsi ai gestori del logger root o di app.logger 
    logger.propagate = False

    log_file_path = log_dir / filename
    
    # Gestore per scrivere su un file specifico, con rotazione giornaliera 
    file_handler = TimedRotatingFileHandler(
        log_file_path, 
        when=when,  # 'W0' per la rotazione di lunedì, può essere 'D' per giornaliera, ecc. 
        backupCount=backup_count,  # Mantiene il log corrente + backup_count backup 
        encoding='utf-8',
        delay=False
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(level)

    # Aggiunge il gestore solo se uno simile non è già presente 
    if not any(isinstance(h, TimedRotatingFileHandler) and h.baseFilename == str(log_file_path) for h in logger.handlers):
        logger.addHandler(file_handler)
    
    return logger

def configure_logging(app):
    """
    Configura il sistema di logging per l'applicazione Flask.
    I log sono categorizzati: auth, api, microcontrollori, e log generali dell'app.
    Ogni categoria ha il suo file di log con rotazione giornaliera (1 backup mantenuto). 
    """
    APP_ROOT_DIR = pathlib.Path(app.root_path)
    LOG_DIR = APP_ROOT_DIR / 'logs'
    
    # Crea la directory per i log se non esiste
    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # --- Configurazione logger specifici --- 
    # Questi logger scriveranno nei loro rispettivi file e non si propagheranno ad app.logger
    _setup_specific_logger('auth', LOG_DIR, 'auth.log', backup_count=1) # Mantiene 1 backup settimanale
    _setup_specific_logger('api', LOG_DIR, 'api.log', backup_count=1)
    _setup_specific_logger('microcontrollers', LOG_DIR, 'microcontrollers.log', backup_count=1)

    # --- Configura il logger predefinito di Flask (app.logger) per log generali e output su console ---
    
    # File di log generale dell'applicazione (app.log) - usa TimedRotatingFileHandler 
    general_log_file_path = LOG_DIR / 'app.log'
    
    # Rimuove eventuali vecchi RotatingFileHandler per app.log se presenti 
    old_file_handler = next((h for h in app.logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler) and h.baseFilename == str(general_log_file_path)), None)
    if old_file_handler:
        app.logger.removeHandler(old_file_handler)

    general_file_handler = TimedRotatingFileHandler(
        general_log_file_path, 
        when='D', 
        backupCount=1, # Mantiene 1 backup settimanale 
        encoding='utf-8'
    )
    general_file_handler.setFormatter(log_formatter)
    general_file_handler.setLevel(logging.INFO) # Log generali dell'app a livello INFO 

    # Aggiunge il gestore file generale ad app.logger se non già presente 
    if not any(isinstance(h, TimedRotatingFileHandler) and h.baseFilename == str(general_log_file_path) for h in app.logger.handlers if isinstance(h, TimedRotatingFileHandler)):
        app.logger.addHandler(general_file_handler)

    # Gestore console per app.logger (utile per debug locale) 
    # Controlla se un gestore console esiste già e lo aggiorna, oppure ne aggiunge uno nuovo 
    existing_console_handler = None
    for handler in app.logger.handlers:
        if isinstance(handler, logging.StreamHandler) and \
           getattr(handler, 'stream', None) and \
           handler.stream.name in ('<stderr>', '<stdout>'):
            existing_console_handler = handler
            break
    
    if existing_console_handler:
        existing_console_handler.setFormatter(log_formatter) # Assicura che usi il nuovo formato 
        existing_console_handler.setLevel(logging.DEBUG) # Assicura che sia a livello DEBUG 
    else:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(console_handler)
    
    # Imposta il livello per app.logger stesso. 
    # Questo dovrebbe essere il livello più basso tra i suoi gestori per permettere a tutti i messaggi di passare. 
    app.logger.setLevel(logging.DEBUG)