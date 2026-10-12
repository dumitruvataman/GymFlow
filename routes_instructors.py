from flask import Blueprint, request, redirect, url_for, session, flash
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

instructors_bp = Blueprint('instructors_bp', __name__)

@instructors_bp.route('/instructors', methods=['GET', 'POST'])
def manage_instructors():
    if 'user_id' not in session: return redirect(url_for('auth_bp.login'))
    conn = get_db()
    if request.method == 'POST':
        if DATABASE_URL:
            conn.cursor().execute('INSERT INTO instructors (nome, cognome, email, cellulare, specialita) VALUES (%s,%s,%s,%s,%s)',
                                  (request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare'], request.form['specialita']))
        else:
            conn.cursor().execute('INSERT INTO instructors (nome, cognome, email, cellulare, specialita) VALUES (?,?,?,?,?)',
                                  (request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare'], request.form['specialita']))
        conn.commit()
        log_activity(session['username'], f"Aggiunto istruttore: {request.form['nome']} {request.form['cognome']}")
        flash('Istruttore aggiunto.', 'success')
    instructors = conn.execute('SELECT * FROM instructors').fetchall()
    conn.close()
    
    content = """
    <h2>Gestione Istruttori</h2>
    <div class="card shadow-sm mb-4 p-3">
        <h5>Nuovo Istruttore</h5>
        <form method="POST" class="row g-3">
            <div class="col-md-3"><label>Nome</label><input type="text" name="nome" class="form-control" required></div>
            <div class="col-md-3"><label>Cognome</label><input type="text" name="cognome" class="form-control" required></div>
            <div class="col-md-3"><label>Email</label><input type="email" name="email" class="form-control"></div>
            <div class="col-md-3"><label>Cellulare</label><input type="text" name="cellulare" class="form-control"></div>
            <div class="col-md-9"><label>Specialità</label><input type="text" name="specialita" class="form-control"></div>
            <div class="col-md-3 d-flex align-items-end"><button type="submit" class="btn btn-primary w-100">Salva</button></div>
        </form>
    </div>
    <div class="table-responsive">
        <table class="table table-striped bg-white shadow-sm">
            <thead><tr><th>Nome</th><th>Specialità</th><th>Contatti</th></tr></thead>
            <tbody>
                {% for i in instructors %}
                <tr><td>{{ i.nome }} {{ i.cognome }}</td><td>{{ i.specialita }}</td><td>{{ i.email }} | {{ i.cellulare }}</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_page(content, instructors=instructors)