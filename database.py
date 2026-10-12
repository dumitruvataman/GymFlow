import os
import sqlite3
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras

def get_db():
    if DATABASE_URL:
        db_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect('gymflow.db')
        conn.row_factory = sqlite3.Row
        return conn

def check_db_ready():
    """Verifica se il database è già configurato con le tabelle e l'admin."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute("SELECT TO_REGCLASS('public.sys_users');")
            res = cursor.fetchone()
            table_exists = res['to_regclass'] is not None if res else False
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sys_users';")
            table_exists = cursor.fetchone() is not None
            
        if not table_exists:
            conn.close()
            return False
            
        cursor.execute("SELECT COUNT(*) FROM sys_users WHERE username = 'admin'")
        res_admin = cursor.fetchone()
        admin_count = res_admin['count'] if DATABASE_URL else res_admin[0]
        conn.close()
        
        return admin_count > 0
    except Exception:
        return False

def log_activity(user_username, action_desc):
    try:
        conn = get_db()
        cursor = conn.cursor()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if DATABASE_URL:
            cursor.execute('INSERT INTO system_logs (timestamp, username, action) VALUES (%s, %s, %s)', (now_str, user_username, action_desc))
        else:
            cursor.execute('INSERT INTO system_logs (timestamp, username, action) VALUES (?, ?, ?)', (now_str, user_username, action_desc))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Errore di log:", e)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL, description TEXT);
            CREATE TABLE IF NOT EXISTS sys_users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role_id INTEGER REFERENCES roles(id), nome TEXT, cognome TEXT, email TEXT, cellulare TEXT);
            CREATE TABLE IF NOT EXISTS days (id SERIAL PRIMARY KEY, nome TEXT UNIQUE NOT NULL, ordine INTEGER);
            CREATE TABLE IF NOT EXISTS instructors (id SERIAL PRIMARY KEY, nome TEXT NOT NULL, cognome TEXT NOT NULL, email TEXT, cellulare TEXT, specialita TEXT);
            CREATE TABLE IF NOT EXISTS rooms (id SERIAL PRIMARY KEY, nome TEXT NOT NULL, capienza INTEGER);
            CREATE TABLE IF NOT EXISTS courses (id SERIAL PRIMARY KEY, nome TEXT NOT NULL, descrizione TEXT, instructor_id INTEGER REFERENCES instructors(id), room_id INTEGER REFERENCES rooms(id), orario_inizio TEXT, orario_fine TEXT);
            CREATE TABLE IF NOT EXISTS course_days (id SERIAL PRIMARY KEY, course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE, day_id INTEGER REFERENCES days(id));
            CREATE TABLE IF NOT EXISTS clients (id SERIAL PRIMARY KEY, pin_code TEXT NOT NULL, nome TEXT NOT NULL, cognome TEXT NOT NULL, email TEXT UNIQUE NOT NULL, cellulare TEXT);
            CREATE TABLE IF NOT EXISTS lesson_instances (id SERIAL PRIMARY KEY, course_id INTEGER REFERENCES courses(id), data_lezione TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS bookings (id SERIAL PRIMARY KEY, client_id INTEGER REFERENCES clients(id), course_id INTEGER REFERENCES courses(id), lesson_id INTEGER REFERENCES lesson_instances(id), data_appuntamento TEXT, stato TEXT DEFAULT 'Confermato', presenza TEXT DEFAULT 'In attesa');
            CREATE TABLE IF NOT EXISTS system_logs (id SERIAL PRIMARY KEY, timestamp TEXT, username TEXT, action TEXT);
        ''')
    else:
        cursor.execute('''CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, description TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS sys_users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role_id INTEGER, nome TEXT, cognome TEXT, email TEXT, cellulare TEXT, FOREIGN KEY(role_id) REFERENCES roles(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS days (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE NOT NULL, ordine INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS instructors (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, cognome TEXT NOT NULL, email TEXT, cellulare TEXT, specialita TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, capienza INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, descrizione TEXT, instructor_id INTEGER, room_id INTEGER, orario_inizio TEXT, orario_fine TEXT, FOREIGN KEY(instructor_id) REFERENCES instructors(id), FOREIGN KEY(room_id) REFERENCES rooms(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS course_days (id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER, day_id INTEGER, FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE, FOREIGN KEY(day_id) REFERENCES days(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, pin_code TEXT NOT NULL, nome TEXT NOT NULL, cognome TEXT NOT NULL, email TEXT UNIQUE NOT NULL, cellulare TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS lesson_instances (id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER, data_lezione TEXT NOT NULL, FOREIGN KEY(course_id) REFERENCES courses(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, course_id INTEGER, lesson_id INTEGER, data_appuntamento TEXT, stato TEXT DEFAULT 'Confermato', presenza TEXT DEFAULT 'In attesa', FOREIGN KEY(client_id) REFERENCES clients(id), FOREIGN KEY(course_id) REFERENCES courses(id), FOREIGN KEY(lesson_id) REFERENCES lesson_instances(id))''')

    cursor.execute("SELECT COUNT(*) FROM roles")
    res = cursor.fetchone()
    count_roles = res['count'] if DATABASE_URL else res[0]
    
    if count_roles == 0:
        roles_data = [('admin', 'Amministratore totale'), ('superuser', 'Gestione utenti pari o inferiori'), ('user', 'Accesso base')]
        if DATABASE_URL:
            cursor.executemany("INSERT INTO roles (name, description) VALUES (%s, %s) ON CONFLICT DO NOTHING", roles_data)
        else:
            cursor.executemany("INSERT INTO roles (name, description) VALUES (?, ?)", roles_data)
            
    cursor.execute("SELECT COUNT(*) FROM days")
    res_d = cursor.fetchone()
    count_days = res_d['count'] if DATABASE_URL else res_d[0]
    
    if count_days == 0:
        giorni_base = [('Lunedì', 1), ('Martedì', 2), ('Mercoledì', 3), ('Giovedì', 4), ('Venerdì', 5), ('Sabato', 6), ('Domenica', 7)]
        if DATABASE_URL:
            cursor.executemany("INSERT INTO days (nome, ordine) VALUES (%s, %s) ON CONFLICT DO NOTHING", giorni_base)
        else:
            cursor.executemany("INSERT INTO days (nome, ordine) VALUES (?, ?)", giorni_base)

    cursor.execute("SELECT * FROM sys_users WHERE username = 'admin'")
    if not cursor.fetchone():
        from werkzeug.security import generate_password_hash
        hashed_pw = generate_password_hash('admin123')
        if DATABASE_URL:
            cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
            role_admin = cursor.fetchone()['id']
            cursor.execute("INSERT INTO sys_users (username, password, role_id, nome, cognome, email, cellulare) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           ('admin', hashed_pw, role_admin, 'Amministratore', 'Generale', 'admin@gymflow.it', '3330000000'))
        else:
            cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
            role_admin = cursor.fetchone()[0]
            cursor.execute("INSERT INTO sys_users (username, password, role_id, nome, cognome, email, cellulare) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           ('admin', hashed_pw, role_admin, 'Amministratore', 'Generale', 'admin@gymflow.it', '3330000000'))
                       
    conn.commit()
    conn.close()
