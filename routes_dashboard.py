from flask import Blueprint, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('auth_bp.login'))
    conn = get_db()
    courses = conn.execute('''
        SELECT c.*, i.nome as i_nome, i.cognome as i_cognome, r.nome as r_nome, d.nome as giorno_nome 
        FROM courses c 
        LEFT JOIN instructors i ON c.instructor_id = i.id 
        LEFT JOIN rooms r ON c.room_id = r.id
        LEFT JOIN days d ON c.day_id = d.id
    ''').fetchall()
    clients = conn.execute('SELECT * FROM clients').fetchall()
    days = conn.execute('SELECT * FROM days ORDER BY ordine').fetchall()
    bookings = conn.execute('''
        SELECT b.id, b.data_appuntamento, cl.nome as cl_nome, cl.cognome as cl_cognome, co.nome as co_nome, d.nome as giorno_nome, co.orario 
        FROM bookings b 
        JOIN clients cl ON b.client_id = cl.id 
        JOIN courses co ON b.course_id = co.id
        LEFT JOIN days d ON co.day_id = d.id
    ''').fetchall()
    conn.close()
    
    content = """
    <h2 class="mb-4"><i class="bi bi-calendar-week"></i> Calendario Settimanale e Prenotazioni</h2>
    
    <div class="card shadow-sm mb-4">
        <div class="card-body">
            <h5>Registra Nuova Prenotazione</h5>
            <form method="POST" action="/book" class="row g-3">
                <div class="col-md-4"><label class="form-label">Cliente</label>
                    <select name="client_id" class="form-select" required>
                        <option value="">Seleziona...</option>
                        {% for cl in clients %}
                        <option value="{{ cl.id }}">{{ cl.nome }} {{ cl.cognome }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-4"><label class="form-label">Corso</label>
                    <select name="course_id" class="form-select" required>
                        <option value="">Seleziona...</option>
                        {% for c in courses %}
                        <option value="{{ c.id }}">{{ c.nome }} ({{ c.giorno_nome }} - {{ c.orario }})</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-2"><label class="form-label">Data</label><input type="date" name="data_appuntamento" class="form-control" required></div>
                <div class="col-md-2 d-flex align-items-end"><button type="submit" class="btn btn-success w-100"><i class="bi bi-plus-circle"></i> Prenota</button></div>
            </form>
        </div>
    </div>

    <div class="row">
        {% for day in days %}
        <div class="col-md-4 mb-3">
            <div class="card h-100 shadow-sm">
                <div class="card-header bg-primary text-white"><strong>{{ day.nome }}</strong></div>
                <div class="card-body">
                    {% set ns = namespace(found=false) %}
                    {% for c in courses %}
                        {% if c.day_id == day.id %}
                            {% set ns.found = true %}
                            <div class="border-bottom pb-2 mb-2">
                                <h6>{{ c.nome }}</h6>
                                <p class="small text-muted mb-1"><i class="bi bi-clock"></i> {{ c.orario }} | <i class="bi bi-door-open"></i> {{ c.r_nome or 'Nessuna' }}<br><i class="bi bi-person-badge"></i> {{ c.i_nome }} {{ c.i_cognome }}</p>
                            </div>
                        {% endif %}
                    {% endfor %}
                    {% if not ns.found %}
                        <p class="text-muted small">Nessun corso programmato.</p>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <h3 class="mt-4">Elenco Prenotazioni Attive</h3>
    <div class="table-responsive">
        <table class="table table-striped bg-white shadow-sm rounded">
            <thead><tr><th>Data</th><th>Cliente</th><th>Corso</th><th>Giorno e Orario</th><th>Azione</th></tr></thead>
            <tbody>
                {% for b in bookings %}
                <tr>
                    <td>{{ b.data_appuntamento }}</td>
                    <td>{{ b.cl_nome }} {{ b.cl_cognome }}</td>
                    <td>{{ b.co_nome }}</td>
                    <td>{{ b.giorno_nome }} - {{ b.orario }}</td>
                    <td><a href="/booking/delete/{{ b.id }}" class="btn btn-danger btn-sm" onclick="return confirm('Eliminare?')"><i class="bi bi-trash"></i></a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_page(content, days=days, courses=courses, clients=clients, bookings=bookings)

@dashboard_bp.route('/book', methods=['POST'])
def add_booking():
    if 'user_id' not in session: return redirect(url_for('auth_bp.login'))
    conn = get_db()
    if DATABASE_URL:
        conn.cursor().execute('INSERT INTO bookings (client_id, course_id, data_appuntamento) VALUES (%s, %s, %s)', 
                              (request.form['client_id'], request.form['course_id'], request.form['data_appuntamento']))
    else:
        conn.cursor().execute('INSERT INTO bookings (client_id, course_id, data_appuntamento) VALUES (?, ?, ?)', 
                              (request.form['client_id'], request.form['course_id'], request.form['data_appuntamento']))
    conn.commit()
    conn.close()
    log_activity(session['username'], f"Registrata nuova prenotazione per cliente ID {request.form['client_id']}")
    flash('Prenotazione registrata!', 'success')
    return redirect(url_for('dashboard_bp.index'))

@dashboard_bp.route('/booking/delete/<int:id>')
def delete_booking(id):
    if 'user_id' not in session: return redirect(url_for('auth_bp.login'))
    conn = get_db()
    if DATABASE_URL:
        conn.cursor().execute('DELETE FROM bookings WHERE id = %s', (id,))
    else:
        conn.cursor().execute('DELETE FROM bookings WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    log_activity(session['username'], f"Eliminata prenotazione ID {id}")
    flash('Prenotazione rimossa.', 'success')
    return redirect(url_for('dashboard_bp.index'))

@dashboard_bp.route('/users', methods=['GET', 'POST'])
def manage_users():
    if 'user_id' not in session or session.get('role') not in ['admin', 'superuser']:
        flash('Accesso negato.', 'error')
        return redirect(url_for('dashboard_bp.index'))
    conn = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            try:
                if DATABASE_URL:
                    conn.cursor().execute('INSERT INTO sys_users (username, password, role_id, nome, cognome, email, cellulare) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                                          (request.form['username'], generate_password_hash(request.form['password']), request.form['role_id'], 
                                           request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare']))
                else:
                    conn.cursor().execute('INSERT INTO sys_users (username, password, role_id, nome, cognome, email, cellulare) VALUES (?,?,?,?,?,?,?)',
                                          (request.form['username'], generate_password_hash(request.form['password']), request.form['role_id'], 
                                           request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare']))
                conn.commit()
                log_activity(session['username'], f"Creato nuovo utente di sistema: {request.form['username']}")
                flash('Utente creato.', 'success')
            except Exception:
                flash('Username già in uso.', 'error')
        elif action == 'edit':
            u_id = request.form['user_id']
            if DATABASE_URL:
                conn.cursor().execute('UPDATE sys_users SET role_id=%s, nome=%s, cognome=%s, email=%s, cellulare=%s WHERE id=%s',
                                      (request.form['role_id'], request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare'], u_id))
            else:
                conn.cursor().execute('UPDATE sys_users SET role_id=?, nome=?, cognome=?, email=?, cellulare=? WHERE id=?',
                                      (request.form['role_id'], request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare'], u_id))
            conn.commit()
            log_activity(session['username'], f"Modificato utente di sistema ID {u_id}")
            flash('Utente aggiornato con successo.', 'success')
            
    users = conn.execute('''
        SELECT u.*, r.name as role_name FROM sys_users u 
        JOIN roles r ON u.role_id = r.id
    ''').fetchall()
    roles = conn.execute('SELECT * FROM roles').fetchall()
    conn.close()
    
    content = """
    <h2>Gestione Utenti di Sistema</h2>
    <div class="card shadow-sm mb-4 p-3">
        <h5>Nuovo Utente</h5>
        <form method="POST" class="row g-3">
            <input type="hidden" name="action" value="add">
            <div class="col-md-3"><label>Username</label><input type="text" name="username" class="form-control" required></div>
            <div class="col-md-3"><label>Password</label>
                <div class="input-group">
                    <input type="password" name="password" id="nu_pass" class="form-control" required>
                    <button class="btn btn-outline-secondary" type="button" onclick="togglePassword('nu_pass', 'i_nu')"><i class="bi bi-eye" id="i_nu"></i></button>
                </div>
            </div>
            <div class="col-md-2"><label>Ruolo</label>
                <select name="role_id" class="form-select">
                    {% for r in roles %}
                        {% if session.get('role') == 'admin' or r.name != 'admin' %}
                        <option value="{{ r.id }}">{{ r.name }}</option>
                        {% endif %}
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-2"><label>Nome</label><input type="text" name="nome" class="form-control"></div>
            <div class="col-md-2"><label>Cognome</label><input type="text" name="cognome" class="form-control"></div>
            <div class="col-md-4"><label>Email</label><input type="email" name="email" class="form-control"></div>
            <div class="col-md-3"><label>Cellulare</label><input type="text" name="cellulare" class="form-control"></div>
            <div class="col-md-2 d-flex align-items-end"><button type="submit" class="btn btn-primary w-100">Crea</button></div>
        </form>
    </div>
    
    <div class="table-responsive">
        <table class="table table-striped bg-white shadow-sm align-middle">
            <thead><tr><th>Username</th><th>Ruolo</th><th>Nome</th><th>Contatti</th><th>Azioni / Modifica</th></tr></thead>
            <tbody>
                {% for u in users %}
                <tr>
                    <td><strong>{{ u.username }}</strong></td>
                    <td><span class="badge bg-secondary">{{ u.role_name }}</span></td>
                    <td>{{ u.nome }} {{ u.cognome }}</td>
                    <td>{{ u.email }}<br>{{ u.cellulare }}</td>
                    <td>
                        <button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#editModal{{ u.id }}"><i class="bi bi-pencil-square"></i> Modifica</button>
                        
                        <div class="modal fade" id="editModal{{ u.id }}" tabindex="-1">
                          <div class="modal-dialog">
                            <form method="POST" class="modal-content">
                              <input type="hidden" name="action" value="edit">
                              <input type="hidden" name="user_id" value="{{ u.id }}">
                              <div class="modal-header">
                                <h5 class="modal-title">Modifica Utente: {{ u.username }}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                              </div>
                              <div class="modal-body text-start">
                                <div class="mb-3"><label>Nome</label><input type="text" name="nome" class="form-control" value="{{ u.nome }}"></div>
                                <div class="mb-3"><label>Cognome</label><input type="text" name="cognome" class="form-control" value="{{ u.cognome }}"></div>
                                <div class="mb-3"><label>Email</label><input type="email" name="email" class="form-control" value="{{ u.email }}"></div>
                                <div class="mb-3"><label>Cellulare</label><input type="text" name="cellulare" class="form-control" value="{{ u.cellulare }}"></div>
                                <div class="mb-3"><label>Ruolo</label>
                                    <select name="role_id" class="form-select">
                                        {% for r in roles %}
                                        <option value="{{ r.id }}" {% if r.id == u.role_id %}selected{% endif %}>{{ r.name }}</option>
                                        {% endfor %}
                                    </select>
                                </div>
                              </div>
                              <div class="modal-footer">
                                <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Chiudi</button>
                                <button type="submit" class="btn btn-success btn-sm">Salva Modifiche</button>
                              </div>
                            </form>
                          </div>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_page(content, users=users, roles=roles)

@dashboard_bp.route('/logs')
def view_logs():
    if 'user_id' not in session or session.get('role') not in ['admin', 'superuser']:
        flash('Accesso negato.', 'error')
        return redirect(url_for('dashboard_bp.index'))
    conn = get_db()
    logs = conn.execute('SELECT * FROM system_logs ORDER BY id DESC LIMIT 100').fetchall()
    conn.close()
    
    content = '''
    <h2>Registro Log Attività di Sistema</h2>
    <p class="text-muted">Ultime 100 operazioni eseguite dagli utenti sulla piattaforma.</p>
    <div class="table-responsive">
        <table class="table table-striped bg-white shadow-sm">
            <thead><tr><th>Data e Ora</th><th>Utente</th><th>Attività Eseguita</th></tr></thead>
            <tbody>
                {% for l in logs %}
                <tr>
                    <td><code>{{ l.timestamp }}</code></td>
                    <td><strong>{{ l.username }}</strong></td>
                    <td>{{ l.action }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    '''
    return render_page(content, logs=logs)