from flask import Blueprint, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, log_activity, check_db_ready, init_db, DATABASE_URL
from templates_layout import render_page

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup_wizard():
    if check_db_ready():
        return redirect(url_for('auth_bp.login'))
        
    if request.method == 'POST':
        try:
            init_db()
            flash('Database configurato e popolato con successo!', 'success')
            return redirect(url_for('auth_bp.login'))
        except Exception as e:
            flash(f'Errore durante la configurazione del database: {e}', 'error')
            
    content = '''
    <div class="row justify-content-center mt-5">
        <div class="col-md-6">
            <div class="card shadow p-4 text-center">
                <h3 class="mb-3 text-primary"><i class="bi bi-gear-fill"></i> Benvenuto in GymFlow</h3>
                <p class="text-muted mb-4">Il sistema ha rilevato che il database non è ancora inizializzato. Clicca sul pulsante sottostante per creare automaticamente le tabelle, i ruoli di sistema e l'account amministratore predefinito.</p>
                <form method="POST">
                    <button type="submit" class="btn btn-success btn-lg w-100"><i class="bi bi-database-check"></i> Configura Database e Avvia</button>
                </form>
            </div>
        </div>
    </div>
    '''
    return render_page(content)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if not check_db_ready():
        return redirect(url_for('auth_bp.setup_wizard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('''
            SELECT u.*, r.name as role_name FROM sys_users u 
            JOIN roles r ON u.role_id = r.id 
            WHERE u.username = ?
        ''' if not DATABASE_URL else '''
            SELECT u.*, r.name as role_name FROM sys_users u 
            JOIN roles r ON u.role_id = r.id 
            WHERE u.username = %s
        ''', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role_name']
            log_activity(user['username'], "Accesso effettuato al sistema")
            return redirect(url_for('dashboard_bp.index'))
        flash('Credenziali non valide.', 'error')
        
    if request.args.get('timeout') == '1':
        flash('Sessione scaduta per inattività (5 minuti). Effettua nuovamente il login.', 'error')
        
    content = '''
    <div class="row justify-content-center mt-5">
        <div class="col-md-4">
            <div class="card shadow p-4">
                <h3 class="text-center mb-4">GymFlow Staff</h3>
                <form method="POST">
                    <div class="mb-3"><label class="form-label">Username</label><input type="text" name="username" class="form-control" required></div>
                    <div class="mb-3"><label class="form-label">Password</label>
                        <div class="input-group">
                            <input type="password" name="password" id="login_pass" class="form-control" required>
                            <button class="btn btn-outline-secondary" type="button" onclick="togglePassword('login_pass', 't_icon')"><i class="bi bi-eye" id="t_icon"></i></button>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Accedi</button>
                </form>
            </div>
        </div>
    </div>
    '''
    return render_page(content)

@auth_bp.route('/logout')
def logout():
    uname = session.get('username')
    if uname:
        log_activity(uname, "Disconnessione (Logout)")
    session.clear()
    timeout = request.args.get('timeout', '0')
    return redirect(url_for('auth_bp.login', timeout=timeout))

@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session: return redirect(url_for('auth_bp.login'))
    user_id = session['user_id']
    conn = get_db()
    if request.method == 'POST':
        if DATABASE_URL:
            conn.cursor().execute('UPDATE sys_users SET nome=%s, cognome=%s, email=%s, cellulare=%s WHERE id=%s',
                                  (request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare'], user_id))
        else:
            conn.cursor().execute('UPDATE sys_users SET nome=?, cognome=?, email=?, cellulare=? WHERE id=?',
                                  (request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare'], user_id))
        conn.commit()
        log_activity(session['username'], "Aggiornamento dati anagrafici personali")
        flash('Anagrafica aggiornata con successo.', 'success')
    user = conn.execute('SELECT * FROM sys_users WHERE id = ?' if not DATABASE_URL else 'SELECT * FROM sys_users WHERE id = %s', (user_id,)).fetchone()
    conn.close()
    
    content = '''
    <h2>Modifica Anagrafica Personale</h2>
    <div class="card shadow-sm p-4 mt-3">
        <form method="POST" class="row g-3">
            <div class="col-md-6"><label>Nome</label><input type="text" name="nome" class="form-control" value="{{ user.nome }}" required></div>
            <div class="col-md-6"><label>Cognome</label><input type="text" name="cognome" class="form-control" value="{{ user.cognome }}" required></div>
            <div class="col-md-6"><label>Email</label><input type="email" name="email" class="form-control" value="{{ user.email }}"></div>
            <div class="col-md-6"><label>Cellulare</label><input type="text" name="cellulare" class="form-control" value="{{ user.cellulare }}"></div>
            <div class="col-12"><button type="submit" class="btn btn-primary">Salva Modifiche</button></div>
        </form>
    </div>
    '''
    return render_page(content, user=user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session: return redirect(url_for('auth_bp.login'))
    if request.method == 'POST':
        old_pw = request.form['old_password']
        new_pw = request.form['new_password']
        confirm_pw = request.form['confirm_password']
        
        if new_pw != confirm_pw:
            flash('Le nuove password inserite non coincidono.', 'error')
        else:
            conn = get_db()
            user = conn.execute('SELECT * FROM sys_users WHERE id = ?' if not DATABASE_URL else 'SELECT * FROM sys_users WHERE id = %s', (session['user_id'],)).fetchone()
            if user and check_password_hash(user['password'], old_pw):
                hashed = generate_password_hash(new_pw)
                if DATABASE_URL:
                    conn.cursor().execute('UPDATE sys_users SET password = %s WHERE id = %s', (hashed, session['user_id']))
                else:
                    conn.cursor().execute('UPDATE sys_users SET password = ? WHERE id = ?', (hashed, session['user_id']))
                conn.commit()
                conn.close()
                log_activity(session['username'], "Modifica password account")
                flash('Password modificata con successo.', 'success')
                return redirect(url_for('dashboard_bp.index'))
            else:
                conn.close()
                flash('La vecchia password non è corretta.', 'error')
                
    content = '''
    <h2>Cambio Password</h2>
    <div class="card shadow-sm p-4 mt-3" style="max-width: 600px;">
        <form method="POST">
            <div class="mb-3">
                <label class="form-label">Vecchia Password</label>
                <div class="input-group">
                    <input type="password" name="old_password" id="op" class="form-control" required>
                    <button class="btn btn-outline-secondary" type="button" onclick="togglePassword('op', 'iop')"><i class="bi bi-eye" id="iop"></i></button>
                </div>
            </div>
            <div class="mb-3">
                <label class="form-label">Nuova Password</label>
                <div class="input-group">
                    <input type="password" name="new_password" id="np" class="form-control" required>
                    <button class="btn btn-outline-secondary" type="button" onclick="togglePassword('np', 'inp')"><i class="bi bi-eye" id="inp"></i></button>
                </div>
            </div>
            <div class="mb-3">
                <label class="form-label">Conferma Nuova Password</label>
                <div class="input-group">
                    <input type="password" name="confirm_password" id="cp" class="form-control" required>
                    <button class="btn btn-outline-secondary" type="button" onclick="togglePassword('cp', 'icp')"><i class="bi bi-eye" id="icp"></i></button>
                </div>
            </div>
            <button type="submit" class="btn btn-warning w-100">Aggiorna Password</button>
        </form>
    </div>
    '''
    return render_page(content)