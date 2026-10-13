from flask import Blueprint, session, redirect, url_for, request, flash
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
        
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create_booking':
            client_id = request.form.get('client_id')
            lesson_id = request.form.get('lesson_id')
            status = request.form.get('status', 'Confermata')
            
            if not client_id or not lesson_id:
                flash('Seleziona un cliente e una lezione.', 'error')
            else:
                try:
                    if DATABASE_URL:
                        cursor.execute('INSERT INTO bookings (lesson_id, client_id, status) VALUES (%s, %s, %s)',
                                       (lesson_id, client_id, status))
                    else:
                        cursor.execute('INSERT INTO bookings (lesson_id, client_id, status) VALUES (?, ?, ?)',
                                       (lesson_id, client_id, status))
                    conn.commit()
                    log_activity(session['username'], f"Creata prenotazione per cliente ID: {client_id}")
                    flash('Prenotazione aggiunta con successo!', 'success')
                except Exception as e:
                    flash(f"Errore durante l'inserimento della prenotazione: {e}", 'error')
                    
        elif action == 'delete_booking':
            booking_id = request.form.get('booking_id')
            if DATABASE_URL:
                cursor.execute('DELETE FROM bookings WHERE id = %s', (booking_id,))
            else:
                cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
            conn.commit()
            log_activity(session['username'], f"Eliminata prenotazione ID: {booking_id}")
            flash('Prenotazione eliminata con successo.', 'success')
            
        return redirect(url_for('dashboard_bp.index'))

    courses = conn.execute('''
        SELECT c.*, i.nome as i_nome, i.cognome as i_cognome, r.nome as r_nome
        FROM courses c 
        LEFT JOIN instructors i ON c.instructor_id = i.id 
        LEFT JOIN rooms r ON c.room_id = r.id
    ''').fetchall()
    
    clients = conn.execute('SELECT * FROM clients').fetchall()
    lessons = conn.execute('''
        SELECT li.*, c.nome as corso_nome 
        FROM lesson_instances li 
        LEFT JOIN courses c ON li.course_id = c.id
        ORDER BY li.data_lezione DESC
    ''').fetchall()
    
    bookings = conn.execute('''
        SELECT b.*, cl.nome as c_nome, cl.cognome as c_cognome, c.nome as corso_nome, li.data_lezione
        FROM bookings b
        LEFT JOIN clients cl ON b.client_id = cl.id
        LEFT JOIN lesson_instances li ON b.lesson_id = li.id
        LEFT JOIN courses c ON li.course_id = c.id
    ''').fetchall()
    
    conn.close()
    
    username = session.get('username', 'Utente')
    
    clients_options = "".join([f'<option value="{cl["id"]}">{cl["nome"]} {cl["cognome"]}</option>' for cl in clients])
    lessons_options = "".join([f'<option value="{l["id"]}">{l["corso_nome"]} - {l["data_lezione"]}</option>' for l in lessons])
    
    bookings_rows = ""
    for b in bookings:
        bd = dict(b)
        bookings_rows += f"""
        <tr>
            <td>{bd.get('c_nome', '')} {bd.get('c_cognome', '')}</td>
            <td>{bd.get('corso_nome', 'N/D')}</td>
            <td>{bd.get('data_lezione', 'N/D')}</td>
            <td><span class="badge bg-success">{bd.get('status', 'Confermata')}</span></td>
            <td>
                <form method="POST" style="display:inline;" onsubmit="return confirm('Confermi l\\'eliminazione di questa prenotazione?');">
                    <input type="hidden" name="action" value="delete_booking">
                    <input type="hidden" name="booking_id" value="{bd.get('id')}">
                    <button type="submit" class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></button>
                </form>
            </td>
        </tr>
        """
    if not bookings:
        bookings_rows = '<tr><td colspan="5" class="text-center text-muted">Nessuna prenotazione attiva.</td></tr>'

    courses_rows = ""
    for c in courses:
        conn_d = get_db()
        cd_list = conn_d.execute('''
            SELECT d.nome, cd.orario_inizio, cd.orario_fine 
            FROM course_days cd 
            JOIN days d ON cd.day_id = d.id 
            WHERE cd.course_id = ?
        ''' if not DATABASE_URL else '''
            SELECT d.nome, cd.orario_inizio, cd.orario_fine 
            FROM course_days cd 
            JOIN days d ON cd.day_id = d.id 
            WHERE cd.course_id = %s
        ''', (c['id'],)).fetchall()
        conn_d.close()
        
        dettagli_orari = "<br>".join([f"<small>• <strong>{item['nome']}</strong>: {item['orario_inizio']} - {item['orario_fine']}</small>" for item in cd_list])
        if not dettagli_orari:
            dettagli_orari = '<span class="text-muted">Nessun giorno programmato</span>'

        courses_rows += f"""
        <tr>
            <td><strong>{c['nome']}</strong><br><small class="text-muted">{c['descrizione'] or ''}</small></td>
            <td>{dettagli_orari}</td>
            <td>{c['r_nome'] or 'N/D'}</td>
            <td>{c['i_nome'] or ''} {c['i_cognome'] or ''}</td>
        </tr>
        """
    if not courses:
        courses_rows = '<tr><td colspan="4" class="text-center text-muted">Nessun corso programmato al momento.</td></tr>'

    content = f"""
    <div class="row mb-4">
        <div class="col-12">
            <h2>Benvenuto, {username}!</h2>
            <p class="text-muted">Gestione centrale del calendario, dei corsi e delle prenotazioni dei clienti.</p>
        </div>
    </div>
    
    <div class="card shadow-sm p-4 mb-4">
        <h4 class="mb-3">Aggiungi Nuova Prenotazione</h4>
        <form method="POST" class="row g-3">
            <input type="hidden" name="action" value="create_booking">
            <div class="col-md-4">
                <label class="form-label">Cliente</label>
                <select name="client_id" class="form-select" required>
                    <option value="">Seleziona Cliente...</option>
                    {clients_options}
                </select>
            </div>
            <div class="col-md-4">
                <label class="form-label">Lezione / Istanza</label>
                <select name="lesson_id" class="form-select" required>
                    <option value="">Seleziona Lezione...</option>
                    {lessons_options}
                </select>
            </div>
            <div class="col-md-4">
                <label class="form-label">Stato</label>
                <select name="status" class="form-select">
                    <option value="Confermata">Confermata</option>
                    <option value="In attesa">In attesa</option>
                    <option value="Annullata">Annullata</option>
                </select>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-success"><i class="bi bi-calendar-plus"></i> Inserisci Prenotazione</button>
            </div>
        </form>
    </div>

    <div class="card shadow-sm p-4 mb-4">
        <h4 class="mb-3">Elenco Prenotazioni Attive</h4>
        <div class="table-responsive">
            <table class="table table-striped align-middle">
                <thead>
                    <tr>
                        <th>Cliente</th>
                        <th>Corso</th>
                        <th>Data Lezione</th>
                        <th>Stato</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {bookings_rows}
                </tbody>
            </table>
        </div>
    </div>

    <div class="card shadow-sm p-4">
        <h4 class="mb-3">Corsi Programmabili e Orari</h4>
        <div class="table-responsive">
            <table class="table table-striped align-middle">
                <thead>
                    <tr>
                        <th>Corso</th>
                        <th>Programmazione e Orari per Giorno</th>
                        <th>Sala</th>
                        <th>Istruttore</th>
                    </tr>
                </thead>
                <tbody>
                    {courses_rows}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_page(content, courses=courses)
