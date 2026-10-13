from flask import Blueprint, request, redirect, url_for, session, flash, jsonify
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page
from datetime import datetime, timedelta

courses_bp = Blueprint('courses_bp', __name__)

@courses_bp.route('/courses', methods=['GET', 'POST'])
def manage_courses():
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
        
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action', 'create')
        
        if action == 'create':
            nome = request.form.get('nome')
            descrizione = request.form.get('descrizione', '')
            instructor_id = request.form.get('instructor_id')
            room_id = request.form.get('room_id')
            start_date = request.form.get('start_date')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            recurrence = request.form.get('recurrence', 'none')
            repeat_until = request.form.get('repeat_until', '')
            repeat_count = request.form.get('repeat_count', '')
            
            try:
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
                
                if start_date:
                    current_date = datetime.strptime(start_date, '%Y-%m-%d')
                    end_repeat_date = datetime.strptime(repeat_until, '%Y-%m-%d') if repeat_until else current_date + timedelta(days=365)
                    max_count = int(repeat_count) if repeat_count and repeat_count.isdigit() else (365 if recurrence != 'none' else 1)
                    
                    count = 0
                    while current_date <= end_repeat_date and count < max_count:
                        date_str = current_date.strftime('%Y-%m-%d')
                        
                        if DATABASE_URL:
                            cursor.execute('INSERT INTO lesson_instances (course_id, data_lezione, stato) VALUES (%s, %s, %s)',
                                           (course_id, date_str, 'Programmata'))
                        else:
                            cursor.execute('INSERT INTO lesson_instances (course_id, data_lezione, stato) VALUES (?, ?, ?)',
                                           (course_id, date_str, 'Programmata'))
                        
                        if recurrence == 'daily':
                            current_date += timedelta(days=1)
                        elif recurrence == 'weekly':
                            current_date += timedelta(weeks=1)
                        elif recurrence == 'monthly':
                            current_date += timedelta(days=30)
                        else:
                            break
                        count += 1
                    
                conn.commit()
                log_activity(session['username'], f"Creato corso con calendario: {nome}")
                flash('Corso e programmazione calendarizzata creati con successo!', 'success')
            except Exception as e:
                conn.rollback()
                flash(f"Errore durante la creazione del corso: {e}", 'error')
                
        elif action == 'update':
            course_id = request.form.get('course_id')
            nome = request.form.get('nome')
            descrizione = request.form.get('descrizione', '')
            instructor_id = request.form.get('instructor_id')
            room_id = request.form.get('room_id')
            start_date = request.form.get('start_date')
            scope = request.form.get('scope', 'future')
            
            try:
                if DATABASE_URL:
                    cursor.execute('''UPDATE courses SET nome=%s, descrizione=%s, instructor_id=%s, room_id=%s WHERE id=%s''',
                                   (nome, descrizione, instructor_id or None, room_id or None, course_id))
                else:
                    cursor.execute('''UPDATE courses SET nome=?, descrizione=?, instructor_id=?, room_id=? WHERE id=?''',
                                   (nome, descrizione, instructor_id or None, room_id or None, course_id))
                
                if scope == 'future' and start_date:
                    target_date = request.form.get('target_date')
                    if DATABASE_URL:
                        cursor.execute('DELETE FROM lesson_instances WHERE course_id = %s AND data_lezione >= %s', (course_id, target_date))
                    else:
                        cursor.execute('DELETE FROM lesson_instances WHERE course_id = ? AND data_lezione >= ?', (course_id, target_date))
                    
                    current_date = datetime.strptime(start_date, '%Y-%m-%d')
                    for i in range(26): 
                        date_str = current_date.strftime('%Y-%m-%d')
                        if DATABASE_URL:
                            cursor.execute('INSERT INTO lesson_instances (course_id, data_lezione, stato) VALUES (%s, %s, %s)',
                                           (course_id, date_str, 'Programmata'))
                        else:
                            cursor.execute('INSERT INTO lesson_instances (course_id, data_lezione, stato) VALUES (?, ?, ?)',
                                           (course_id, date_str, 'Programmata'))
                        current_date += timedelta(weeks=1)
                        
                conn.commit()
                log_activity(session['username'], f"Aggiornato corso ID: {course_id}")
                flash('Corso e programmazione aggiornati con successo!', 'success')
            except Exception as e:
                conn.rollback()
                flash(f"Errore durante l'aggiornamento: {e}", 'error')
                
        return redirect(url_for('courses_bp.manage_courses'))

    user_id = session.get('user_id')
    user_pref = conn.execute('SELECT calendar_view FROM sys_users WHERE id = ?' if not DATABASE_URL else 'SELECT calendar_view FROM sys_users WHERE id = %s', (user_id,)).fetchone()
    current_view = user_pref['calendar_view'] if user_pref and user_pref['calendar_view'] else 'dayGridWeek'

    instructors = conn.execute('SELECT * FROM instructors').fetchall()
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
    
    lessons = conn.execute('''
        SELECT li.id as lesson_id, li.data_lezione, c.id as course_id, c.nome as corso_nome, 
               c.descrizione, c.instructor_id, c.room_id,
               r.nome as sala_nome, i.nome as i_nome, i.cognome as i_cognome
        FROM lesson_instances li
        LEFT JOIN courses c ON li.course_id = c.id
        LEFT JOIN rooms r ON c.room_id = r.id
        LEFT JOIN instructors i ON c.instructor_id = i.id
    ''').fetchall()
    
    courses_list = conn.execute('''
        SELECT c.*, r.nome as r_nome, i.nome as i_nome, i.cognome as i_cognome
        FROM courses c
        LEFT JOIN rooms r ON c.room_id = r.id
        LEFT JOIN instructors i ON c.instructor_id = i.id
    ''').fetchall()
    conn.close()
    
    instructors_options = "".join([f'<option value="{i["id"]}">{i["nome"]} {i["cognome"]}</option>' for i in instructors])
    rooms_options = "".join([f'<option value="{r["id"]}">{r["nome"]}</option>' for r in rooms])
    
    events_js = []
    for l in lessons:
        ld = dict(l)
        if ld.get('data_lezione') and ld.get('corso_nome'):
            title = f"{ld['corso_nome']} ({ld.get('sala_nome', 'Sala N/D')})"
            events_js.append(f"""{{
                id: "{ld['lesson_id']}",
                title: "{title}",
                start: "{ld['data_lezione']}",
                allDay: true,
                backgroundColor: "#0d6efd",
                borderColor: "#0d6efd",
                extendedProps: {{
                    courseId: "{ld['course_id']}",
                    corsoNome: "{ld['corso_nome']}",
                    descrizione: "{ld.get('descrizione', '') or ''}",
                    salaNome: "{ld.get('sala_nome', 'N/D')}",
                    roomID: "{ld.get('room_id', '')}",
                    istruttore: "{ld.get('i_nome', '')} {ld.get('i_cognome', '')}",
                    instructorID: "{ld.get('instructor_id', '')}",
                    dataLezione: "{ld['data_lezione']}"
                }}
            }}""")
    events_json_str = "[" + ",".join(events_js) + "]"

    courses_rows = ""
    for c in courses_list:
        cd = dict(c)
        courses_rows += f"""
        <tr>
            <td><strong>{cd.get('nome', '')}</strong><br><small class="text-muted">{cd.get('descrizione', '') or ''}</small></td>
            <td>{cd.get('r_nome', 'N/D')}</td>
            <td>{cd.get('i_nome', '')} {cd.get('i_cognome', '')}</td>
            <td>
                <form method="POST" action="/courses/delete" style="display:inline;" onsubmit="return confirm('Eliminare questo corso?');">
                    <input type="hidden" name="course_id" value="{cd.get('id')}">
                    <button type="submit" class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></button>
                </form>
            </td>
        </tr>
        """
    if not courses_list:
        courses_rows = '<tr><td colspan="4" class="text-center text-muted">Nessun corso programmato al momento.</td></tr>'

    content = f"""
    <link href='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.css' rel='stylesheet' />
    <script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.js'></script>

    <div class="row mb-4">
        <div class="col-12 d-flex justify-content-between align-items-center">
            <div>
                <h2>Calendario Corsi</h2>
                <p class="text-muted mb-0">Gestione e pianificazione dei corsi in stile Google Calendar.</p>
            </div>
            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#createCourseModal">
                <i class="bi bi-plus-lg"></i> Crea Nuovo Corso
            </button>
        </div>
    </div>

    <div class="card shadow-sm p-4 mb-4 bg-white">
        <div id="calendar" style="min-height: 650px;"></div>
    </div>

    <div class="card shadow-sm p-4">
        <h4 class="mb-3">Elenco Corsi Registrati</h4>
        <div class="table-responsive">
            <table class="table table-striped align-middle">
                <thead>
                    <tr>
                        <th>Corso</th>
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

    <!-- MODALE ANTEPRIMA EVENTO -->
    <div class="modal fade" id="eventPreviewModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-light">
                    <h5 class="modal-title" id="previewTitle">Dettagli Corso</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p><strong>Data:</strong> <span id="previewDate"></span></p>
                    <p><strong>Descrizione:</strong> <span id="previewDesc"></span></p>
                    <p><strong>Sala:</strong> <span id="previewRoom"></span></p>
                    <p><strong>Istruttore:</strong> <span id="previewInstructor"></span></p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Chiudi</button>
                    <button type="button" class="btn btn-primary" onclick="openEditModalFromPreview()">Modifica Corso</button>
                </div>
            </div>
        </div>
    </div>

    <!-- MODALE MODIFICA COMPLETA CORSO -->
    <div class="modal fade" id="editCourseModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <form method="POST">
                    <input type="hidden" name="action" value="update">
                    <input type="hidden" name="course_id" id="edit_course_id">
                    <input type="hidden" name="target_date" id="edit_target_date">
                    <div class="modal-header bg-warning text-dark">
                        <h5 class="modal-title"><i class="bi bi-pencil-square"></i> Modifica Completa Corso</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label">Nome Corso</label>
                                <input type="text" name="nome" id="edit_nome" class="form-control" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Descrizione</label>
                                <input type="text" name="descrizione" id="edit_descrizione" class="form-control">
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Sala</label>
                                <select name="room_id" id="edit_room_id" class="form-select">
                                    <option value="">Seleziona Sala...</option>
                                    {rooms_options}
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Istruttore</label>
                                <select name="instructor_id" id="edit_instructor_id" class="form-select">
                                    <option value="">Seleziona Istruttore...</option>
                                    {instructors_options}
                                </select>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Data Inizio / Riferimento</label>
                                <input type="date" name="start_date" id="edit_start_date" class="form-control" required>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Orario Inizio</label>
                                <input type="time" name="start_time" id="edit_start_time" class="form-control" value="09:00" required onchange="calculateEditEndTime()">
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Durata (minuti)</label>
                                <select id="edit_duration_minutes" class="form-select" onchange="calculateEditEndTime()">
                                    <option value="30">30 minuti</option>
                                    <option value="45">45 minuti</option>
                                    <option value="60" selected>60 minuti (1h)</option>
                                    <option value="90">90 minuti (1h 30m)</option>
                                    <option value="120">120 minuti (2h)</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Orario Fine (Calcolato)</label>
                                <input type="time" name="end_time" id="edit_end_time" class="form-control" value="10:00" required readonly>
                            </div>
                            <div class="col-12">
                                <label class="form-label fw-bold">Ambito della Modifica</label>
                                <select name="scope" class="form-select" required>
                                    <option value="future">Applica modifiche a questo evento e a tutte le ripetizioni successive</option>
                                    <option value="single">Applica modifiche solo a questo evento specifico</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annulla</button>
                        <button type="submit" class="btn btn-warning"><i class="bi bi-check-lg"></i> Salva Modifiche</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- MODALE CREAZIONE CORSO -->
    <div class="modal fade" id="createCourseModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <form method="POST">
                    <input type="hidden" name="action" value="create">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title"><i class="bi bi-calendar-event"></i> Crea Nuovo Corso / Attività</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label">Nome Corso</label>
                                <input type="text" name="nome" class="form-control" required placeholder="Es. Functional Training">
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Descrizione</label>
                                <input type="text" name="descrizione" class="form-control" placeholder="Dettagli corso...">
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
                            <div class="col-md-4">
                                <label class="form-label">Data Inizio</label>
                                <input type="date" name="start_date" id="start_date" class="form-control" required value="{datetime.now().strftime('%Y-%m-%d')}">
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Orario Inizio</label>
                                <input type="time" name="start_time" id="start_time" class="form-control" value="09:00" required onchange="calculateEndTime()">
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Durata (minuti)</label>
                                <select id="duration_minutes" class="form-select" onchange="calculateEndTime()">
                                    <option value="30">30 minuti</option>
                                    <option value="45">45 minuti</option>
                                    <option value="60" selected>60 minuti (1h)</option>
                                    <option value="90">90 minuti (1h 30m)</option>
                                    <option value="120">120 minuti (2h)</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Orario Fine (Calcolato)</label>
                                <input type="time" name="end_time" id="end_time" class="form-control" value="10:00" required readonly>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Ripetizione</label>
                                <select name="recurrence" id="recurrence" class="form-select" onchange="toggleRecurrenceOptions()">
                                    <option value="none">Non si ripete</option>
                                    <option value="daily">Ogni giorno</option>
                                    <option value="weekly" selected>Ogni settimana</option>
                                    <option value="monthly">Ogni mese</option>
                                </select>
                            </div>
                            <div class="col-md-6" id="until_box">
                                <label class="form-label">Ripeti fino alla data</label>
                                <input type="date" name="repeat_until" class="form-control">
                            </div>
                            <div class="col-md-6" id="count_box">
                                <label class="form-label">Numero massimo di ripetizioni</label>
                                <input type="number" name="repeat_count" class="form-control" placeholder="Es. 10" min="1" max="365">
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annulla</button>
                        <button type="submit" class="btn btn-primary"><i class="bi bi-check-lg"></i> Salva Corso</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
    var selectedEventData = null;

    document.addEventListener('DOMContentLoaded', function() {{
        var calendarEl = document.getElementById('calendar');
        var initialViewName = "{current_view}";

        var calendar = new FullCalendar.Calendar(calendarEl, {{
            initialView: initialViewName,
            headerToolbar: {{
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridDay,dayGridWeek,dayGridMonth'
            }},
            locale: 'it',
            buttonText: {{
                today: 'Oggi',
                month: 'Mese',
                week: 'Settimana',
                day: 'Giorno'
            }},
            events: {events_json_str},
            datesSet: function(info) {{
                var activeView = info.view.type;
                fetch('/courses/save-view', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ view: activeView }})
                }});
            }},
            dateClick: function(info) {{
                document.getElementById('start_date').value = info.dateStr;
                var myModal = new bootstrap.Modal(document.getElementById('createCourseModal'));
                myModal.show();
            }},
            eventClick: function(info) {{
                selectedEventData = info.event;
                document.getElementById('previewTitle').innerText = info.event.extendedProps.corsoNome;
                document.getElementById('previewDate').innerText = info.event.startStr;
                document.getElementById('previewDesc').innerText = info.event.extendedProps.descrizione || 'Nessuna descrizione';
                document.getElementById('previewRoom').innerText = info.event.extendedProps.salaNome;
                document.getElementById('previewInstructor').innerText = info.event.extendedProps.istruttore || 'Non assegnato';
                
                var previewModal = new bootstrap.Modal(document.getElementById('eventPreviewModal'));
                previewModal.show();
            }}
        }});
        calendar.render();
        toggleRecurrenceOptions();
    }});

    function openEditModalFromPreview() {{
        var previewModalEl = document.getElementById('eventPreviewModal');
        var previewModal = bootstrap.Modal.getInstance(previewModalEl);
        previewModal.hide();

        if (selectedEventData) {{
            document.getElementById('edit_course_id').value = selectedEventData.extendedProps.courseId;
            document.getElementById('edit_target_date').value = selectedEventData.extendedProps.dataLezione;
            document.getElementById('edit_nome').value = selectedEventData.extendedProps.corsoNome;
            document.getElementById('edit_descrizione').value = selectedEventData.extendedProps.descrizione;
            document.getElementById('edit_room_id').value = selectedEventData.extendedProps.roomID;
            document.getElementById('edit_instructor_id').value = selectedEventData.extendedProps.instructorID;
            document.getElementById('edit_start_date').value = selectedEventData.extendedProps.dataLezione;

            var editModal = new bootstrap.Modal(document.getElementById('editCourseModal'));
            editModal.show();
        }}
    }}

    function calculateEndTime() {{
        var startTime = document.getElementById('start_time').value;
        var duration = parseInt(document.getElementById('duration_minutes').value);
        if (startTime) {{
            var parts = startTime.split(':');
            var hours = parseInt(parts[0]);
            var minutes = parseInt(parts[1]);
            var date = new Date();
            date.setHours(hours);
            date.setMinutes(minutes + duration);
            document.getElementById('end_time').value = String(date.getHours()).padStart(2, '0') + ':' + String(date.getMinutes()).padStart(2, '0');
        }}
    }}

    function calculateEditEndTime() {{
        var startTime = document.getElementById('edit_start_time').value;
        var duration = parseInt(document.getElementById('edit_duration_minutes').value);
        if (startTime) {{
            var parts = startTime.split(':');
            var hours = parseInt(parts[0]);
            var minutes = parseInt(parts[1]);
            var date = new Date();
            date.setHours(hours);
            date.setMinutes(minutes + duration);
            document.getElementById('edit_end_time').value = String(date.getHours()).padStart(2, '0') + ':' + String(date.getMinutes()).padStart(2, '0');
        }}
    }}

    function toggleRecurrenceOptions() {{
        var rec = document.getElementById('recurrence').value;
        var untilBox = document.getElementById('until_box');
        var countBox = document.getElementById('count_box');
        if (rec !== 'none') {{
            untilBox.style.display = 'block';
            countBox.style.display = 'block';
        }} else {{
            untilBox.style.display = 'none';
            countBox.style.display = 'none';
        }}
    }}
    </script>
    """
    return render_page(content)

