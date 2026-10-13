import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    if DATABASE_URL:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect('gymflow.db')
        conn.row_factory = sqlite3.Row
        return conn

def check_db_ready():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM sys_users LIMIT 1")
        conn.close()
        return True
    except Exception:
        return False

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('''CREATE TABLE IF NOT EXISTS roles (
                            id SERIAL PRIMARY KEY,
                            name TEXT UNIQUE
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS sys_users (
                            id SERIAL PRIMARY KEY,
                            username TEXT UNIQUE,
                            password TEXT,
                            role_id INTEGER,
                            nome TEXT,
                            cognome TEXT,
                            email TEXT,
                            cellulare TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS company_info (
                            id SERIAL PRIMARY KEY,
                            nome_palestra TEXT,
                            logo_path TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS courses (
                            id SERIAL PRIMARY KEY,
                            nome TEXT,
                            descrizione TEXT,
                            instructor_id INTEGER,
                            room_id INTEGER
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS course_days (
                            course_id INTEGER,
                            day_id INTEGER,
                            orario_inizio TEXT,
                            orario_fine TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS days (
                            id SERIAL PRIMARY KEY,
                            nome TEXT,
                            ordine INTEGER
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS instructors (
                            id SERIAL PRIMARY KEY,
                            nome TEXT,
                            cognome TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS rooms (
                            id SERIAL PRIMARY KEY,
                            nome TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS clients (
                            id SERIAL PRIMARY KEY,
                            nome TEXT,
                            cognome TEXT,
                            email TEXT,
                            telefono TEXT,
                            data_iscrizione TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS lesson_instances (
                            id SERIAL PRIMARY KEY,
                            course_id INTEGER,
                            data_lezione TEXT,
                            stato TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (
                            id SERIAL PRIMARY KEY,
                            lesson_id INTEGER,
                            client_id INTEGER,
                            status TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
                            id SERIAL PRIMARY KEY,
                            username TEXT,
                            action TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                          )''')
        
        # Inserimento dati di default per Postgres (Render)
        cursor.execute('SELECT COUNT(*) as cnt FROM roles')
        if cursor.fetchone()['cnt'] == 0:
            cursor.executemany('INSERT INTO roles (name) VALUES (%s)', [('admin',), ('superuser',), ('staff',)])

        cursor.execute('SELECT COUNT(*) as cnt FROM sys_users WHERE username = %s', ('admin',))
        if cursor.fetchone()['cnt'] == 0:
            hashed_pw = generate_password_hash('admin')
            cursor.execute('INSERT INTO sys_users (username, password, role_id, nome, cognome) VALUES (%s, %s, %s, %s, %s)', 
                           ('admin', hashed_pw, 1, 'Amministratore', 'Sistema'))

        cursor.execute('SELECT COUNT(*) as cnt FROM days')
        if cursor.fetchone()['cnt'] == 0:
            default_days = [
                ('Lunedì', 1), ('Martedì', 2), ('Mercoledì', 3), 
                ('Giovedì', 4), ('Venerdì', 5), ('Sabato', 6), ('Domenica', 7)
            ]
            cursor.executemany('INSERT INTO days (nome, ordine) VALUES (%s, %s)', default_days)
            
        cursor.execute('SELECT COUNT(*) as cnt FROM company_info')
        if cursor.fetchone()['cnt'] == 0:
            cursor.execute('INSERT INTO company_info (nome_palestra, logo_path) VALUES (%s, %s)', ('GymFlow Palestra', 'static/logo.png'))

    else:
        cursor.execute('''CREATE TABLE IF NOT EXISTS roles (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT UNIQUE
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS sys_users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE,
                            password TEXT,
                            role_id INTEGER,
                            nome TEXT,
                            cognome TEXT,
                            email TEXT,
                            cellulare TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS company_info (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nome_palestra TEXT,
                            logo_path TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS courses (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nome TEXT,
                            descrizione TEXT,
                            instructor_id INTEGER,
                            room_id INTEGER
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS course_days (
                            course_id INTEGER,
                            day_id INTEGER,
                            orario_inizio TEXT,
                            orario_fine TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS days (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nome TEXT,
                            ordine INTEGER
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS instructors (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nome TEXT,
                            cognome TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS rooms (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nome TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS clients (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nome TEXT,
                            cognome TEXT,
                            email TEXT,
                            telefono TEXT,
                            data_iscrizione TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS lesson_instances (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            course_id INTEGER,
                            data_lezione TEXT,
                            stato TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            lesson_id INTEGER,
                            client_id INTEGER,
                            status TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT,
                            action TEXT,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                          )''')
        
        # Inserisci ruoli di default se vuoti
        cursor.execute('SELECT COUNT(*) as cnt FROM roles')
        if cursor.fetchone()['cnt'] == 0:
            cursor.executemany('INSERT INTO roles (name) VALUES (?)', [('admin',), ('superuser',), ('staff',)])

        # Inserisci utente admin di default se non esiste
        cursor.execute('SELECT COUNT(*) as cnt FROM sys_users WHERE username = ?', ('admin',))
        if cursor.fetchone()['cnt'] == 0:
            hashed_pw = generate_password_hash('admin')
            cursor.execute('INSERT INTO sys_users (username, password, role_id, nome, cognome) VALUES (?, ?, ?, ?, ?)', 
                           ('admin', hashed_pw, 1, 'Amministratore', 'Sistema'))

        # Inserisci giorni di default se vuoti
        cursor.execute('SELECT COUNT(*) as cnt FROM days')
        if cursor.fetchone()['cnt'] == 0:
            default_days = [
                ('Lunedì', 1), ('Martedì', 2), ('Mercoledì', 3), 
                ('Giovedì', 4), ('Venerdì', 5), ('Sabato', 6), ('Domenica', 7)
            ]
            cursor.executemany('INSERT INTO days (nome, ordine) VALUES (?, ?)', default_days)
            
        # Inserisci azienda di default se vuota
        cursor.execute('SELECT COUNT(*) as cnt FROM company_info')
        if cursor.fetchone()['cnt'] == 0:
            cursor.execute('INSERT INTO company_info (nome_palestra, logo_path) VALUES (?, ?)', ('GymFlow Palestra', 'static/logo.png'))

    conn.commit()
    conn.close()

def log_activity(username, action):
    try:
        conn = get_db()
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute('INSERT INTO activity_logs (username, action) VALUES (%s, %s)', (username, action))
        else:
            cursor.execute('INSERT INTO activity_logs (username, action) VALUES (?, ?)', (username, action))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Errore di log: {e}")
