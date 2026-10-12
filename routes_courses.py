from flask import Blueprint, request, redirect, url_for, session, flash
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

courses_bp = Blueprint('courses_bp', __name__)

@courses_bp.route('/courses', methods=['GET', 'POST'])
def manage_courses():
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
        
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nome = request.form['nome']
        descrizione = request.form.get('descrizione', '')
        instructor_id = request.form.get('instructor_id')
        room_id = request.form.get('room_id')
        orario_inizio = request.form.get('orario_inizio')
        orario_fine = request.form.get('orario_fine')
        giorni_selezionati = request.form.getlist('giorni') # Lista degli ID dei giorni selezionati via checkbox
        
        if DATABASE_URL:
            cursor.execute('''INSERT INTO courses (nome, descrizione, instructor_id, room_id, orario_inizio, orario_fine)
                              VALUES (%s, %s, %s, %s, %s, %s) RETURNING id''',
                           (nome, descrizione, instructor_id or None, room_id or None, orario_inizio, orario_fine))
            course_id = cursor.fetchone()['id']
        else:
            cursor.execute('''INSERT INTO courses (nome, descrizione, instructor_id, room_id, orario_inizio, orario_fine)
                              VALUES (?, ?, ?, ?, ?, ?)''',
                           (nome, descrizione, instructor_id or None, room_id or None, orario_inizio, orario_fine))
            course_id = cursor.lastrowid
            
        # Inserisci le relazioni nella tabella course_days
        for day_id in giorni_selezionati:
            if DATABASE_URL:
                cursor.execute('INSERT INTO course_days (course_id, day_id) VALUES (%s, %s)', (course_id, day_id))
            else:
                cursor.execute('INSERT INTO course_days (course_id, day_id) VALUES (?, ?)', (course_id, day_id))
                
        conn.commit()
        log_activity(session['username'], f"Creato nuovo corso: {nome}")
        flash('Corso creato con successo!', 'success')
        return redirect(url_for('courses_bp.manage_courses'))

    # Recupera i corsi unendo la tabella course_days e days per ottenere i giorni concatenati
    courses = conn.execute('''
        SELECT c.*, i.nome as i_nome, i.cognome as i_cognome, r.nome as r_nome,
               GROUP_CONCAT(d.nome, ', ') as giorni_str
        FROM courses c 
        LEFT JOIN instructors i ON c.instructor_id = i.id 
        LEFT JOIN rooms r ON c.room_id = r.id
        LEFT JOIN course_days cd ON c.id = cd.course_id
        LEFT JOIN days d ON cd.day_id = d.id
        GROUP BY c.id
    ''').fetchall()
    
    instructors = conn.execute('SELECT * FROM instructors').fetchall()
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
    days = conn.execute('SELECT * FROM days ORDER BY ordine').fetchall()
    conn.close()
    
    # Costruzione della pagina con tabella e form di inserimento
    days_checkboxes = "".join([f'<div class="form-check form-check-inline"><input class="form-check-input" type="checkbox" name="giorni" value="{d["id"]}" id="day_{d["id"]}"><label class="form-check-label" for="day_{d["id"]}">{d["nome"]}</label></div>' for d in days])
    
    instructors_options = "".join([f'<option value="{i["id"]}">{i["nome"]} {i["cognome"]}</option>' for i in instructors])
    rooms_options = "".join([f'<option value="{r["id"]}">{r["nome"]}</option>' for r in rooms])
    
    courses_rows = ""
    for c in courses:
        courses_rows += f"""
        <tr>
            <td><strong>{c['nome']}</strong><br><small class="text-muted">{c['descrizione'] or ''}</small></td>
            <td>{c['orario_inizio'] or ''} - {c['orario_fine'] or ''}</td>
            <td><span class="badge bg-info text-dark">{c['giorni_str'] or 'Nessun giorno'}</span></td>
            <td>{c['r_nome'] or 'N/D'}</td>
            <td>{c['i_nome'] or ''} {c['i_cognome'] or ''}</td>
        </tr>
        """
    if not courses:
        courses_rows = '<tr><td colspan="5" class="text-center text-muted">Nessun corso programmato al momento.</td></tr>'

    content = f"""
    <div class="row mb-4">
        <div class="col-12">
            <h2>Gestione Corsi e Orari</h2>
            <p class="text-muted">Crea e gestisci i corsi della palestra con programmazione settimanale multipla.</p>
        </div>
    </div>
    
    <div class="card shadow-sm p-4 mb-4">
        <h4 class="mb-3">Aggiungi Nuovo Corso</h4>
        <form method="POST" class="row g-3">
            <div class="col-md-4">
                <label class="form-label">Nome Corso</label>
                <input type="text" name="nome" class="form-control" required>
            </div>
            <div class="col-md-8">
                <label class="form-label">Descrizione</label>
                <input type="text" name="descrizione" class="form-control">
            </div>
            <div class="col-md-3">
                <label class="form-label">Orario Inizio</label>
                <input type="time" name="orario_inizio" class="form-control" required>
            </div>
            <div class="col-md-3">
                <label class="form-label">Orario Fine</label>
                <input type="time" name="orario_fine" class="form-control" required>
            </div>
            <div class="col-md-3">
                <label class="form-label">Sala</label>
                <select name="room_id" class="form-select">
                    <option value="">Seleziona Sala...</option>
                    {rooms_options}
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">Istruttore</label>
                <select name="instructor_id" class="form-select">
                    <option value="">Seleziona Istruttore...</option>
                    {instructors_options}
                </select>
            </div>
            <div class="col-12">
                <label class="form-label d-block">Giorni della Settimana</label>
                {days_checkboxes}
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-primary"><i class="bi bi-plus-circle"></i> Salva Corso</button>
            </div>
        </form>
    </div>

    <div class="card shadow-sm p-4">
        <h4 class="mb-3">Elenco Corsi Attivi</h4>
        <div class="table-responsive">
            <table class="table table-striped align-middle">
                <thead>
                    <tr>
                        <th>Corso</th>
                        <th>Orario</th>
                        <th>Giorni</th>
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
