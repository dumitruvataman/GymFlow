def render_page(content, **context):
    from flask import render_template_string
    from database import get_db
    
    try:
        conn = get_db()
        company = conn.execute("SELECT * FROM company_info LIMIT 1").fetchone()
        conn.close()
        nome_palestra = company['nome_palestra'] if company else "GymFlow Admin"
        logo_path = company['logo_path'] if company and company['logo_path'] else "static/logo.png"
    except Exception:
        nome_palestra = "GymFlow Admin"
        logo_path = "static/logo.png"

    if not logo_path or "logo_path" in logo_path:
        logo_path = "static/logo.png"
    if logo_path.startswith('/'):
        logo_path = logo_path.lstrip('/')

    full_template = f'''
    <!doctype html>
    <html lang="it">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{nome_palestra}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    </head>
    <body class="bg-light">
        {{% if session.get('user_id') %}}
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
            <div class="container-fluid">
                <a class="navbar-brand d-flex align-items-center" href="/">
                    <img src="/{logo_path}" alt="Logo" width="35" height="35" class="d-inline-block align-text-top me-2 rounded-circle bg-white p-1" onerror="this.style.display='none'">
                    <span>{nome_palestra}</span>
                </a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item"><a class="nav-link" href="/">Calendario & Prenotazioni</a></li>
                        <li class="nav-item"><a class="nav-link" href="/history-calendar">Calendario Storico</a></li>
                        <li class="nav-item"><a class="nav-link" href="/courses">Corsi</a></li>
                        <li class="nav-item"><a class="nav-link" href="/instructors">Istruttori</a></li>
                        <li class="nav-item"><a class="nav-link" href="/rooms">Sale</a></li>
                        <li class="nav-item"><a class="nav-link" href="/clients">Clienti (App)</a></li>
                        {{% if session.get('role') in ['admin', 'superuser'] %}}
                        <li class="nav-item"><a class="nav-link" href="/company-settings">Anagrafica Azienda</a></li>
                        <li class="nav-item"><a class="nav-link" href="/users">Utenti Sistema</a></li>
                        <li class="nav-item"><a class="nav-link" href="/logs">Registro Log</a></li>
                        {{% endif %}}
                    </ul>
                    
                    <div class="dropdown me-3">
                        <button class="btn btn-outline-light dropdown-toggle btn-sm" type="button" data-bs-toggle="dropdown">
                            <i class="bi bi-person-circle"></i> {{{{ session.get('username') }}}} ({{{{ session.get('role') }}}})
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><a class="dropdown-item" href="/profile"><i class="bi bi-person-gear"></i> Modifica Anagrafica</a></li>
                            <li><a class="dropdown-item" href="/change-password"><i class="bi bi-key"></i> Cambio Password</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item text-danger" href="/logout"><i class="bi bi-box-arrow-right"></i> Esci</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </nav>
        {{% endif %}}

        <div class="container">
            {{% with messages = get_flashed_messages(with_categories=true) %}}
                {{% if messages %}}
                    {{% for category, message in messages %}}
                        <div class="alert alert-{{{{ 'danger' if category == 'error' else 'success' }}}} alert-dismissible fade show" role="alert">
                            {{{{ message }}}}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {{% endfor %}}
                {{% endif %}}
            {{% endwith %}}

            {content}
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function togglePassword(fieldId, btnId) {{
                const input = document.getElementById(fieldId);
                const icon = document.getElementById(btnId);
                if (input.type === "password") {{
                    input.type = "text";
                    icon.classList.remove("bi-eye");
                    icon.classList.add("bi-eye-slash");
                }} else {{
                    input.type = "password";
                    icon.classList.remove("bi-eye-slash");
                    icon.classList.add("bi-eye");
                }}
            }}

            {{% if session.get('user_id') %}}
            let inactivityTimeout;
            function resetInactivityTimer() {{
                clearTimeout(inactivityTimeout);
                inactivityTimeout = setTimeout(() => {{
                    window.location.href = '/logout?timeout=1';
                }}, 300000); // 5 minuti
            }}
            window.onload = resetInactivityTimer;
            window.onmousemove = resetInactivityTimer;
            window.onkeypress = resetInactivityTimer;
            window.onclick = resetInactivityTimer;
            window.onscroll = resetInactivityTimer;
            {{% endif %}}
        </script>
    </body>
    </html>
    '''
    return render_template_string(full_template, **context)
