import sqlite3

def init_db():
    conn = sqlite3.connect("ecole.db")
    cursor = conn.cursor()

    # Activer les clés étrangères
    cursor.execute("PRAGMA foreign_keys = ON")

    # Create teachers table first as it is referenced by courses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enseignants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifiant TEXT UNIQUE NOT NULL,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        telephone TEXT UNIQUE NOT NULL,
        specialite TEXT NOT NULL,
        a_propos TEXT,
        statut TEXT CHECK(statut IN ('Actif', 'En congé', 'Retraité')) NOT NULL,
        date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
        date_modification TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create courses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cours (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifiant TEXT UNIQUE NOT NULL,
        nom TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        description TEXT,
        credits INTEGER NOT NULL,
        capacite_max INTEGER NOT NULL,
        enseignant_id INTEGER NOT NULL,
        statut TEXT CHECK(statut IN ('Actif', 'Fermé', 'Annulé')) NOT NULL,
        date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
        date_modification TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (enseignant_id) REFERENCES enseignants (id)
    )
    """)

    # Create students table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS etudiants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifiant TEXT UNIQUE NOT NULL,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        telephone TEXT UNIQUE,
        date_naissance TEXT NOT NULL,
        adresse TEXT,
        a_propos TEXT,
        statut TEXT CHECK(statut IN ('Actif', 'Suspendu', 'Expulsé', 'Diplômé')) NOT NULL,
        date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
        date_modification TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create enrollments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifiant TEXT UNIQUE NOT NULL,
        etudiant_id INTEGER NOT NULL,
        cours_id INTEGER NOT NULL,
        date_inscription TEXT DEFAULT CURRENT_TIMESTAMP,
        statut TEXT CHECK(statut IN ('En attente', 'Actif', 'Abandonné', 'Terminé')) NOT NULL,
        note_finale REAL,
        date_modification TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (etudiant_id) REFERENCES etudiants (id),
        FOREIGN KEY (cours_id) REFERENCES cours (id)
    )
    """)

    # Commit changes and close connection
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