@courses_bp.route('/courses/save-view', methods=['POST'])
def save_calendar_view():
    if 'user_id' not in session:
        return jsonify({'status': 'unauthorized'}), 401
    
    data = request.get_json()
    view_name = data.get('view')
    if view_name:
        user_id = session['user_id']
        conn = get_db()
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute('UPDATE sys_users SET calendar_view = %s WHERE id = %s', (view_name, user_id))
        else:
            cursor.execute('UPDATE sys_users SET calendar_view = ? WHERE id = ?', (view_name, user_id))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

@courses_bp.route('/courses/delete', methods=['POST'])
def delete_course():
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
    course_id = request.form.get('course_id')
    conn = get_db()
    cursor = conn.cursor()
    if DATABASE_URL:
        cursor.execute('DELETE FROM lesson_instances WHERE course_id = %s', (course_id,))
        cursor.execute('DELETE FROM course_days WHERE course_id = %s', (course_id,))
        cursor.execute('DELETE FROM courses WHERE id = %s', (course_id,))
    else:
        cursor.execute('DELETE FROM lesson_instances WHERE course_id = ?', (course_id,))
        cursor.execute('DELETE FROM course_days WHERE course_id = ?', (course_id,))
        cursor.execute('DELETE FROM courses WHERE id = ?', (course_id,))
    conn.commit()
    conn.close()
    flash('Corso eliminato con successo.', 'success')
    return redirect(url_for('courses_bp.manage_courses'))
