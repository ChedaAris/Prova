from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime
from models.conn import db
from models.model import Module
from services.mqtt_service import publish_new_configuration
import logging

api_logger = logging.getLogger('api')

"""
Gestione delle route per la parte di gestione dei moduli.
"""

modules_bp = Blueprint('modules_bp', __name__)


@modules_bp.route("/", methods=["GET"])
@login_required
def index():
    """
    Gestisce l'accesso alla pagina principale che elenca tutti i moduli.
    Recupera tutti i moduli e i conteggi per tipo (numerico, freccia).
    """
    modules = Module.get_all()
    numeric_count = Module.get_count_by_type('numeric')
    arrow_count = Module.get_count_by_type('arrow')
    return render_template('modules/index.html', modules=modules, numeric_count=numeric_count, arrow_count=arrow_count)

@modules_bp.route("/edit/<int:id>", methods=["GET"])
@login_required
def edit(id):
    """
    Gestisce l'accesso alla pagina di modifica di un modulo.
    """
    module = Module.get_one(id)
    
    if not module:
        api_logger.warning(f"TITLE: Module Not Found | DESC: Attempt to edit non-existent module ID '{id}' by user '{current_user.username}'.")
        return render_template('errors/404.html'), 404
    # Registra l'accesso alla pagina di modifica
    api_logger.debug(f"TITLE: Module Edit Page Accessed | DESC: User '{current_user.username}' accessed edit page for module ID '{id}' ('{module.place}').")
    return render_template('modules/edit.html', module=module)


@modules_bp.route("/edit/<int:id>", methods=["POST"])
@login_required
def update(id):
    """
    Gestisce l'aggiornamento dei dati di un modulo specifico.
    Recupera il modulo, aggiorna i suoi campi in base ai dati del form,
    salva le modifiche e pubblica la nuova configurazione via MQTT.
    """
    module = Module.get_one(id)
    
    if not module:
        api_logger.warning(f"TITLE: Module Update Failed (Not Found) | DESC: Attempt to update non-existent module ID '{id}' by user '{current_user.username}'.")
        return render_template('errors/404.html'), 404
    
    # Aggiornamento dei campi dal form
    try:
        # Gestione accensione/spegnimento
        module.on = 'is_power_off' in request.form
        
        # Gestione del colore
        is_color_random = 'is_color_random' in request.form
        if is_color_random:
            # Se è impostato come casuale, usa la stringa 'random'
            module.color = 'random'
        else:
            # Altrimenti, prende il colore esadecimale dal form
            module.color = request.form.get('color', '#ffffff') # Default a bianco se non specificato
            
        # Gestione dell'animazione
        animation_value = request.form.get('animation')
        if animation_value:
            module.animation = animation_value

        # Gestione del numero (solo per moduli di tipo 'numeric')
        if module.type == 'numeric' and 'number' in request.form:
            number_value = request.form.get('number')
            if number_value.isdigit():
                number_int = int(number_value)
                # Verifica che il numero sia tra 0 e 99
                if 0 <= number_int <= 99:
                    module.number = number_int
                else:
                    # Se il numero non è nell'intervallo accettabile, mostra un errore
                    flash('Number must be between 0 and 99', 'danger')
                    return redirect(url_for('modules_bp.edit', id=module.id))
            else:
                # Se non è un numero valido, mostra un messaggio di errore
                flash('Number must be a valid integer', 'danger')
                return redirect(url_for('modules_bp.edit', id=module.id))
                
        # Aggiornamento della posizione/luogo del modulo
        module.place = request.form.get('place', '')
        
        # Aggiornamento del timestamp dell'ultima modifica
        module.last_update = datetime.now()
        
        # Salvataggio delle modifiche nel database
        db.session.commit()

        # Invia la nuova configurazione al modulo tramite MQTT
        publish_new_configuration(module)
        
        api_logger.info(f"TITLE: Module Update Success | DESC: Module ID '{module.id}' ('{module.place}') updated successfully by user '{current_user.username}'.")
        flash('Module successfully udpated', 'success')
        return redirect(url_for('modules_bp.index'))
        
    except Exception as e:
        db.session.rollback()
        api_logger.error(f"TITLE: Module Update Error | DESC: Error updating module ID '{id}' by user '{current_user.username}'. Error: {str(e)}")
        flash(f"Unknown error updating the module", 'danger')
        return redirect(url_for('modules_bp.edit', id=module.id))

@modules_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    """
    Gestisce l'eliminazione di un modulo specifico.
    Spegne il modulo via MQTT prima di eliminarlo dal database.
    """
    module = Module.get_one(id)
    
    if not module:
        api_logger.warning(f"TITLE: Module Deletion Failed (Not Found) | DESC: Attempt to delete non-existent module ID '{id}' by user '{current_user.username}'.")
        return render_template('errors/404.html'), 404
    
    # Spegni il modulo prima di eliminarlo, inviando una configurazione di "off"
    module.on = False 
    publish_new_configuration(module)

    module_place_for_log = module.place # Memorizza il nome del luogo per il log prima dell'eliminazione
    try:
        db.session.delete(module)
        db.session.commit()
        api_logger.info(f"TITLE: Module Deletion Success | DESC: Module ID '{id}' ('{module_place_for_log}') deleted successfully by user '{current_user.username}'.")
        flash('Module successfully deleted', 'success')
    except Exception as e:
        db.session.rollback()
        api_logger.error(f"TITLE: Module Deletion Error | DESC: Error deleting module ID '{id}' ('{module_place_for_log}') by user '{current_user.username}'. Error: {str(e)}")
        flash(f"Unknown error deleting the module", 'danger')
    
    return redirect(url_for('modules_bp.index'))