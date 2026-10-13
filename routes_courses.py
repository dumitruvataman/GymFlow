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
        giorni_selezionati = request.form.getlist('giorni')
        
        if DATABASE_URL:
            cursor.execute('''INSERT INTO courses (nome, descrizione, instructor_id, room_id)
                              VALUES (%s, %s, %s, %s) RETURNING id''',
                           (nome, descrizione, instructor_id or None, room_id or None))
            course_id = cursor.fetchone()['id']
        else:
            cursor.execute('''INSERT INTO courses (nome, descrizione, instructor_id, room_id)
                              VALUES (?, ?, ?, ?)''',
                           (nome, descrizione, instructor_id or None, room_id or None))
            course_id = cursor.lastrowid
            
        for day_id in giorni_selezionati:
            h_i = request.form.get(f'ora_inizio_{day_id}', '08')
            m_i = request.form.get(f'min_inizio_{day_id}', '00')
            h_f = request.form.get(f'ora_fine_{day_id}', '09')
            m_f = request.form.get(f'min_fine_{day_id}', '00')
            
            orario_inizio = f"{h_i}:{m_i}"
            orario_fine = f"{h_f}:{m_f}"
            
            if DATABASE_URL:
                cursor.execute('INSERT INTO course_days (course_id, day_id, orario_inizio, orario_fine) VALUES (%s, %s, %s, %s)', 
                               (course_id, day_id, orario_inizio, orario_fine))
            else:
                cursor.execute('INSERT INTO course_days (course_id, day_id, orario_inizio, orario_fine) VALUES (?, ?, ?, ?)', 
                               (course_id, day_id, orario_inizio, orario_fine))
                
        conn.commit()
        log_activity(session['username'], f"Creato nuovo corso con orari differenziati: {nome}")
        flash('Corso creato con successo!', 'success')
        return redirect(url_for('courses_bp.manage_courses'))

    courses = conn.execute('''
        SELECT c.*, i.nome as i_nome, i.cognome as i_cognome, r.nome as r_nome
        FROM courses c 
        LEFT JOIN instructors i ON c.instructor_id = i.id 
        LEFT JOIN rooms r ON c.room_id = r.id
    ''').fetchall()
    
    instructors = conn.execute('SELECT * FROM instructors').fetchall()
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
    days = conn.execute('SELECT * FROM days ORDER BY ordine').fetchall()
    conn.close()
    
    instructors_options = "".join([f'<option value="{i["id"]}">{i["nome"]} {i["cognome"]}</option>' for i in instructors])
    rooms_options = "".join([f'<option value="{r["id"]}">{r["nome"]}</option>' for r in rooms])
    
    ore_options = "".join([f'<option value="{h:02d}">{h:02d}</option>' for h in range(24)])
    minuti_options = "".join([f'<option value="{m:02d}">{m:02d}</option>' for m in range(0, 60, 10)])
    
    days_builder = ""
    for d in days:
        d_id = d['id']
        d_nome = d['nome']
        days_builder += f"""
        <div class="card mb-2 p-3 bg-white border">
            <div class="form-check mb-2">
                <input class="form-check-input day-checkbox" type="checkbox" name="giorni" value="{d_id}" id="day_{d_id}" onchange="toggleDayTime({d_id})">
                <label class="form-check-label fw-bold" for="day_{d_id}">{d_nome}</label>
            </div>
            <div id="time_box_{d_id}" class="row g-2 d-none">
                <div class="col-md-6">
                    <label class="form-label small text-muted">Inizio ({d_nome})</label>
                    <div class="input-group input-group-sm">
                        <select name="ora_inizio_{d_id}" class="form-select">{ore_options}</select>
                        <span class="input-group-text">:</span>
                        <select name="min_inizio_{d_id}" class="form-select">{minuti_options}</select>
                    </div>
                </div>
                <div class="col-md-6">
                    <label class="form-label small text-muted">Fine ({d_nome})</label>
                    <div class="input-group input-group-sm">
                        <select name="ora_fine_{d_id}" class="form-select">{ore_options}</select>
                        <span class="input-group-text">:</span>
                        <select name="min_fine_{d_id}" class="form-select">{minuti_options}</select>
                    </div>
                </div>
            </div>
        </div>
        """
    
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
            <td>
                <form method="POST" action="/courses/delete" style="display:inline;" onsubmit="return confirm('Eliminare questo corso?');">
                    <input type="hidden" name="course_id" value="{c['id']}">
                    <button type="submit" class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></button>
                </form>
            </td>
        </tr>
        """
    if not courses:
        courses_rows = '<tr><td colspan="5" class="text-center text-muted">Nessun corso programmato al momento.</td></tr>'

    content = f"""
    <div class="row mb-4">
        <div class="col-12">
            <h2>Gestione Corsi e Orari</h2>
            <p class="text-muted">Crea corsi impostando giorni e orari personalizzati (con intervalli di 10 minuti).</p>
        </div>
    </div>
    
    <div class="card shadow-sm p-4 mb-4">
        <h4 class="mb-3">Aggiungi Nuovo Corso</h4>
        <form method="POST" class="row g-3">
            <div class="col-md-6">
                <label class="form-label">Nome Corso</label>
                <input type="text" name="nome" class="form-control" required>
            </div>
            <div class="col-md-6">
                <label class="form-label">Descrizione</label>
                <input type="text" name="descrizione" class="form-control">
            </div>
            <div class="col-md-6">
                <label class="form-label">Sala</label>
                <select name="room_id" class="form-select">
                    <option value="">Seleziona Sala...</option>
                    {rooms_options}
                </select>
            </div>
            <div class="col-md-6">
                <label class="form-label">Istruttore</label>
                <select name="instructor_id" class="form-select">
                    <option value="">Seleziona Istruttore...</option>
                    {instructors_options}
                </select>
            </div>
            <div class="col-12">
                <label class="form-label fw-bold d-block mt-2">Giorni della Settimana e Orari Dedicati</label>
                <p class="text-muted small">Seleziona i giorni in cui si svolge il corso per abilitare la selezione dell'orario specifico.</p>
                {days_builder}
            </div>
            <div class="col-12 mt-3">
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
                        <th>Programmazione e Orari per Giorno</th>
                        <th>Sala</th>
                        <th>Istruttore</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {courses_rows}
                </tbody>
            </table>
        </div>
    </div>

    <script>
    function toggleDayTime(dayId) {{
        const checkbox = document.getElementById('day_' + dayId);
        const timeBox = document.getElementById('time_box_' + dayId);
        if (checkbox.checked) {{
            timeBox.classList.remove('d-none');
        }} else {{
            timeBox.classList.add('d-none');
        }}
    }}
    </script>
    """
    return render_page(content, courses=courses)

@courses_bp.route('/courses/delete', methods=['POST'])
def delete_course():
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
    course_id = request.form.get('course_id')
    conn = get_db()
    cursor = conn.cursor()
    if DATABASE_URL:
        cursor.execute('DELETE FROM course_days WHERE course_id = %s', (course_id,))
        cursor.execute('DELETE FROM courses WHERE id = %s', (course_id,))
    else:
        cursor.execute('DELETE FROM course_days WHERE course_id = ?', (course_id,))
        cursor.execute('DELETE FROM courses WHERE id = ?', (course_id,))
    conn.commit()
    conn.close()
    flash('Corso eliminato con successo.', 'success')
    return redirect(url_for('courses_bp.manage_courses'))
