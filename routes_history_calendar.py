from datetime import datetime, timedelta
from flask import Blueprint, request, redirect, url_for, session, flash
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

history_calendar_bp = Blueprint('history_calendar_bp', __name__)

@history_calendar_bp.route('/history-calendar')
def history_calendar():
    if 'user_id' not in session: return redirect(url_for('auth_bp.login'))
    
    # Gestione mese/anno corrente o selezionato
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    
    conn = get_db()
    # Recupera tutte le istanze di lezione registrate o genera gli appuntamenti basati sui corsi
    lessons = conn.execute('''
        SELECT l.*, c.nome as corso_nome, c.orario_inizio, c.orario_fine, r.nome as sala_nome,
               (SELECT COUNT(*) FROM bookings b WHERE b.lesson_id = l.id) as prenotati_count
        FROM lesson_instances l
        JOIN courses c ON l.course_id = c.id
        LEFT JOIN rooms r ON c.room_id = r.id
        WHERE SUBSTR(l.data_lezione, 1, 7) = ?
    ''', (f"{year:04d}-{month:02d}",)).fetchall()
    
    # Se non ci sono lezioni generate per il mese, generiamole al volo dai corsi programmati per i giorni della settimana corrispondenti
    if not lessons:
        courses = conn.execute('SELECT * FROM courses').fetchall()
        # Per semplicità dimostrativa del calendario, creiamo le istanze di lezione per il mese corrente se vuote
        # Iteriamo tutti i giorni del mese
        import calendar
        cal = calendar.monthcalendar(year, month)
        for week in cal:
            for day_idx, day_num in enumerate(week):
                if day_num != 0:
                    current_date = f"{year:04d}-{month:02d}-{day_num:02d}"
                    # giorno della settimana (0=Lunedì, 6=Domenica)
                    weekday_order = day_idx + 1 
                    # Troviamo i corsi associati a questo giorno della settimana
                    day_courses = conn.execute('''
                        SELECT c.* FROM courses c
                        JOIN course_days cd ON c.id = cd.course_id
                        JOIN days d ON cd.day_id = d.id
                        WHERE d.ordine = ?
                    ''', (weekday_order,)).fetchall()
                    for dc in day_courses:
                        # Controlla se esiste già l'istanza
                        exists = conn.execute('SELECT id FROM lesson_instances WHERE course_id = ? AND data_lezione = ?', (dc['id'], current_date)).fetchone()
                        if not exists:
                            if DATABASE_URL:
                                conn.cursor().execute('INSERT INTO lesson_instances (course_id, data_lezione) VALUES (%s, %s)', (dc['id'], current_date))
                            else:
                                conn.cursor().execute('INSERT INTO lesson_instances (course_id, data_lezione) VALUES (?, ?)', (dc['id'], current_date))
        conn.commit()
        # Ricarica lezioni
        lessons = conn.execute('''
            SELECT l.*, c.nome as corso_nome, c.orario_inizio, c.orario_fine, r.nome as sala_nome,
                   (SELECT COUNT(*) FROM bookings b WHERE b.lesson_id = l.id) as prenotati_count
            FROM lesson_instances l
            JOIN courses c ON l.course_id = c.id
            LEFT JOIN rooms r ON c.room_id = r.id
            WHERE SUBSTR(l.data_lezione, 1, 7) = ?
        ''', (f"{year:04d}-{month:02d}",)).fetchall()

    conn.close()
    
    # Raggruppa le lezioni per data (chiave: 'YYYY-MM-DD')
    lessons_by_date = {}
    for l in lessons:
        d = l['data_lezione']
        if d not in lessons_by_date:
            lessons_by_date[d] = []
        lessons_by_date[d].append(l)
        
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="bi bi-calendar3"></i> Calendario Storico Lezioni ({month}/{year})</h2>
        <div>
            <a href="/history-calendar?year={year}&month={month-1 if month > 1 else 12}" class="btn btn-outline-secondary btn-sm">Mese Precedente</a>
            <a href="/history-calendar?year={year}&month={month+1 if month < 12 else 1}" class="btn btn-outline-secondary btn-sm">Mese Successivo</a>
        </div>
    </div>

    <div class="card shadow-sm p-4 bg-white">
        <p class="text-muted">Clicca su una lezione nel calendario per visualizzare i dettagli, i clienti prenotati e registrare le presenze.</p>
        
        <div class="row row-cols-1 row-cols-md-7 g-2">
    """
    
    # Creazione griglia calendario mensile
    import calendar
    cal = calendar.monthcalendar(year, month)
    day_names = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    
    for dn in day_names:
        content += f'<div class="col text-center fw-bold bg-light border py-2">{dn}</div>'
        
    for week in cal:
        for day_idx, day_num in enumerate(week):
            if day_num == 0:
                content += '<div class="col border bg-light text-muted p-2" style="min-height: 120px;"></div>'
            else:
                date_str = f"{year:04d}-{month:02d}-{day_num:02d}"
                day_lessons = lessons_by_date.get(date_str, [])
                
                lessons_html = ""
                for dl in day_lessons:
                    lessons_html += f'''
                    <a href="/lesson-details/{dl['id']}" class="d-block text-decoration-none bg-primary text-white p-1 mb-1 rounded small" title="{dl['corso_nome']}">
                        <strong>{dl['orario_inizio']}</strong> {dl['corso_nome']} <span class="badge bg-light text-dark">{dl['prenotati_count']} pr.</span>
                    </a>
                    '''
                
                content += f'''
                <div class="col border p-1 bg-white" style="min-height: 120px; overflow-y: auto;">
                    <div class="fw-bold text-secondary border-bottom mb-1">{day_num}</div>
                    {lessons_html}
                </div>
                '''
                
    content += """
        </div>
    </div>
    """
    return render_page(content)

@history_calendar_bp.route('/lesson-details/<int:lesson_id>', methods=['GET', 'POST'])
def lesson_details(lesson_id):
    if 'user_id' not in session: return redirect(url_for('auth_bp.login'))
    conn = get_db()
    
    if request.method == 'POST':
        booking_id = request.form['booking_id']
        presenza = request.form['presenza'] # 'Presente' o 'Assente'
        if DATABASE_URL:
            conn.cursor().execute('UPDATE bookings SET presenza = %s WHERE id = %s', (presenza, booking_id))
        else:
            conn.cursor().execute('UPDATE bookings SET presenza = ? WHERE id = ?', (presenza, booking_id))
        conn.commit()
        flash('Stato presenza aggiornato.', 'success')
        
    lesson = conn.execute('''
        SELECT l.*, c.nome as corso_nome, c.descrizione, c.orario_inizio, c.orario_fine, i.nome as i_nome, i.cognome as i_cognome, r.nome as sala_nome
        FROM lesson_instances l
        JOIN courses c ON l.course_id = c.id
        LEFT JOIN instructors i ON c.instructor_id = i.id
        LEFT JOIN rooms r ON c.room_id = r.id
        WHERE l.id = ?
    ''' if not DATABASE_URL else '''
        SELECT l.*, c.nome as corso_nome, c.descrizione, c.orario_inizio, c.orario_fine, i.nome as i_nome, i.cognome as i_cognome, r.nome as sala_nome
        FROM lesson_instances l
        JOIN courses c ON l.course_id = c.id
        LEFT JOIN instructors i ON c.instructor_id = i.id
        LEFT JOIN rooms r ON c.room_id = r.id
        WHERE l.id = %s
    ''', (lesson_id,)).fetchone()
    
    bookings = conn.execute('''
        SELECT b.*, cl.nome as cl_nome, cl.cognome as cl_cognome, cl.email, cl.cellulare
        FROM bookings b
        JOIN clients cl ON b.client_id = cl.id
        WHERE b.lesson_id = ? OR (b.course_id = ? AND b.data_appuntamento = ?)
    ''' if not DATABASE_URL else '''
        SELECT b.*, cl.nome as cl_nome, cl.cognome as cl_cognome, cl.email, cl.cellulare
        FROM bookings b
        JOIN clients cl ON b.client_id = cl.id
        WHERE b.lesson_id = %s OR (b.course_id = %s AND b.data_appuntamento = %s)
    ''', (lesson_id, lesson['course_id'], lesson['data_lezione'])).fetchall()
    
    conn.close()
    
    rows_html = ""
    for b in bookings:
        badge_color = "secondary"
        if b['presenza'] == 'Presente': badge_color = "success"
        elif b['presenza'] == 'Assente': badge_color = "danger"
        
        rows_html += f"""
        <tr>
            <td><strong>{b['cl_nome']} {b['cl_cognome']}</strong></td>
            <td>{b['email']} | {b['cellulare'] or '-'}</td>
            <td><span class="badge bg-{badge_color}">{b['presenza'] or 'In attesa'}</span></td>
            <td>
                <form method="POST" class="d-inline">
                    <input type="hidden" name="booking_id" value="{b['id']}">
                    <input type="hidden" name="presenza" value="Presente">
                    <button type="submit" class="btn btn-success btn-sm"><i class="bi bi-check-lg"></i> Presente</button>
                </form>
                <form method="POST" class="d-inline">
                    <input type="hidden" name="booking_id" value="{b['id']}">
                    <input type="hidden" name="presenza" value="Assente">
                    <button type="submit" class="btn btn-danger btn-sm"><i class="bi bi-x-lg"></i> Assente</button>
                </form>
            </td>
        </tr>
        """

    content = f"""
    <div class="mb-3">
        <a href="/history-calendar" class="btn btn-outline-secondary btn-sm"><i class="bi bi-arrow-left"></i> Torna al Calendario Storico</a>
    </div>
    
    <div class="card shadow-sm p-4 mb-4 bg-white">
        <h3>Dettaglio Lezione: {lesson['corso_nome']}</h3>
        <p class="text-muted mb-2">{lesson['descrizione'] or ''}</p>
        <div class="row g-3">
            <div class="col-md-3"><strong>Data:</strong> {lesson['data_lezione']}</div>
            <div class="col-md-3"><strong>Orario:</strong> {lesson['orario_inizio']} - {lesson['orario_fine']}</div>
            <div class="col-md-3"><strong>Sala:</strong> {lesson['sala_nome'] or 'Nessuna'}</div>
            <div class="col-md-3"><strong>Istruttore:</strong> {lesson['i_nome'] or ''} {lesson['i_cognome'] or ''}</div>
        </div>
    </div>

    <h4 class="mb-3">Registro Presenze Clienti Prenotati</h4>
    <div class="table-responsive">
        <table class="table table-striped bg-white shadow-sm align-middle">
            <thead><tr><th>Cliente</th><th>Contatti</th><th>Stato Presenza</th><th>Azioni (Segna Presenza / Assenza)</th></tr></thead>
            <tbody>
                {rows_html if rows_html else '<tr><td colspan="4" class="text-center text-muted">Nessun cliente prenotato per questa lezione.</td></tr>'}
            </tbody>
        </table>
    </div>
    """
    return render_page(content)