from flask import Blueprint, request, redirect, url_for, session, flash
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

courses_bp = Blueprint('courses_bp', __name__)

@courses_bp.route('/courses', methods=['GET', 'POST'])
def manage_courses():
    if 'user_id' not in session: return redirect(url_for('auth_bp.login'))
    conn = get_db()
    if request.method == 'POST':
        if DATABASE_URL:
            conn.cursor().execute('INSERT INTO courses (nome, descrizione, instructor_id, room_id, day_id, orario) VALUES (%s,%s,%s,%s,%s,%s)',
                                  (request.form['nome'], request.form['descrizione'], request.form['instructor_id'], request.form['room_id'], request.form['day_id'], request.form['orario']))
        else:
            conn.cursor().execute('INSERT INTO courses (nome, descrizione, instructor_id, room_id, day_id, orario) VALUES (?,?,?,?,?,?)',
                                  (request.form['nome'], request.form['descrizione'], request.form['instructor_id'], request.form['room_id'], request.form['day_id'], request.form['orario']))
        conn.commit()
        log_activity(session['username'], f"Creato nuovo corso: {request.form['nome']}")
        flash('Corso creato.', 'success')
    courses = conn.execute('''
        SELECT c.*, i.nome as i_nome, i.cognome as i_cognome, r.nome as r_nome, d.nome as giorno_nome 
        FROM courses c 
        LEFT JOIN instructors i ON c.instructor_id = i.id 
        LEFT JOIN rooms r ON c.room_id = r.id
        LEFT JOIN days d ON c.day_id = d.id
    ''').fetchall()
    instructors = conn.execute('SELECT * FROM instructors').fetchall()
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
    days = conn.execute('SELECT * FROM days ORDER BY ordine').fetchall()
    conn.close()
    
    content = """
    <h2>Gestione Corsi, Orari e Sale</h2>
    <div class="card shadow-sm mb-4 p-3">
        <h5>Nuovo Corso</h5>
        <form method="POST" class="row g-3">
            <div class="col-md-3"><label>Nome</label><input type="text" name="nome" class="form-control" required></div>
            <div class="col-md-3"><label>Descrizione</label><input type="text" name="descrizione" class="form-control"></div>
            <div class="col-md-3"><label>Istruttore</label>
                <select name="instructor_id" class="form-select">
                    {% for i in instructors %}
                    <option value="{{ i.id }}">{{ i.nome }} {{ i.cognome }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-3"><label>Sala</label>
                <select name="room_id" class="form-select">
                    {% for r in rooms %}
                    <option value="{{ r.id }}">{{ r.nome }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-3"><label>Giorno</label>
                <select name="day_id" class="form-select">
                    {% for d in days %}
                    <option value="{{ d.id }}">{{ d.nome }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-3"><label>Orario (es. 10:00 - 11:00)</label><input type="text" name="orario" class="form-control" required></div>
            <div class="col-md-6 d-flex align-items-end"><button type="submit" class="btn btn-primary w-100">Salva e Associa</button></div>
        </form>
    </div>
    <div class="table-responsive">
        <table class="table table-striped bg-white shadow-sm">
            <thead><tr><th>Corso</th><th>Giorno e Orario</th><th>Sala</th><th>Istruttore</th></tr></thead>
            <tbody>
                {% for c in courses %}
                <tr><td><strong>{{ c.nome }}</strong><br><small>{{ c.descrizione }}</small></td><td>{{ c.giorno_nome }} - {{ c.orario }}</td><td>{{ c.r_nome }}</td><td>{{ c.i_nome }} {{ c.i_cognome }}</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_page(content, courses=courses, instructors=instructors, rooms=rooms, days=days)