from flask import Blueprint, session, redirect, url_for, flash, request
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/admin/users', methods=['GET'])
def manage_users():
    if 'user_id' not in session or session.get('role') not in ['admin', 'superuser']:
        flash('Accesso negato.', 'error')
        return redirect(url_for('dashboard_bp.index'))
        
    conn = get_db()
    users = conn.execute('SELECT * FROM users' if 'users' in [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()] else 'SELECT 1 WHERE 0').fetchall()
    conn.close()
    
    content = """
    <h2>Gestione Utenti e Permessi</h2>
    <p class="text-muted">Pannello di amministrazione per il controllo degli accessi.</p>
    <div class="card shadow-sm p-4">
        <p>Sezione utenti attiva.</p>
    </div>
    """
    return render_page(content)
