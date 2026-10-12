from flask import Flask, redirect, url_for, session
from database import check_db_ready
from routes_auth import auth_bp
from routes_dashboard import dashboard_bp
from routes_instructors import instructors_bp
from routes_rooms import rooms_bp
from routes_courses import courses_bp
from routes_app_clients import app_clients_bp
from routes_client import client_bp
from routes_history_calendar import history_calendar_bp
from routes_company import company_bp

app = Flask(__name__)
app.secret_key = 'chiave_segreta_gymflow_super_sicura_v4'

# Registra tutti i Blueprint dei moduli
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(instructors_bp)
app.register_blueprint(rooms_bp)
app.register_blueprint(courses_bp)
app.register_blueprint(app_clients_bp)
app.register_blueprint(client_bp)
app.register_blueprint(history_calendar_bp)
app.register_blueprint(company_bp)

@app.route('/')
def root_redirect():
    if not check_db_ready():
        return redirect(url_for('auth_bp.setup_wizard'))
        
    if 'user_id' in session:
        return redirect(url_for('dashboard_bp.index'))
    return redirect(url_for('auth_bp.login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
