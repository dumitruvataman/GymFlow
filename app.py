from flask import Flask, redirect, url_for, session
from database import init_db, check_db_ready
from routes_auth import auth_bp
from routes_dashboard import dashboard_bp
from routes_courses import courses_bp
from routes_company import company_bp
from routes_instructors import instructors_bp
from routes_rooms import rooms_bp
from routes_history_calendar import history_calendar_bp
from routes_admin import admin_bp
from routes_app_clients import app_clients_bp
from routes_client import client_bp

app = Flask(__name__)
app.secret_key = 'gymflow_secret_key_change_in_production'

# Inizializza il database e crea automaticamente tutte le tabelle all'avvio
with app.app_context():
    init_db()

# Registrazione di tutti i Blueprint dell'applicazione
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(courses_bp)
app.register_blueprint(company_bp)
app.register_blueprint(instructors_bp)
app.register_blueprint(rooms_bp)
app.register_blueprint(history_calendar_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(app_clients_bp)
app.register_blueprint(client_bp)

@app.route('/health')
def health_check():
    if check_db_ready():
        return "OK", 200
    return "Database not ready", 500

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
    return redirect(url_for('dashboard_bp.index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
