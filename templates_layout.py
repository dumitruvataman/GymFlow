from flask import session, url_for
from database import get_db

def render_page(content_html, **kwargs):
    # Recupera le informazioni aziendali (incluso il logo_path) dal database
    conn = get_db()
    company = conn.execute('SELECT * FROM company_info LIMIT 1').fetchone()
    conn.close()
    
    logo_path = company['logo_path'] if company and company['logo_path'] else 'static/logo.png'
    gym_name = company['nome_palestra'] if company and company['nome_palestra'] else 'GymFlow'
    
    username = session.get('username', '')
    role = session.get('role', '')
    
    # Navbar condizionale in base allo stato di autenticazione
    navbar_html = ""
    if username:
        navbar_html = f"""
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
            <div class="container-fluid">
                <a class="navbar-brand d-flex align-items-center" href="{url_for('dashboard_bp.index')}">
                    <img src="/{logo_path}" alt="Logo" width="30" height="30" class="d-inline-block align-text-top me-2 rounded-circle" onerror="this.style.display='none'">
                    {gym_name}
                </a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item"><a class="nav-link" href="{url_for('dashboard_bp.index')}"><i class="bi bi-speedometer2"></i> Dashboard</a></li>
                        <li class="nav-item"><a class="nav-link" href="{url_for('courses_bp.manage_courses')}"><i class="bi bi-calendar-event"></i> Corsi</a></li>
                        <li class="nav-item"><a class="nav-link" href="{url_for('instructors_bp.manage_instructors')}"><i class="bi bi-people"></i> Istruttori</a></li>
                        <li class="nav-item"><a class="nav-link" href="{url_for('rooms_bp.manage_rooms')}"><i class="bi bi-door-open"></i> Sale</a></li>
                        <li class="nav-item"><a class="nav-link" href="{url_for('app_clients_bp.manage_clients')}"><i class="bi bi-person-badge"></i> Clienti</a></li>
                        <li class="nav-item"><a class="nav-link" href="{url_for('history_calendar_bp.history_calendar')}"><i class="bi bi-calendar3"></i> Calendario & Storico</a></li>
                        <li class="nav-item"><a class="nav-link" href="{url_for('company_bp.company_settings')}"><i class="bi bi-building"></i> Azienda</a></li>
                    </ul>
                    <ul class="navbar-nav">
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle text-light" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="bi bi-person-circle"></i> {username} <span class="badge bg-secondary">{role}</span>
                            </a>
                            <ul class="dropdown-menu dropdown-menu-end">
                                <li><a class="dropdown-item" href="{url_for('auth_bp.profile')}"><i class="bi bi-person-gear"></i> Profilo</a></li>
                                <li><a class="dropdown-item" href="{url_for('auth_bp.change_password')}"><i class="bi bi-key"></i> Cambia Password</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item text-danger" href="{url_for('auth_bp.logout')}"><i class="bi bi-box-arrow-right"></i> Esci</a></li>
                            </ul>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        """
    
    # Template HTML principale con Bootstrap 5 e Bootstrap Icons
    full_html = f"""<!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{gym_name} - Gestionale Palestra</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        {navbar_html}
        <div class="container pb-5">
            <!-- Messaggi Flash -->
            <div id="flash-messages">
                <!-- I messaggi flash gestiti da Flask possono essere inseriti qui se presenti nei kwargs o gestiti nel layout -->
            </div>
            {content_html}
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function togglePassword(inputId, iconId) {{
                const input = document.getElementById(inputId);
                const icon = document.getElementById(iconId);
                if (input.type === 'password') {{
                    input.type = 'text';
                    icon.classList.remove('bi-eye');
                    icon.classList.add('bi-eye-slash');
                }} else {{
                    input.type = 'password';
                    icon.classList.remove('bi-eye-slash');
                    icon.classList.add('bi-eye');
                }}
            }}
        </script>
    </body>
    </html>
    """
    return full_html
