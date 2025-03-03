from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import uuid

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete'

def get_db():
    conn = sqlite3.connect('ecole.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM etudiants")
    total_etudiants = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM enseignants")
    total_enseignants = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM cours")
    total_cours = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM inscriptions")
    total_inscriptions = c.fetchone()[0]

    conn.close()

    return render_template('dashboard.html', total_etudiants=total_etudiants,
                           total_enseignants=total_enseignants, total_cours=total_cours,
                           total_inscriptions=total_inscriptions)

@app.route('/ajout_etudiant', methods=['GET', 'POST'])
def ajout_etudiant():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        telephone = request.form.get('telephone')
        date_naissance = request.form['date_naissance']
        adresse = request.form.get('adresse')
        a_propos = request.form.get('a_propos')
        statut = 'Actif'

        identifiant = str(uuid.uuid4())[:8]

        db = get_db()
        cursor = db.cursor()
        cursor.execute('''INSERT INTO etudiants (identifiant, nom, prenom, email, telephone, date_naissance, adresse, a_propos, statut)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (identifiant, nom, prenom, email, telephone, date_naissance, adresse, a_propos, statut))
        db.commit()
        db.close()

        return redirect(url_for('liste_etudiants'))

    return render_template('ajout_etudiant.html')

@app.route('/modifier_etudiant/<string:identifiant>', methods=['GET', 'POST'])
def modifier_etudiant(identifiant):
    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        telephone = request.form['telephone']
        date_naissance = request.form['date_naissance']
        adresse = request.form.get('adresse')
        a_propos = request.form.get('a_propos')
        statut = request.form['statut']  # Ajout de la gestion du statut

        # Mettre à jour l'étudiant dans la base de données
        c.execute('''UPDATE etudiants SET nom=?, prenom=?, email=?, telephone=?, date_naissance=?, adresse=?, a_propos=?, statut=?, date_modification=CURRENT_TIMESTAMP
                     WHERE identifiant=?''',
                  (nom, prenom, email, telephone, date_naissance, adresse, a_propos, statut, identifiant))
        conn.commit()

        # Actions spécifiques en fonction du statut
        if statut == "Suspendu":
            # Bloquer l'inscription à de nouveaux cours
            c.execute("UPDATE inscriptions SET statut='Abandonnée' WHERE etudiant_id=?", (identifiant,))
            conn.commit()
        elif statut == "Expulsé":
            # Supprimer l'étudiant de toutes les inscriptions et cours
            c.execute("DELETE FROM inscriptions WHERE etudiant_id=?", (identifiant,))
            conn.commit()

        conn.close()
        return redirect(url_for('liste_etudiants'))

    c.execute("SELECT * FROM etudiants WHERE identifiant=?", (identifiant,))
    etudiant = c.fetchone()
    conn.close()
    return render_template('modifier_etudiant.html', etudiant=etudiant)


@app.route('/modifier_enseignant/<string:identifiant>', methods=['GET', 'POST'])
def modifier_enseignant(identifiant):
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        telephone = request.form['telephone']
        specialite = request.form['specialite']
        a_propos = request.form['a_propos']
        statut = request.form['statut']  # Ajout de la gestion du statut

        # Mettre à jour l'enseignant
        cursor.execute('''UPDATE enseignants SET nom=?, prenom=?, email=?, telephone=?, specialite=?, a_propos=?, statut=?, date_modification=CURRENT_TIMESTAMP
                     WHERE identifiant=?''',
                  (nom, prenom, email, telephone, specialite,a_propos, statut, identifiant))
        db.commit()

        # Actions spécifiques selon le statut
        if statut == "En congé":
            # Empêcher l'affectation de nouveaux cours
            cursor.execute("UPDATE cours SET enseignant_id=NULL WHERE enseignant_id=?", (identifiant,))
            db.commit()
        elif statut == "Retraité":
            # Empêcher l'affectation à de nouveaux cours mais garder son historique
            cursor.execute("UPDATE cours SET enseignant_id=NULL WHERE enseignant_id=?", (identifiant,))
            db.commit()

        db.close()
        return redirect(url_for('liste_enseignants'))

    cursor.execute("SELECT * FROM enseignants WHERE identifiant=?", (identifiant,))
    enseignant = cursor.fetchone()
    db.close()
    return render_template('modifier_enseignant.html', enseignant=enseignant)


@app.route('/modifier_cours/<string:identifiant>', methods=['GET', 'POST'])
def modifier_cours(identifiant):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, nom, prenom FROM enseignants WHERE statut='Actif'")
    enseignants = c.fetchall()

    if request.method == 'POST':
        nom = request.form['nom']
        code = request.form['code']
        description = request.form['description']
        credits = request.form['credits']
        capacite_max = request.form['capacite_max']
        enseignant_id = request.form['enseignant']
        statut = request.form['statut']  # Ajout de la gestion du statut

        # Mise à jour du cours
        c.execute('''UPDATE cours SET nom=?, code=?, description=?, credits=?, capacite_max=?, enseignant_id=?, statut=?, date_modification=CURRENT_TIMESTAMP
                     WHERE identifiant=?''',
                  (nom, code, description, credits, capacite_max, enseignant_id, statut, identifiant))
        conn.commit()

        # Actions spécifiques selon le statut
        if statut == "Fermé":
            # Désactiver les inscriptions futures
            c.execute("UPDATE inscriptions SET statut='Abandonnée' WHERE cours_identifiant=? AND statut='En attente'", (identifiant,))
            conn.commit()
        elif statut == "Annulé":
            # Annuler le cours et notifier les étudiants inscrits
            c.execute("UPDATE inscriptions SET statut='Abandonnée' WHERE cours_identifiant=?", (identifiant,))
            conn.commit()
            # Envoyer une notification ou un email aux étudiants inscrits (logique supplémentaire à ajouter)

        conn.close()
        return redirect(url_for('liste_cours', ))

    c.execute("SELECT * FROM cours WHERE identifiant=?", (identifiant,))
    cours = c.fetchone()
    conn.close()
    return render_template('modifier_cours.html', cours=cours, enseignants=enseignants)

@app.route('/ajout_cours', methods=['GET', 'POST'])
def ajout_cours():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, nom, prenom FROM enseignants WHERE statut='Actif'")
    enseignants = c.fetchall()

    if request.method == 'POST':
        nom = request.form['nom']
        code = request.form['code']
        description = request.form.get('description', '')
        credits = request.form['credits']
        capacite_max = request.form['capacite_max']
        enseignant_id = request.form['enseignant']
        statut = 'Actif'

        identifiant = str(uuid.uuid4())[:8]

        c.execute('''INSERT INTO cours (identifiant, nom, code, description, credits, capacite_max, enseignant_id, statut)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (identifiant, nom, code, description, credits, capacite_max, enseignant_id, statut))
        conn.commit()
        conn.close()
        return redirect(url_for('liste_cours'))

    return render_template('ajout_cours.html', enseignants=enseignants)


@app.route('/modifier_inscription/<string:identifiant>', methods=['GET', 'POST'])
def modifier_inscription(identifiant):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, nom, prenom FROM etudiants WHERE statut='Actif'")
    etudiants = c.fetchall()
    c.execute("SELECT id, nom FROM cours WHERE statut='Actif'")
    cours = c.fetchall()

    if request.method == 'POST':
        etudiant_id = request.form['etudiant']
        cours_id = request.form['cours']
        statut = request.form['statut'] 
        note_finale = request.form.get('note_finale', None) 

        # Mise à jour de l'inscription
        c.execute('''UPDATE inscriptions SET etudiant_id=?, cours_id=?, statut=?, note_finale=?, date_modification=CURRENT_TIMESTAMP WHERE identifiant=?''',
                  (etudiant_id, cours_id, statut, note_finale, identifiant))
        conn.commit()

        # Actions spécifiques selon le statut
        if statut == "Abandonnée":
            # Notifier l'étudiant de son abandon
            pass  # Logique à ajouter pour notifier
        elif statut == "Terminée":
            # Marquer l'inscription comme terminée et ajouter dans les rapports ou certificats
            pass  # Logique à ajouter pour générer un certificat

        conn.close()
        return redirect(url_for('liste_inscriptions'))

    c.execute("SELECT * FROM inscriptions WHERE identifiant=?", (identifiant,))
    inscription = c.fetchone()
    conn.close()
    return render_template('modifier_inscription.html', inscription=inscription, etudiants=etudiants, cours=cours)

@app.route('/etudiants')
def liste_etudiants():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM etudiants")
    etudiants = cursor.fetchall()
    db.close()
    return render_template('liste_etudiants.html', etudiants=etudiants)

@app.route('/supprimer_etudiant/<string:identifiant>')
def supprimer_etudiant(identifiant):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM etudiants WHERE identifiant=?", (identifiant,))
    conn.commit()
    conn.close()
    return redirect(url_for('liste_etudiants'))

@app.route('/ajout_enseignant', methods=['GET', 'POST'])
def ajout_enseignant():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        telephone = request.form['telephone']
        specialite = request.form['specialite']
        a_propos = request.form.get('a_propos', '')
        statut = 'Actif'

        identifiant = str(uuid.uuid4())[:8]

        db = get_db()
        cursor = db.cursor()
        cursor.execute('''INSERT INTO enseignants (identifiant, nom, prenom, email, telephone, specialite, a_propos, statut)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (identifiant, nom, prenom, email, telephone, specialite, a_propos, statut))
        db.commit()
        db.close()

        return redirect(url_for('liste_enseignants'))

    return render_template('ajout_enseignant.html')

@app.route('/enseignants')
def liste_enseignants():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM enseignants")
    enseignants = cursor.fetchall()
    db.close()
    return render_template('liste_enseignants.html', enseignants=enseignants)


@app.route('/supprimer_enseignant/<string:identifiant>')
def supprimer_enseignant(identifiant):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM enseignants WHERE identifiant=?", (identifiant,))
    db.commit()
    db.close()
    return redirect(url_for('liste_enseignants'))


@app.route('/cours')
def liste_cours():
    conn = get_db()
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux résultats comme des dictionnaires
    c = conn.cursor()
    c.execute("""
        SELECT cours.*, enseignants.nom AS enseignant_nom, enseignants.prenom AS enseignant_prenom
        FROM cours
        JOIN enseignants ON cours.enseignant_id = enseignants.id
    """)
    cours = c.fetchall()
    conn.close()
    return render_template('liste_cours.html', cours=cours)

@app.route('/supprimer_cours/<string:identifiant>')
def supprimer_cours(identifiant):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM cours WHERE identifiant=?", (identifiant,))
    conn.commit()
    conn.close()
    return redirect(url_for('liste_cours'))

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, nom, prenom FROM etudiants WHERE statut='Actif'")
    etudiants = c.fetchall()
    c.execute("SELECT id, nom FROM cours WHERE statut='Actif'")
    cours = c.fetchall()

    if request.method == 'POST':
        etudiant_id = request.form['etudiant']
        cours_id = request.form['cours']
        statut = 'En attente'

        identifiant = str(uuid.uuid4())[:8]

        c.execute('''INSERT INTO inscriptions (identifiant, etudiant_id, cours_id, statut)
                     VALUES (?, ?, ?, ?)''',
                  (identifiant, etudiant_id, cours_id, statut))
        conn.commit()
        conn.close()
        return redirect(url_for('liste_inscriptions'))

    return render_template('inscription.html', etudiants=etudiants, cours=cours)

@app.route('/inscriptions')
def liste_inscriptions():
    conn = get_db()
    conn.row_factory = sqlite3.Row  # Ajoutez cette ligne
    c = conn.cursor()
    
    c.execute('''SELECT inscriptions.*, etudiants.nom AS etudiant_nom, etudiants.prenom AS etudiant_prenom,
                 cours.nom AS cours_nom FROM inscriptions
                 JOIN etudiants ON inscriptions.etudiant_id = etudiants.id
                 JOIN cours ON inscriptions.cours_id = cours.id''')
    
    inscriptions = c.fetchall()
    conn.close()
    
    return render_template('liste_inscriptions.html', inscriptions=inscriptions)


@app.route('/supprimer_inscription/<string:identifiant>')
def supprimer_inscription(identifiant):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM inscriptions WHERE identifiant=?", (identifiant,))
    conn.commit()
    conn.close()
    return redirect(url_for('liste_inscriptions'))

if __name__ == "__main__":
    app.run(debug=True)
