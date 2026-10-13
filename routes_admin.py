from flask import Blueprint, session, redirect, url_for, flash, request
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/users', methods=['GET'])
def manage_users():
    if 'user_id' not in session or session.get('role') not in ['admin', 'superuser']:
        flash('Accesso negato.', 'error')
        return redirect(url_for('dashboard_bp.index'))
        
    conn = get_db()
    users = conn.execute('SELECT u.*, r.name as role_name FROM sys_users u LEFT JOIN roles r ON u.role_id = r.id').fetchall()
    conn.close()
    
    users_rows = ""
    for u in users:
        # Converte la riga in dizionario per supportare il metodo .get() sia su SQLite che su Postgres
        ud = dict(u)
        users_rows += f"""
        <tr>
            <td><strong>{ud.get('username', '')}</strong></td>
            <td>{ud.get('nome', '') or ''} {ud.get('cognome', '') or ''}</td>
            <td>{ud.get('email', '') or ''}</td>
            <td><span class="badge bg-secondary">{ud.get('role_name', 'N/D')}</span></td>
        </tr>
        """
    if not users:
        users_rows = '<tr><td colspan="4" class="text-center text-muted">Nessun utente registrato.</td></tr>'

    content = f"""
    <div class="row mb-4">
        <div class="col-12">
            <h2>Gestione Utenti e Permessi</h2>
            <p class="text-muted">Pannello di amministrazione per il controllo degli accessi di sistema.</p>
        </div>
    </div>
    
    <div class="card shadow-sm p-4">
        <div class="table-responsive">
            <table class="table table-striped align-middle">
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Nome e Cognome</th>
                        <th>Email</th>
                        <th>Ruolo</th>
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
