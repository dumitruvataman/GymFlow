from flask import Blueprint, request, redirect, url_for, session, flash
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

app_clients_bp = Blueprint('app_clients_bp', __name__)

@app_clients_bp.route('/clients', methods=['GET', 'POST'])
def manage_clients():
    if 'user_id' not in session: return redirect(url_for('auth_bp.login'))
    conn = get_db()
    if request.method == 'POST':
        try:
            if DATABASE_URL:
                conn.cursor().execute('INSERT INTO clients (nome, cognome, email, cellulare, pin_code) VALUES (%s,%s,%s,%s,%s)',
                                      (request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare'], request.form['pin_code']))
            else:
                conn.cursor().execute('INSERT INTO clients (nome, cognome, email, cellulare, pin_code) VALUES (?,?,?,?,?)',
                                      (request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare'], request.form['pin_code']))
            conn.commit()
            log_activity(session['username'], f"Registrato nuovo cliente App: {request.form['nome']} {request.form['cognome']}")
            flash('Cliente registrato.', 'success')
        except Exception:
            flash('Email già registrata.', 'error')
    clients = conn.execute('SELECT * FROM clients').fetchall()
    conn.close()
    
    content = """
    <h2>Gestione Clienti (Accesso Web App Mobile)</h2>
    <div class="card shadow-sm mb-4 p-3">
        <h5>Nuovo Cliente</h5>
        <form method="POST" class="row g-3">
            <div class="col-md-3"><label>Nome</label><input type="text" name="nome" class="form-control" required></div>
            <div class="col-md-3"><label>Cognome</label><input type="text" name="cognome" class="form-control" required></div>
            <div class="col-md-3"><label>Email</label><input type="email" name="email" class="form-control" required></div>
            <div class="col-md-2"><label>Cellulare</label><input type="text" name="cellulare" class="form-control"></div>
            <div class="col-md-1"><label>PIN App</label><input type="text" name="pin_code" class="form-control" required></div>
            <div class="col-12"><button type="submit" class="btn btn-primary">Registra</button></div>
        </form>
    </div>
    <div class="table-responsive">
        <table class="table table-striped bg-white shadow-sm">
            <thead><tr><th>Nome</th><th>Email / Cellulare</th><th>PIN App Mobile</th></tr></thead>
            <tbody>
                {% for cl in clients %}
                <tr><td>{{ cl.nome }} {{ cl.cognome }}</td><td>{{ cl.email }} | {{ cl.cellulare }}</td><td><code>{{ cl.pin_code }}</code></td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_page(content, clients=clients)
5.