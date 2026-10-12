import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

# Se siamo su Render/Cloud, useremo PostgreSQL, altrimenti SQLite in locale
DATABASE_URL = os.environ.get('DATABASE_URL')

app = Flask(__name__)
app.secret_key = 'chiave_segreta_palestra_super_sicura_render_v3'

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras

def get_db():
    if DATABASE_URL:
        # Connessione a PostgreSQL (Cloud)
        # Nota: su alcuni provider l'URL inizia con postgres:// e va corretto in postgresql://
        db_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor)
        return conn
    else:
        # Connessione a SQLite (Locale sul PC)
        conn = sqlite3.connect('palestra.db')
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Sintassi adattabile o standard per la creazione delle tabelle
    # 1. Ruoli Sistema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            description TEXT
        ) if not exists;
    ''') if DATABASE_URL else cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    ''')
    
    # Per semplicità di compatibilità multi-database pulita in un unico file,
    # usiamo query standard supportate da entrambi o gestiamo i tipi auto-incremento.
    # Di seguito la struttura unificata:
    
    if DATABASE_URL:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL, description TEXT);
            CREATE TABLE IF NOT EXISTS sys_users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role_id INTEGER REFERENCES roles(id), nome TEXT, cognome TEXT, email TEXT, cellulare TEXT);
            CREATE TABLE IF NOT EXISTS days (id SERIAL PRIMARY KEY, nome TEXT UNIQUE NOT NULL, ordine INTEGER);
            CREATE TABLE IF NOT EXISTS instructors (id SERIAL PRIMARY KEY, nome TEXT NOT NULL, cognome TEXT NOT NULL, email TEXT, cellulare TEXT, specialita TEXT);
            CREATE TABLE IF NOT EXISTS rooms (id SERIAL PRIMARY KEY, nome TEXT NOT NULL, capienza INTEGER);
            CREATE TABLE IF NOT EXISTS courses (id SERIAL PRIMARY KEY, nome TEXT NOT NULL, descrizione TEXT, instructor_id INTEGER REFERENCES instructors(id), room_id INTEGER REFERENCES rooms(id), day_id INTEGER REFERENCES days(id), orario TEXT);
            CREATE TABLE IF NOT EXISTS clients (id SERIAL PRIMARY KEY, pin_code TEXT NOT NULL, nome TEXT NOT NULL, cognome TEXT NOT NULL, email TEXT UNIQUE NOT NULL, cellulare TEXT);
            CREATE TABLE IF NOT EXISTS bookings (id SERIAL PRIMARY KEY, client_id INTEGER REFERENCES clients(id), course_id INTEGER REFERENCES courses(id), data_appuntamento TEXT, stato TEXT DEFAULT 'Confermato');
        ''')
    else:
        cursor.execute('''CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, description TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS sys_users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role_id INTEGER, nome TEXT, cognome TEXT, email TEXT, cellulare TEXT, FOREIGN KEY(role_id) REFERENCES roles(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS days (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE NOT NULL, ordine INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS instructors (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, cognome TEXT NOT NULL, email TEXT, cellulare TEXT, specialita TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, capienza INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, descrizione TEXT, instructor_id INTEGER, room_id INTEGER, day_id INTEGER, orario TEXT, FOREIGN KEY(instructor_id) REFERENCES instructors(id), FOREIGN KEY(room_id) REFERENCES rooms(id), FOREIGN KEY(day_id) REFERENCES days(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, pin_code TEXT NOT NULL, nome TEXT NOT NULL, cognome TEXT NOT NULL, email TEXT UNIQUE NOT NULL, cellulare TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, course_id INTEGER, data_appuntamento TEXT, stato TEXT DEFAULT 'Confermato', FOREIGN KEY(client_id) REFERENCES clients(id), FOREIGN KEY(course_id) REFERENCES courses(id))''')

    # Inserimento dati essenziali di default se vuoti
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

    # Admin di default
    if DATABASE_URL:
        cursor.execute("SELECT * FROM sys_users WHERE username = 'admin'")
    else:
        cursor.execute("SELECT * FROM sys_users WHERE username = 'admin'")
        
    if not cursor.fetchone():
        hashed_pw = generate_password_hash('admin123')
        if DATABASE_URL:
            cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
            role_admin = cursor.fetchone()['id']
            cursor.execute("INSERT INTO sys_users (username, password, role_id, nome, cognome, email, cellulare) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           ('admin', hashed_pw, role_admin, 'Amministratore', 'Generale', 'admin@palestra.it', '3330000000'))
        else:
            cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
            role_admin = cursor.fetchone()[0]
            cursor.execute("INSERT INTO sys_users (username, password, role_id, nome, cognome, email, cellulare) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           ('admin', hashed_pw, role_admin, 'Amministratore', 'Generale', 'admin@palestra.it', '3330000000'))
                       
    conn.commit()
    conn.close()

init_db()

# --- NOTA IMPORTANTE SUI REQUISITI ---
# Se pubblichi su Render con PostgreSQL, ricordati di aggiungere 'psycopg2-binary' 
# nel file requirements.txt insieme a 'flask' e 'gunicorn'.
