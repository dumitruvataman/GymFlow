from flask import Blueprint, request, redirect, url_for, session, flash, render_template_string
from database import get_db, DATABASE_URL

client_bp = Blueprint('client_bp', __name__)

@client_bp.route('/client/login', methods=['GET', 'POST'])
def client_login():
    if request.method == 'POST':
        conn = get_db()
        client = conn.execute('''
            SELECT * FROM clients WHERE email = ? AND pin_code = ?
        ''' if not DATABASE_URL else '''
            SELECT * FROM clients WHERE email = %s AND pin_code = %s
        ''', (request.form['email'], request.form['pin_code'])).fetchone()
        conn.close()
        if client:
            session['client_id'] = client['id']
            session['client_name'] = f"{client['nome']} {client['cognome']}"
            return redirect(url_for('client_bp.client_dashboard'))
        flash('Email o PIN errati.', 'error')
        
    return render_template_string('''
    <!doctype html>
    <html lang="it">
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>GymFlow - Area Clienti</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light d-flex align-items-center py-4" style="min-height: 100vh;">
        <div class="container text-center" style="max-width: 400px;">
            <div class="card shadow p-4">
                <h3 class="mb-3 text-success">GymFlow Clienti</h3>
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

@client_bp.route('/client/dashboard', methods=['GET', 'POST'])
def client_dashboard():
    if 'client_id' not in session: return redirect(url_for('client_bp.client_login'))
    client_id = session['client_id']
    conn = get_db()
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile':
            if DATABASE_URL:
                conn.cursor().execute('UPDATE clients SET nome=%s, cognome=%s, email=%s, cellulare=%s WHERE id=%s', 
                                      (request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare'], client_id))
            else:
                conn.cursor().execute('UPDATE clients SET nome=?, cognome=?, email=?, cellulare=? WHERE id=?', 
                                      (request.form['nome'], request.form['cognome'], request.form['email'], request.form['cellulare'], client_id))
            conn.commit()
            flash('Dati anagrafici aggiornati!', 'success')
        elif action == 'book_course':
            if DATABASE_URL:
                conn.cursor().execute('INSERT INTO bookings (client_id, course_id, data_appuntamento, stato) VALUES (%s, %s, %s, %s)',
                                      (client_id, request.form['course_id'], request.form['data_appuntamento'], 'Confermato'))
            else:
                conn.cursor().execute('INSERT INTO bookings (client_id, course_id, data_appuntamento, stato) VALUES (?, ?, ?, ?)',
                                      (client_id, request.form['course_id'], request.form['data_appuntamento'], 'Confermato'))
            conn.commit()
            flash('Appuntamento prenotato con successo!', 'success')
        elif action == 'cancel_booking':
            if DATABASE_URL:
                conn.cursor().execute('DELETE FROM bookings WHERE id = %s AND client_id = %s', (request.form['booking_id'], client_id))
            else:
                conn.cursor().execute('DELETE FROM bookings WHERE id = ? AND client_id = ?', (request.form['booking_id'], client_id))
            conn.commit()
            flash('Prenotazione cancellata.', 'success')
            
    client = conn.execute('SELECT * FROM clients WHERE id = ?' if not DATABASE_URL else 'SELECT * FROM clients WHERE id = %s', (client_id,)).fetchone()
    courses = conn.execute('''
        SELECT c.*, r.nome as r_nome, d.nome as giorno_nome 
        FROM courses c 
        LEFT JOIN rooms r ON c.room_id=r.id 
        LEFT JOIN days d ON c.day_id = d.id
    ''').fetchall()
    bookings = conn.execute('''
        SELECT b.id, b.data_appuntamento, c.nome as corso_nome, d.nome as giorno_nome, c.orario, r.nome as sala 
        FROM bookings b 
        JOIN courses c ON b.course_id = c.id 
        LEFT JOIN rooms r ON c.room_id = r.id
        LEFT JOIN days d ON c.day_id = d.id
        WHERE b.client_id = ? ORDER BY b.data_appuntamento DESC
    ''' if not DATABASE_URL else '''
        SELECT b.id, b.data_appuntamento, c.nome as corso_nome, d.nome as giorno_nome, c.orario, r.nome as sala 
        FROM bookings b 
        JOIN courses c ON b.course_id = c.id 
        LEFT JOIN rooms r ON c.room_id = r.id
        LEFT JOIN days d ON c.day_id = d.id
        WHERE b.client_id = %s ORDER BY b.data_appuntamento DESC
    ''', (client_id,)).fetchall()
    conn.close()
    
    return render_template_string('''
    <!doctype html>
    <html lang="it">
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>GymFlow - Area Personale</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    </head>
    <body class="bg-light">
    <nav class="navbar navbar-dark bg-success mb-4">
        <div class="container-fluid">
            <span class="navbar-brand"><i class="bi bi-person-circle"></i> {{ client.nome }} (GymFlow)</span>
            <a href="/client/logout" class="btn btn-outline-light btn-sm">Esci</a>
        </div>
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}{% for cat, msg in messages %}<div class="alert alert-{{ 'danger' if cat=='error' else 'success' }}">{{ msg }}</div>{% endfor %}{% endif %}
        {% endwith %}

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
                                <option value="{{ c.id }}">{{ c.nome }} ({{ c.giorno_nome }} - {{ c.orario }})</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-4"><label>Data</label><input type="date" name="data_appuntamento" class="form-control" required></div>
                        <div class="col-md-2 d-flex align-items-end"><button type="submit" class="btn btn-primary w-100">Prenota</button></div>
                    </div>
                </form>
            </div>
        </div>

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
                                <td>{{ b.giorno_nome }} ({{ b.orario }})</td>
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

@client_bp.route('/client/logout')
def client_logout():
    session.pop('client_id', None)
    return redirect(url_for('client_bp.client_login'))