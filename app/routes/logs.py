from flask import Blueprint, render_template, request, current_app
from flask_login import login_required
from datetime import datetime
import pathlib
from services.log_reader_service import parse_log_file, LOG_FILES_CONFIG


logs_bp = Blueprint('logs_bp', __name__)

"""
Gestione delle route per la visualizzazione dei log.
"""

@logs_bp.app_template_filter('format_timestamp')
def _format_timestamp_filter(timestamp_str, fmt="%d %b %Y, %H:%M:%S"):
    """Filtro Jinja per formattare una stringa timestamp."""
    if not timestamp_str:
        return "N/A"
    try:
        # Il timestamp nel log è nel formato 'YYYY-MM-DD HH:MM:SS,ms'
        dt_object = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
        return dt_object.strftime(fmt)
    except ValueError:
        # Se il parsing fallisce, restituisce la stringa originale o un placeholder
        current_app.logger.warning(f"TITLE: Errore Formattazione Timestamp | DESC: Impossibile formattare il timestamp '{timestamp_str}'")
        return timestamp_str # o "Data Invalida"


@logs_bp.route("/", methods=["GET"])
@login_required
def index():
    log_dir = pathlib.Path(current_app.root_path) / 'logs'
    
    # Definisce l'ordine delle schede
    ordered_tabs = ['app', 'auth', 'api', 'microcontrollers']
    
    active_tab = request.args.get('tab', ordered_tabs[0]) # Predefinito alla prima scheda in ordine

    if active_tab not in LOG_FILES_CONFIG:
        active_tab = ordered_tabs[0]

    logs_for_active_tab = []
    log_file_name = LOG_FILES_CONFIG.get(active_tab)

    if log_file_name:
        log_file_full_path = log_dir / log_file_name
        logs_for_active_tab = parse_log_file(log_file_full_path)
    
    # Il template si aspetta logs[active_tab], quindi creiamo un dizionario in questo formato
    # ma popoliamo solo i log della scheda attiva per evitare di caricare tutti i file.
    display_logs = {
        active_tab: logs_for_active_tab
    }

    return render_template('log/index.html', 
                           logs=display_logs, 
                           active_tab=active_tab,
                           available_tabs=ordered_tabs)
