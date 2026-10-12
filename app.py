import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'chiave_segreta_palestra_super_sicura_render'
DB_NAME = 'palestra.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            nome TEXT,
            cognome TEXT,
            email TEXT,
            cellulare TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instructors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cognome TEXT NOT NULL,
            email TEXT,
            cellulare TEXT,
            specialita TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            capienza INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descrizione TEXT,
            instructor_id INTEGER,
            room_id INTEGER,
            giorno TEXT,
            orario TEXT,
            FOREIGN KEY(instructor_id) REFERENCES instructors(id),
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pin_code TEXT NOT NULL,
            nome TEXT NOT NULL,
            cognome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            cellulare TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            course_id INTEGER,
            data_appuntamento TEXT,
            stato TEXT DEFAULT 'Confermato',
            FOREIGN KEY(client_id) REFERENCES clients(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')
    
    cursor.execute("SELECT * FROM sys_users WHERE username = 'admin'")
    if not cursor.fetchone():
        hashed_pw = generate_password_hash('admin123')
        cursor.execute("INSERT INTO sys_users (username, password, role, nome, cognome, email, cellulare) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ('admin', hashed_pw, 'admin', 'Amministratore', 'Generale', 'admin@palestra.it', '3330000000'))
                       
    conn.commit()
    conn.close()

init_db()

# --- TEMPLATE LAYOUT ADMIN ---
LAYOUT_ADMIN = '''
<!doctype html>
<html lang="it">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>GymManager Gestione</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
</head>
<body class="bg-light">
    {% if session.get('user_id') %}
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
        <div class="container-fluid">
            <a class="navbar-brand" href="/"><i class="bi bi-activity"></i> GymManager Admin</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link" href="/">Calendario & Prenotazioni</a></li>
                    <li class="nav-item"><a class="nav-link" href="/courses">Corsi</a></li>
                    <li class="nav-item"><a class="nav-link" href="/instructors">Istruttori</a></li>
                    <li class="nav-item"><a class="nav-link" href="/rooms">Sale</a></li>
                    <li class="nav-item"><a class="nav-link" href="/clients">Clienti (App)</a></li>
                    {% if session.get('role') in ['admin', 'superuser'] %}
                    <li class="nav-item"><a class="nav-link" href="/users">Utenti Sistema</a></li>
                    {% endif %}
                </ul>
                <span class="navbar-text text-white me-3 d-none d-lg-inline">
                    {{ session.get('username') }} ({{ session.get('role') }})
                </span>
                <a href="/logout" class="btn btn-outline-light btn-sm">Esci</a>
            </div>
        </div>
    </nav>
    {% endif %}

    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {{ body|safe }}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function togglePassword(fieldId, btnId) {
            const input = document.getElementById(fieldId);
            const icon = document.getElementById(btnId);
            if (input.type === "password") {
                input.type = "text";
                icon.classList.remove("bi-eye");
                icon.classList.add("bi-eye-slash");
            } else {
                input.type = "password";
                icon.classList.remove("bi-eye-slash");
                icon.classList.add("bi-eye");
            }
        }
    </script>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM sys_users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
        flash('Credenziali non valide.', 'error')
        
    content = '''
    <div class="row justify-content-center mt-5">
        <div class="col-md-4">
            <div class="card shadow p-4">
                <h3 class="text-center mb-4">Accesso Staff</h3>
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
    return render_template_string(LAYOUT_ADMIN, body=content)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    courses = conn.execute('''
        SELECT c.*, i.nome as i_nome, i.cognome as i_cognome, r.nome as r_nome 
        FROM courses c LEFT JOIN instructors i ON c.instructor_id = i.id LEFT JOIN rooms r ON c.room_id = r.id
    ''').fetchall()
    clients = conn.execute('SELECT * FROM clients').fetchall()
    bookings = conn.execute('''
        SELECT b.id, b.data_appuntamento, cl.nome as cl_nome, cl.cognome as cl_cognome, co.nome as co_nome, co.giorno, co.orario 
        FROM bookings b JOIN clients cl ON b.client_id = cl.id JOIN courses co ON b.course_id = co.id
    ''').fetchall()
    conn.close()
    
    giorni = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
    
    # HTML formattato correttamente come stringa multilinea senza interruzioni nei tag Jinja
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
                        <option value="{{ c.id }}">{{ c.nome }} ({{ c.giorno }} - {{ c.orario }})</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-2"><label class="form-label">Data</label><input type="date" name="data_appuntamento" class="form-control" required></div>
                <div class="col-md-2 d-flex align-items-end"><button type="submit" class="btn btn-success w-100"><i class="bi bi-plus-circle"></i> Prenota</button></div>
            </form>
        </div>
    </div>

    <div class="row">
        {% for g in giorni %}
        <div class="col-md-4 mb-3">
            <div class="card h-100 shadow-sm">
                <div class="card-header bg-primary text-white"><strong>{{ g }}</strong></div>
                <div class="card-body">
                    {% set ns = namespace(found=false) %}
                    {% for c in courses %}
                        {% if c.giorno == g %}
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
            <thead><tr><th>Data</th><th>Cliente</th><th>Corso</th><th>Orario</th><th>Azione</th></tr></thead>
            <tbody>
                {% for b in bookings %}
                <tr>
                    <td>{{ b.data_appuntamento }}</td>
                    <td>{{ b.cl_nome }} {{ b.cl_cognome }}</td>
                    <td>{{ b.co_nome }}</td>
                    <td>{{ b.giorno }} - {{ b.orario }}</td>
                    <td><a href="/booking/delete/{{ b.id }}" class="btn btn-danger btn-sm" onclick="return confirm('Eliminare?')"><i class="bi bi-trash"></i></a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_template_string(LAYOUT_ADMIN, body=content, giorni=giorni, courses=courses, clients=clients, bookings=bookings)

@app.route('/book', methods=['POST'])
def add_booking():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    conn.execute('INSERT INTO bookings (client_id, course_id, data_appuntamento) VALUES (?, ?, ?)', 
                 (request.form['client_id'], request.form['course_id'], request.form['data_appuntamento']))
    conn.commit()
    conn.close()
    flash('Prenotazione registrata!', 'success')
    return redirect(url_for('index'))

@app.route('/booking/delete/<int:id>')
def delete_booking(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM bookings WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Prenotazione rimossa.', 'success')
    return redirect(url_for('index'))

@app.route('/users', methods=['GET', 'POST'])
def manage_users():
    if 'user_id' not in session or session.get('role') not in ['admin', 'superuser']:
        flash('Accesso negato.', 'error')
        return redirect(url_for('index'))
    conn = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            try:
                conn.execute('INSERT INTO sys_users (username, password, role, nome, cognome, email, cellulare) VALUES (?,?,?,?,?,?,?)',
                             (request.form['username'], generate_password_hash(request.form['password']), request.form['role'], 
                              request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare']))
                conn.commit()
                flash('Utente creato.', 'success')
            except sqlite3.IntegrityError:
                flash('Username già in uso.', 'error')
        elif action == 'change_password':
            conn.execute('UPDATE sys_users SET password = ? WHERE id = ?', 
                         (generate_password_hash(request.form['new_password']), request.form['user_id']))
            conn.commit()
            flash('Password aggiornata.', 'success')
    users = conn.execute('SELECT * FROM sys_users').fetchall()
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
                <select name="role" class="form-select">
                    <option value="user">User</option>
                    {% if session.get('role') == 'admin' %}
                    <option value="superuser">Superuser</option>
                    <option value="admin">Admin</option>
                    {% endif %}
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
        <table class="table table-striped bg-white shadow-sm">
            <thead><tr><th>Username</th><th>Ruolo</th><th>Nome</th><th>Contatti</th><th>Cambio Password</th></tr></thead>
            <tbody>
                {% for u in users %}
                <tr>
                    <td><strong>{{ u.username }}</strong></td>
                    <td><span class="badge bg-secondary">{{ u.role }}</span></td>
                    <td>{{ u.nome }} {{ u.cognome }}</td>
                    <td>{{ u.email }}<br>{{ u.cellulare }}</td>
                    <td>
                        <form method="POST" class="row g-1">
                            <input type="hidden" name="action" value="change_password">
                            <input type="hidden" name="user_id" value="{{ u.id }}">
                            <div class="col">
                                <div class="input-group input-group-sm">
                                    <input type="password" name="new_password" id="p_{{ u.id }}" class="form-control" placeholder="Nuova password" required>
                                    <button class="btn btn-outline-secondary" type="button" onclick="togglePassword('p_{{ u.id }}', 'ip_{{ u.id }}')"><i class="bi bi-eye" id="ip_{{ u.id }}"></i></button>
                                </div>
                            </div>
                            <div class="col-auto"><button type="submit" class="btn btn-warning btn-sm">Aggiorna</button></div>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_template_string(LAYOUT_ADMIN, body=content, users=users)

@app.route('/instructors', methods=['GET', 'POST'])
def manage_instructors():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        conn.execute('INSERT INTO instructors (nome, cognome, email, cellulare, specialita) VALUES (?,?,?,?,?)',
                     (request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare'], request.form['specialita']))
        conn.commit()
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
    return render_template_string(LAYOUT_ADMIN, body=content, instructors=instructors)

@app.route('/rooms', methods=['GET', 'POST'])
def manage_rooms():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        conn.execute('INSERT INTO rooms (nome, capienza) VALUES (?, ?)', (request.form['nome'], request.form['capienza']))
        conn.commit()
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
    return render_template_string(LAYOUT_ADMIN, body=content, rooms=rooms)

@app.route('/courses', methods=['GET', 'POST'])
def manage_courses():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        conn.execute('INSERT INTO courses (nome, descrizione, instructor_id, room_id, giorno, orario) VALUES (?,?,?,?,?,?)',
                     (request.form['nome'], request.form['descrizione'], request.form['instructor_id'], request.form['room_id'], request.form['giorno'], request.form['orario']))
        conn.commit()
        flash('Corso creato.', 'success')
    courses = conn.execute('SELECT c.*, i.nome as i_nome, r.nome as r_nome FROM courses c LEFT JOIN instructors i ON c.instructor_id=i.id LEFT JOIN rooms r ON c.room_id=r.id').fetchall()
    instructors = conn.execute('SELECT * FROM instructors').fetchall()
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
    conn.close()
    giorni = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
    
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
                <select name="giorno" class="form-select">
                    {% for g in giorni %}
                    <option value="{{ g }}">{{ g }}</option>
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
                <tr><td><strong>{{ c.nome }}</strong><br><small>{{ c.descrizione }}</small></td><td>{{ c.giorno }} - {{ c.orario }}</td><td>{{ c.r_nome }}</td><td>{{ c.i_nome }}</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_template_string(LAYOUT_ADMIN, body=content, courses=courses, instructors=instructors, rooms=rooms, giorni=giorni)

@app.route('/clients', methods=['GET', 'POST'])
def manage_clients():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        try:
            conn.execute('INSERT INTO clients (nome, cognome, email, cellulare, pin_code) VALUES (?,?,?,?,?)',
                         (request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare'], request.form['pin_code']))
            conn.commit()
            flash('Cliente registrato.', 'success')
        except sqlite3.IntegrityError:
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
    return render_template_string(LAYOUT_ADMIN, body=content, clients=clients)


# ==========================================================
# --- AREA RISERVATA CLIENTE (WEB APP MOBILE / RESPONSIVE) ---
# ==========================================================

@app.route('/client/login', methods=['GET', 'POST'])
def client_login():
    if request.method == 'POST':
        conn = get_db()
        client = conn.execute('SELECT * FROM clients WHERE email = ? AND pin_code = ?', 
                              (request.form['email'], request.form['pin_code'])).fetchone()
        conn.close()
        if client:
            session['client_id'] = client['id']
            session['client_name'] = f"{client['nome']} {client['cognome']}"
            return redirect(url_for('client_dashboard'))
        flash('Email o PIN errati.', 'error')
        
    return render_template_string('''
    <!doctype html>
    <html lang="it">
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Area Clienti Palestra</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light d-flex align-items-center py-4" style="min-height: 100vh;">
        <div class="container text-center" style="max-width: 400px;">
            <div class="card shadow p-4">
                <h3 class="mb-3">Accesso Area Clienti</h3>
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}{% for cat, msg in messages %}<div class="alert alert-danger">{{ msg }}</div>{% endfor %}{% endif %}
                {% endwith %}
                <form method="POST">
                    <div class="mb-3 text-start"><label class="form-label">Email</label><input type="email" name="email" class="form-control" required></div>
                    <div class="mb-3 text-start"><label class="form-label">PIN Personale</label><input type="password" name="pin_code" class="form-control" required></div>
                    <button type="submit" class="btn btn-success w-100">Accedi</button>
                </form>
            </div>
        </div>
    </body></html>
    ''')

@app.route('/client/dashboard', methods=['GET', 'POST'])
def client_dashboard():
    if 'client_id' not in session: return redirect(url_for('client_login'))
    client_id = session['client_id']
    conn = get_db()
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile':
            conn.execute('UPDATE clients SET nome=?, cognome=?, email=?, cellulare=? WHERE id=?', 
                         (request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare'], client_id))
            conn.commit()
            flash('Dati anagrafici aggiornati!', 'success')
        elif action == 'book_course':
            conn.execute('INSERT INTO bookings (client_id, course_id, data_appuntamento, stato) VALUES (?, ?, ?, ?)',
                         (client_id, request.form['course_id'], request.form['data_appuntamento'], 'Confermato'))
            conn.commit()
            flash('Appuntamento prenotato con successo!', 'success')
        elif action == 'cancel_booking':
            conn.execute('DELETE FROM bookings WHERE id = ? AND client_id = ?', (request.form['booking_id'], client_id))
            conn.commit()
            flash('Prenotazione cancellata.', 'success')
            
    client = conn.execute('SELECT * FROM clients WHERE id = ?', (client_id,)).fetchone()
    courses = conn.execute('SELECT c.*, r.nome as r_nome FROM courses c LEFT JOIN rooms r ON c.room_id=r.id').fetchall()
    bookings = conn.execute('''
        SELECT b.id, b.data_appuntamento, c.nome as corso_nome, c.giorno, c.orario, r.nome as sala 
        FROM bookings b JOIN courses c ON b.course_id = c.id LEFT JOIN rooms r ON c.room_id = r.id
        WHERE b.client_id = ? ORDER BY b.data_appuntamento DESC
    ''', (client_id,)).fetchall()
    conn.close()
    
    return render_template_string('''
    <!doctype html>
    <html lang="it">
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Area Personale</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    </head>
    <body class="bg-light">
    <nav class="navbar navbar-dark bg-success mb-4">
        <div class="container-fluid">
            <span class="navbar-brand"><i class="bi bi-person-circle"></i> {{ client.nome }}</span>
            <a href="/client/logout" class="btn btn-outline-light btn-sm">Esci</a>
        </div>
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}{% for cat, msg in messages %}<div class="alert alert-{{ 'danger' if cat=='error' else 'success' }}">{{ msg }}</div>{% endfor %}{% endif %}
        {% endwith %}

        <!-- Anagrafica -->
        <div class="card shadow-sm mb-4">
            <div class="card-header bg-white"><h5><i class="bi bi-person-badge"></i> I miei dati</h5></div>
            <div class="card-body">
                <form method="POST">
                    <input type="hidden" name="action" value="update_profile">
                    <div class="row g-3">
                        <div class="col-md-6"><label>Nome</label><input type="text" name="nome" class="form-control" value="{{ client.nome }}" required></div>
                        <div class="col-md-6"><label>Cognome</label><input type="text" name="cognome" class="form-control" value="{{ client.cognome }}" required></div>
                        <div class="col-md-6"><label>Email</label><input type="email" name="email" class="form-control" value="{{ client.email }}" required></div>
                        <div class="col-md-6"><label>Cellulare</label><input type="text" name="cellulare" class="form-control" value="{{ client.cellulare }}"></div>
                        <div class="col-12"><button type="submit" class="btn btn-success">Salva Modifiche</button></div>
                    </div>
                </form>
            </div>
        </div>

        <!-- Prenotazione Corso -->
        <div class="card shadow-sm mb-4">
            <div class="card-header bg-white"><h5><i class="bi bi-calendar-plus"></i> Richiedi Appuntamento / Corso</h5></div>
            <div class="card-body">
                <form method="POST">
                    <input type="hidden" name="action" value="book_course">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label>Corso</label>
                            <select name="course_id" class="form-select" required>
                                {% for c in courses %}
                                <option value="{{ c.id }}">{{ c.nome }} ({{ c.giorno }} - {{ c.orario }})</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-4"><label>Data</label><input type="date" name="data_appuntamento" class="form-control" required></div>
                        <div class="col-md-2 d-flex align-items-end"><button type="submit" class="btn btn-primary w-100">Prenota</button></div>
                    </div>
                </form>
            </div>
        </div>

        <!-- Storico e Appuntamenti -->
        <div class="card shadow-sm mb-4">
            <div class="card-header bg-white"><h5><i class="bi bi-clock-history"></i> I miei Appuntamenti e Storico</h5></div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead><tr><th>Data</th><th>Corso</th><th>Orario</th><th>Sala</th><th>Azione</th></tr></thead>
                        <tbody>
                            {% for b in bookings %}
                            <tr>
                                <td>{{ b.data_appuntamento }}</td>
                                <td><strong>{{ b.corso_nome }}</strong></td>
                                <td>{{ b.giorno }} ({{ b.orario }})</td>
                                <td>{{ b.sala or '-' }}</td>
                                <td>
                                    <form method="POST">
                                        <input type="hidden" name="action" value="cancel_booking">
                                        <input type="hidden" name="booking_id" value="{{ b.id }}">
                                        <button type="submit" class="btn btn-danger btn-sm" onclick="return confirm('Disdire?')">Disdici</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    </body></html>
    ''', client=client, courses=courses, bookings=bookings)

@app.route('/client/logout')
def client_logout():
    session.pop('client_id', None)
    return redirect(url_for('client_login'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
