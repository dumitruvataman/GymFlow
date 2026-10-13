from flask import Blueprint, session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/users', methods=['GET', 'POST'])
def manage_users():
    if 'user_id' not in session or session.get('role') not in ['admin', 'superuser']:
        flash('Accesso negato.', 'error')
        return redirect(url_for('dashboard_bp.index'))
        
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            username = request.form.get('username')
            password = request.form.get('password')
            role_id = request.form.get('role_id')
            nome = request.form.get('nome', '')
            cognome = request.form.get('cognome', '')
            email = request.form.get('email', '')
            cellulare = request.form.get('cellulare', '')
            
            if not username or not password:
                flash('Username e password sono obbligatori.', 'error')
            else:
                hashed_pw = generate_password_hash(password)
                try:
                    if DATABASE_URL:
                        cursor.execute('''INSERT INTO sys_users (username, password, role_id, nome, cognome, email, cellulare)
                                          VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                                       (username, hashed_pw, role_id, nome, cognome, email, cellulare))
                    else:
                        cursor.execute('''INSERT INTO sys_users (username, password, role_id, nome, cognome, email, cellulare)
                                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                       (username, hashed_pw, role_id, nome, cognome, email, cellulare))
                    conn.commit()
                    log_activity(session['username'], f"Creato nuovo utente di sistema: {username}")
                    flash('Utente creato con successo!', 'success')
                except Exception as e:
                    flash(f"Errore durante la creazione dell'utente (username già esistente?): {e}", 'error')
                    
        elif action == 'delete':
            user_id_to_del = request.form.get('user_id')
            if int(user_id_to_del) == session.get('user_id'):
                flash("Non puoi eliminare il tuo stesso account amministrativo in uso.", 'error')
            else:
                if DATABASE_URL:
                    cursor.execute('DELETE FROM sys_users WHERE id = %s', (user_id_to_del,))
                else:
                    cursor.execute('DELETE FROM sys_users WHERE id = ?', (user_id_to_del,))
                conn.commit()
                log_activity(session['username'], f"Eliminato utente ID: {user_id_to_del}")
                flash('Utente eliminato con successo.', 'success')
                
        return redirect(url_for('admin_bp.manage_users'))

    users = conn.execute('SELECT u.*, r.name as role_name FROM sys_users u LEFT JOIN roles r ON u.role_id = r.id').fetchall()
    roles = conn.execute('SELECT * FROM roles').fetchall()
    conn.close()
    
    roles_options = "".join([f'<option value="{r["id"]}">{r["name"].upper()}</option>' for r in roles])
    
    users_rows = ""
    for u in users:
        ud = dict(u)
        users_rows += f"""
        <tr>
            <td><strong>{ud.get('username', '')}</strong></td>
            <td>{ud.get('nome', '') or ''} {ud.get('cognome', '') or ''}</td>
            <td>{ud.get('email', '') or ''}</td>
            <td><span class="badge bg-secondary">{ud.get('role_name', 'N/D')}</span></td>
            <td>
                <form method="POST" style="display:inline;" onsubmit="return confirm('Confermi l\\'eliminazione di questo utente?');">
                    <input type="hidden" name="action" value="delete">
                    <input type="hidden" name="user_id" value="{ud.get('id')}">
                    <button type="submit" class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></button>
                </form>
            </td>
        </tr>
        """
    if not users:
        users_rows = '<tr><td colspan="5" class="text-center text-muted">Nessun utente registrato.</td></tr>'

    content = f"""
    <div class="row mb-4">
        <div class="col-12">
            <h2>Gestione Utenti e Permessi</h2>
            <p class="text-muted">Pannello di amministrazione per il controllo e la creazione degli accessi di sistema.</p>
        </div>
    </div>
    
    <div class="card shadow-sm p-4 mb-4">
        <h4 class="mb-3">Aggiungi Nuovo Utente</h4>
        <form method="POST" class="row g-3">
            <input type="hidden" name="action" value="create">
            <div class="col-md-3">
                <label class="form-label">Username</label>
                <input type="text" name="username" class="form-control" required>
            </div>
            <div class="col-md-3">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control" required>
            </div>
            <div class="col-md-3">
                <label class="form-label">Ruolo</label>
                <select name="role_id" class="form-select" required>
                    {roles_options}
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">Nome</label>
                <input type="text" name="nome" class="form-control">
            </div>
            <div class="col-md-4">
                <label class="form-label">Cognome</label>
                <input type="text" name="cognome" class="form-control">
            </div>
            <div class="col-md-4">
                <label class="form-label">Email</label>
                <input type="email" name="email" class="form-control">
            </div>
            <div class="col-md-4">
                <label class="form-label">Cellulare</label>
                <input type="text" name="cellulare" class="form-control">
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-primary"><i class="bi bi-person-plus-fill"></i> Crea Utente</button>
            </div>
        </form>
    </div>

    <div class="card shadow-sm p-4">
        <h4 class="mb-3">Elenco Utenti Registrati</h4>
        <div class="table-responsive">
            <table class="table table-striped align-middle">
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Nome e Cognome</th>
                        <th>Email</th>
                        <th>Ruolo</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {users_rows}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_page(content)

@admin_bp.route('/logs', methods=['GET'])
def view_logs():
    if 'user_id' not in session or session.get('role') not in ['admin', 'superuser']:
        flash('Accesso negato.', 'error')
        return redirect(url_for('dashboard_bp.index'))
        
    conn = get_db()
    logs = conn.execute('SELECT * FROM activity_logs ORDER BY timestamp DESC LIMIT 50').fetchall()
    conn.close()
    
    logs_rows = ""
    for l in logs:
        ld = dict(l)
        logs_rows += f"""
        <tr>
            <td><code>{ld.get('timestamp', '')}</code></td>
            <td><strong>{ld.get('username', '')}</strong></td>
            <td>{ld.get('action', '')}</td>
        </tr>
        """
    if not logs:
        logs_rows = '<tr><td colspan="3" class="text-center text-muted">Nessuna attività registrata.</td></tr>'

    content = f"""
    <div class="row mb-4">
        <div class="col-12">
            <h2>Registro Log Attività</h2>
            <p class="text-muted">Ultime 50 azioni registrate nel sistema.</p>
        </div>
    </div>
    
    <div class="card shadow-sm p-4">
        <div class="table-responsive">
            <table class="table table-sm table-striped align-middle">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Utente</th>
                        <th>Azione</th>
                    </tr>
                </thead>
                <tbody>
                    {logs_rows}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_page(content)
