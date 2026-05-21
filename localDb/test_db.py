import sqlite3
from localDb.clases import Usuario,Cita

def inicializar_db():
    conn = sqlite3.connect("sistema_citas.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        nombre TEXT,
        apellidos TEXT,
        rut TEXT,
        sexo TEXT,
        rol TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS citas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anio INTEGER,
        mes INTEGER,
        dia INTEGER,
        hora INTEGER,
        minutos INTEGER,
        usuario_id INTEGER,
        docente TEXT,
        asunto TEXT,
        estado INTEGER,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    )''')

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        usuarios_prueba = [
            ('admin', '1234', 'Admin', 'Sistema', '00000000-0', 'N/A', 'ADMIN'),
            ('dlopez', 'doc123', 'Dra. María', 'López', '11111111-1', 'Mujer', 'DOCENTE'),
            ('pperez', 'doc456', 'Dr. Pedro', 'Pérez', '22222222-2', 'Hombre', 'DOCENTE'),
            ('dyimi', 'doc789', 'Dr. Yimi', 'Desconocido', '33333333-3', 'Hombre', 'DOCENTE'),
            ('user1', 'pass1', 'Juan', 'Doe', '44444444-4', 'Hombre', 'PACIENTE'),
            ('user2', 'pass2', 'Maria', 'Garcia', '55555555-5', 'Mujer', 'PACIENTE')
        ]
        cursor.executemany('''INSERT INTO usuarios 
                              (username, password, nombre, apellidos, rut, sexo, rol) 
                              VALUES (?,?,?,?,?,?,?)''', usuarios_prueba)
    
    cursor.execute("SELECT COUNT(*) FROM citas")
    if cursor.fetchone()[0] == 0:
        citas_prueba = [
            # (anio, mes, dia, hora, minutos, usuario_id, docente, asunto, estado)
            (2026, 4, 15, 10, 30, 5, 'Dra. María López', 'Chequeo general', 1),
            (2026, 4, 15, 11, 0, 6, 'Dr. Pedro Pérez', 'Dolor de cabeza', 1),
            (2026, 4, 16, 9, 15, 5, 'Dr. Yimi', 'Control médico', 1),
            (2026, 4, 17, 14, 45, 6, 'Dra. María López', 'Examen anual', 1),
            (2026, 4, 18, 16, 0, 5, 'Dr. Pedro Pérez', 'Consulta seguimiento', 2),  # ausente
            (2026, 4, 19, 8, 30, 6, 'Dr. Yimi', 'Vacunación', 3),  # concluida
            (2026, 4, 20, 12, 0, 5, 'Dra. María López', 'Revisión resultados', 0)  # cancelada
        ]

        cursor.executemany('''INSERT INTO citas 
            (anio, mes, dia, hora, minutos, usuario_id, docente, asunto, estado)
            VALUES (?,?,?,?,?,?,?,?,?)''', citas_prueba)

        conn.commit()

    conn.close()

def validar_credenciales(u, p):
    conn = sqlite3.connect("sistema_citas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, apellidos, rut, sexo, rol FROM usuarios WHERE username=? AND password=?", (u, p))
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado:
        # Mapeo Objeto-Relacional: Se retorna una instancia
        return Usuario(
            _id=resultado[0],
            _n=resultado[1],
            _a=resultado[2],
            _r=resultado[3],
            _s=resultado[4],
            _rol=resultado[5]
        )
    return None

def obtener_todos_docentes():
    """Recupera todos los usuarios con rol DOCENTE o DOCTOR y retorna una lista de objetos Usuario."""
    conn = sqlite3.connect("sistema_citas.db")
    cursor = conn.cursor()
    # Se filtran los roles que corresponden al personal médico/docente
    cursor.execute("SELECT id, nombre, apellidos, rut, sexo, rol FROM usuarios WHERE rol IN ('DOCENTE')")
    filas = cursor.fetchall()
    conn.close()

    docentes = []
    for f in filas:
        docentes.append(Usuario(
            _id=f[0],
            _n=f[1],
            _a=f[2],
            _r=f[3],
            _s=f[4],
            _rol=f[5]
        ))
    return docentes


def obtener_todas_citas():
    conn = sqlite3.connect("sistema_citas.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM citas")
    filas = cursor.fetchall()
    conn.close()

    citas = []
    for f in filas:
        c = Cita(f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8])
        c.id = f[0]
        c.estado = f[9]
        citas.append(c)

    return citas