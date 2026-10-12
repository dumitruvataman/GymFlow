from flask import Blueprint, request, redirect, url_for, session, flash
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

courses_bp = Blueprint('courses_bp', __name__)

@courses_bp.route('/courses', methods=['GET', 'POST'])
def manage_courses():
    if 'user_id' not in session: return redirect(url_for('auth_bp.login'))
    conn = get_db()
    
    if request.method == 'POST':
        nome = request.form['nome']
        descrizione = request.form['descrizione']
        instructor_id = request.form['instructor_id']
        room_id = request.form['room_id']
        
        h_inizio = request.form['h_inizio']
        m_inizio = request.form['m_inizio']
        h_fine = request.form['h_fine']
        m_fine = request.form['m_fine']
        orario_inizio = f"{h_inizio}:{m_inizio}"
        orario_fine = f"{h_fine}:{m_fine}"
        
        selected_days = request.form.getlist('days')
        
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute('INSERT INTO courses (nome, descrizione, instructor_id, room_id, orario_inizio, orario_fine) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id',
                           (nome, descrizione, instructor_id, room_id, orario_inizio, orario_fine))
            course_id = cursor.fetchone()['id']
        else:
            cursor.execute('INSERT INTO courses (nome, descrizione, instructor_id, room_id, orario_inizio, orario_fine) VALUES (?,?,?,?,?,?)',
                           (nome, descrizione, instructor_id, room_id, orario_inizio, orario_fine))
            course_id = cursor.lastrowid
            
        for day_id in selected_days:
            if DATABASE_URL:
                cursor.execute('INSERT INTO course_days (course_id, day_id) VALUES (%s, %s)', (course_id, day_id))
            else:
                cursor.execute('INSERT INTO course_days (course_id, day_id) VALUES (?, ?)', (course_id, day_id))
                
        conn.commit()
        log_activity(session['username'], f"Creato nuovo corso con programmazione: {nome}")
        flash('Corso creato con successo.', 'success')
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
    
    ore_options = [f"{i:02d}" for i in range(24)]
    minuti_options = ["00", "10", "20", "30", "40", "50"]
    
    content = """
    <h2>Gestione Corsi, Orari e Sale</h2>
    <div class="card shadow-sm mb-4 p-4">
        <h5>Nuovo Corso con Programmazione Settimanale</h5>
        <form method="POST" class="row g-3">
            <div class="col-md-4"><label class="form-label">Nome Corso</label><input type="text" name="nome" class="form-control" required></div>
            <div class="col-md-8"><label class="form-label">Descrizione</label><input type="text" name="descrizione" class="form-control"></div>
            
            <div class="col-md-4"><label class="form-label">Istruttore</label>
                <select name="instructor_id" class="form-select">
                    {% for i in instructors %}
                    <option value="{{ i.id }}">{{ i.nome }} {{ i.cognome }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-4"><label class="form-label">Sala</label>
                <select name="room_id" class="form-select">
                    {% for r in rooms %}
                    <option value="{{ r.id }}">{{ r.nome }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="col-md-6">
                <label class="form-label d-block">Orario Inizio</label>
                <div class="input-group">
                    <select name="h_inizio" class="form-select">
                        {% for o in ore_options %}<option value="{{ o }}">{{ o }}</option>{% endfor %}
                    </select>
                    <span class="input-group-text">:</span>
                    <select name="m_inizio" class="form-select">
                        {% for m in minuti_options %}<option value="{{ m }}">{{ m }}</option>{% endfor %}
                    </select>
                </div>
            </div>
            <div class="col-md-6">
                <label class="form-label d-block">Orario Fine</label>
                <div class="input-group">
                    <select name="h_fine" class="form-select">
                        {% for o in ore_options %}<option value="{{ o }}">{{ o }}</option>{% endfor %}
                    </select>
                    <span class="input-group-text">:</span>
                    <select name="m_fine" class="form-select">
                        {% for m in minuti_options %}<option value="{{ m }}">{{ m }}</option>{% endfor %}
                    </select>
                </div>
            </div>
            
            <div class="col-12">
                <label class="form-label d-block fw-bold">Giorni della Settimana (Seleziona le spunte)</label>
                {% for d in days %}
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="checkbox" name="days" value="{{ d.id }}" id="day_{{ d.id }}">
                    <label class="form-check-label" for="day_{{ d.id }}">{{ d.nome }}</label>
                </div>
                {% endfor %}
            </div>
            
            <div class="col-12 mt-3"><button type="submit" class="btn btn-primary">Salva Corso e Programmazione</button></div>
        </form>
    </div>
    
    <div class="table-responsive">
        <table class="table table-striped bg-white shadow-sm">
            <thead><tr><th>Corso</th><th>Orario</th><th>Sala</th><th>Istruttore</th></tr></thead>
            <tbody>
                {% for c in courses %}
                <tr><td><strong>{{ c.nome }}</strong><br><small>{{ c.descrizione }}</small></td><td>{{ c.orario_inizio }} - {{ c.orario_fine }}</td><td>{{ c.r_nome }}</td><td>{{ c.i_nome }} {{ c.i_cognome }}</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_page(content, courses=courses, instructors=instructors, rooms=rooms, days=days, ore_options=ore_options, minuti_options=minuti_options)
