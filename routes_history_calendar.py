from flask import Blueprint, session, redirect, url_for, request, flash
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page
from datetime import datetime

history_calendar_bp = Blueprint('history_calendar_bp', __name__)

@history_calendar_bp.route('/history-calendar', methods=['GET', 'POST'])
def history_calendar():
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Gestione generazione istanze lezioni o azioni calendario
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'generate_lessons':
            # Logica di generazione istanze dalle programmazioni dei corsi
            flash('Funzionalità di generazione lezioni', 'success')
            return redirect(url_for('history_calendar_bp.history_calendar'))

    # Parametri mese/anno correnti o filtrati
    now = datetime.now()
    year = int(request.args.get('year', now.year))
    month = int(request.args.get('month', now.month))
    
    # Recupera le istanze di lezione unendo i corsi, le sale, gli istruttori e gli orari specifici dai giorni
    lessons = conn.execute('''
        SELECT l.*, c.nome as corso_nome, r.nome as sala_nome,
               cd.orario_inizio, cd.orario_fine
        FROM lesson_instances l
        LEFT JOIN courses c ON l.course_id = c.id
        LEFT JOIN rooms r ON c.room_id = r.id
        LEFT JOIN course_days cd ON c.id = cd.course_id
        WHERE SUBSTR(l.data_lezione, 1, 7) = ?
    ''' if not DATABASE_URL else '''
        SELECT l.*, c.nome as corso_nome, r.nome as sala_nome,
               cd.orario_inizio, cd.orario_fine
        FROM lesson_instances l
        LEFT JOIN courses c ON l.course_id = c.id
        LEFT JOIN rooms r ON c.room_id = r.id
        LEFT JOIN course_days cd ON c.id = cd.course_id
        WHERE SUBSTR(l.data_lezione, 1, 7) = %s
    ''', (f"{year:04d}-{month:02d}",)).fetchall()
    
    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    
    courses_options = "".join([f'<option value="{c["id"]}">{c["nome"]}</option>' for c in courses])
    
    lessons_rows = ""
    for l in lessons:
        ld = dict(l)
        lessons_rows += f"""
        <tr>
            <td><code>{ld.get('data_lezione', '')}</code></td>
            <td><strong>{ld.get('corso_nome', 'N/D')}</strong></td>
            <td>{ld.get('orario_inizio', '')} - {ld.get('orario_fine', '')}</td>
            <td>{ld.get('sala_nome', 'N/D')}</td>
            <td><span class="badge bg-info text-dark">{ld.get('stato', 'Programmata')}</span></td>
        </tr>
        """
    if not lessons:
        lessons_rows = '<tr><td colspan="5" class="text-center text-muted">Nessuna lezione registrata per questo mese.</td></tr>'

    content = f"""
    <div class="row mb-4">
        <div class="col-12">
            <h2>Calendario Storico e Lezioni</h2>
            <p class="text-muted">Visualizza lo storico delle lezioni programmate ed effettuate per il mese {month:02d}/{year}.</p>
        </div>
    </div>
    
    <div class="card shadow-sm p-4 mb-4">
        <h4 class="mb-3">Filtra per Mese</h4>
        <form method="GET" class="row g-3">
            <div class="col-md-4">
                <label class="form-label">Anno</label>
                <input type="number" name="year" value="{year}" class="form-control" required>
            </div>
            <div class="col-md-4">
                <label class="form-label">Mese (1-12)</label>
                <input type="number" name="month" value="{month}" min="1" max="12" class="form-control" required>
            </div>
            <div class="col-md-4 d-flex align-items-end">
                <button type="submit" class="btn btn-primary w-100"><i class="bi bi-search"></i> Filtra Storico</button>
            </div>
        </form>
    </div>

    <div class="card shadow-sm p-4">
        <h4 class="mb-3">Elenco Lezioni del Mese</h4>
        <div class="table-responsive">
            <table class="table table-striped align-middle">
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Corso</th>
                        <th>Orario</th>
                        <th>Sala</th>
                        <th>Stato</th>
                    </tr>
                </thead>
                <tbody>
                    {lessons_rows}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_page(content)
