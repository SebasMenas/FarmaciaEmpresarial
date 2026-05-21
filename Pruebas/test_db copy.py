import sqlite3
from clases import Usuario

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