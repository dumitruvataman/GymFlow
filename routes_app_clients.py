from flask import Blueprint, request, redirect, url_for, session, flash
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

app_clients_bp = Blueprint('app_clients_bp', __name__)

@app_clients_bp.route('/clients', methods=['GET', 'POST'])
def manage_clients():
    if 'user_id' not in session: 
        return redirect(url_for('auth_bp.login'))
        
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        email = request.form.get('email')
        cellulare = request.form.get('cellulare', '')
        pin_code = request.form.get('pin_code')
        
        try:
            if DATABASE_URL:
                cursor.execute('INSERT INTO clients (nome, cognome, email, cellulare, pin_code) VALUES (%s,%s,%s,%s,%s)',
                               (nome, cognome, email, cellulare, pin_code))
            else:
                cursor.execute('INSERT INTO clients (nome, cognome, email, cellulare, pin_code) VALUES (?,?,?,?,?)',
                               (nome, cognome, email, cellulare, pin_code))
            conn.commit()
            log_activity(session['username'], f"Registrato nuovo cliente App: {nome} {cognome}")
            flash('Cliente registrato con successo.', 'success')
        except Exception as e:
            conn.rollback()
            err_str = str(e).lower()
            if 'unique' in err_str or 'duplicate' in err_str:
                flash('Questo indirizzo email risulta già registrato.', 'error')
            else:
                flash(f"Errore durante la registrazione: {e}", 'error')
                
    clients = conn.execute('SELECT * FROM clients').fetchall()
    conn.close()
    
    content = f"""
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
        <table class="table table-striped bg-white shadow-sm align-middle">
            <thead>
                <tr>
                    <th>Nome</th>
                    <th>Email / Cellulare</th>
                    <th>PIN App Mobile</th>
                </tr>
            </thead>
            <tbody>
    """
    
    rows = ""
    for cl in clients:
        c_dict = dict(cl)
        rows += f"""
        <tr>
            <td>{c_dict.get('nome', '')} {c_dict.get('cognome', '')}</td>
            <td>{c_dict.get('email', '')} | {c_dict.get('cellulare', '') or 'N/D'}</td>
            <td><code>{c_dict.get('pin_code', '')}</code></td>
        </tr>
        """
        
    if not clients:
        rows = '<tr><td colspan="3" class="text-center text-muted">Nessun cliente registrato al momento.</td></tr>'
        
    content += rows + """
            </tbody>
        </table>
    </div>
    """
    return render_page(content, clients=clients)
