from flask import Blueprint, session, redirect, url_for
from database import get_db
from templates_layout import render_page

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
        
    conn = get_db()
    
    courses = conn.execute('''
        SELECT c.*, i.nome as i_nome, i.cognome as i_cognome, r.nome as r_nome,
               GROUP_CONCAT(d.nome, ', ') as giorni_str
        FROM courses c 
        LEFT JOIN instructors i ON c.instructor_id = i.id 
        LEFT JOIN rooms r ON c.room_id = r.id
        LEFT JOIN course_days cd ON c.id = cd.course_id
        LEFT JOIN days d ON cd.day_id = d.id
        GROUP BY c.id
    ''').fetchall()
    
    conn.close()
    
    username = session.get('username', 'Utente')
    
    content = f"""
    <div class="row mb-4">
        <div class="col-12">
            <h2>Benvenuto, {username}!</h2>
            <p class="text-muted">Panoramica generale della gestione corsi e programmazione settimanale.</p>
        </div>
    </div>
    
    <div class="row">
        <div class="col-12">
            <div class="card shadow-sm p-4">
                <h4 class="mb-3">Corsi Programmabili e Orari</h4>
                <div class="table-responsive">
                    <table class="table table-striped align-middle">
                        <thead>
                            <tr>
                                <th>Corso</th>
                                <th>Orario</th>
                                <th>Giorni</th>
                                <th>Sala</th>
                                <th>Istruttore</th>
                            </tr>
                        </thead>
                        <tbody>
                            """ + "{% for c in courses %}" + """
                            <tr>
                                <td><strong>{{ c.nome }}</strong><br><small class="text-muted">{{ c.descrizione }}</small></td>
                                <td>{{ c.orario_inizio }} - {{ c.orario_fine }}</td>
                                <td><span class="badge bg-info text-dark">{{ c.giorni_str or 'Nessun giorno' }}</span></td>
                                <td>{{ c.r_nome or 'N/D' }}</td>
                                <td>{{ c.i_nome or '' }} {{ c.i_cognome or '' }}</td>
                            </tr>
                            """ + "{% else %}" + """
                            <tr>
                                <td colspan="5" class="text-center text-muted">Nessun corso programmato al momento.</td>
                            </tr>
                            """ + "{% endfor %}" + """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    """
    return render_page(content, courses=courses)
