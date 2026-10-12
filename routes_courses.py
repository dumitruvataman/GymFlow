from flask import Blueprint, request, redirect, url_for, session, flash
from database import get_db, log_activity, DATABASE_URL
from templates_layout import render_page

company_bp = Blueprint('company_bp', __name__)

@company_bp.route('/company-settings', methods=['GET', 'POST'])
def company_settings():
    if 'user_id' not in session or session.get('role') not in ['admin', 'superuser']:
        flash('Accesso negato.', 'error')
        return redirect(url_for('dashboard_bp.index'))
        
    conn = get_db()
    if request.method == 'POST':
        nome_palestra = request.form['nome_palestra']
        logo_path = request.form['logo_path']
        
        if DATABASE_URL:
            conn.cursor().execute('UPDATE company_info SET nome_palestra = %s, logo_path = %s WHERE id = 1', (nome_palestra, logo_path))
        else:
            conn.cursor().execute('UPDATE company_info SET nome_palestra = ?, logo_path = ? WHERE id = 1', (nome_palestra, logo_path))
        conn.commit()
        log_activity(session['username'], f"Aggiornata anagrafica aziendale: {nome_palestra}")
        flash('Anagrafica azienda aggiornata con successo.', 'success')
        return redirect(url_for('company_bp.company_settings'))
        
    company = conn.execute('SELECT * FROM company_info LIMIT 1').fetchone()
    conn.close()
    
    # Usiamo una stringa normale (senza f-prefix) per evitare conflitti con le parentesi graffe
    content = """
    <h2><i class="bi bi-building"></i> Anagrafica Azienda e Logo</h2>
    <p class="text-muted">Configura il nome della palestra e il file immagine del logo presente nel repository (es. cartella <code>static/</code>).</p>
    
    <div class="card shadow-sm p-4 mt-3" style="max-width: 600px;">
        <form method="POST">
            <div class="mb-3">
                <label class="form-label">Nome della Palestra</label>
                <input type="text" name="nome_palestra" class="form-control" value=""" + f"\"{company['nome_palestra'] if company else ''}\"" + """ required>
            </div>
            <div class="mb-3">
                <label class="form-label">Percorso File Logo nel Repository (es. <code>static/logo.png</code>)</label>
                <input type="text" name="logo_path" class="form-control" value=""" + f"\"{company['logo_path'] if company else 'static/logo.png'}\"" + """ required>
            </div>
            <div class="text-center mb-3">
                <p class="small text-muted">Anteprima Logo attuale:</p>
                <img src="/""" + f"{company['logo_path'] if company else 'static/logo.png'}" + """" alt="Logo" width="80" height="80" class="rounded-circle border p-1 bg-white" onerror="this.style.display='none'">
            </div>
            <button type="submit" class="btn btn-primary w-100">Salva Impostazioni Azienda</button>
        </form>
    </div>
    """
    return render_page(content)
