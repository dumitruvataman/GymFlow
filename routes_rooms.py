from flask import Blueprint, request, redirect, url_for, session, flash
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

rooms_bp = Blueprint('rooms_bp', __name__)

@rooms_bp.route('/rooms', methods=['GET', 'POST'])
def manage_rooms():
    if 'user_id' not in session: return redirect(url_for('auth_bp.login'))
    conn = get_db()
    if request.method == 'POST':
        if DATABASE_URL:
            conn.cursor().execute('INSERT INTO rooms (nome, capienza) VALUES (%s, %s)', (request.form['nome'], request.form['capienza']))
        else:
            conn.cursor().execute('INSERT INTO rooms (nome, capienza) VALUES (?, ?)', (request.form['nome'], request.form['capienza']))
        conn.commit()
        log_activity(session['username'], f"Aggiunta sala: {request.form['nome']}")
        flash('Sala aggiunta.', 'success')
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
    conn.close()
    
    content = """
    <h2>Gestione Sale</h2>
    <div class="card shadow-sm mb-4 p-3">
        <h5>Nuova Sala</h5>
        <form method="POST" class="row g-3">
            <div class="col-md-5"><label>Nome</label><input type="text" name="nome" class="form-control" required></div>
            <div class="col-md-5"><label>Capienza</label><input type="number" name="capienza" class="form-control" required></div>
            <div class="col-md-2 d-flex align-items-end"><button type="submit" class="btn btn-primary w-100">Salva</button></div>
        </form>
    </div>
    <table class="table table-striped bg-white shadow-sm">
        <thead><tr><th>Nome</th><th>Capienza</th></tr></thead>
        <tbody>{% for r in rooms %}<tr><td>{{ r.nome }}</td><td>{{ r.capienza }} persone</td></tr>{% endfor %}</tbody>
    </table>
    """
    return render_page(content, rooms=rooms)