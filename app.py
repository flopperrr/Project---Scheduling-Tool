from flask import Flask, request, render_template, redirect, url_for, flash
import sqlite3
import os
from flask import jsonify
from datetime import datetime
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash

#Initialize the Flask application

app = Flask(__name__)
app.secret_key = 'yoursecretkey'

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d/%m/%Y'):
    try:
        return datetime.strptime(value, '%Y-%m-%d').strftime(format)
    except:
        return value

#Require login on all routes except ‘login’ and static assets

@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect(url_for('login'))

DB_PATH = 'SchedulingTool.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

#Creates tables only if DB file is missing it won’t run on existing DB

def init_db():
    if not os.path.exists(DB_PATH):
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                preferred_name TEXT,
                gender TEXT,
                address TEXT,
                date_of_birth TEXT,
                phone TEXT,
                email TEXT,
                health_fund TEXT,
                medicare_number TEXT,
                medicare_reference TEXT,
                medicare_expiry TEXT,
                general_practitioner TEXT,
                referral TEXT
            );
        ''')
        conn.execute('''
            CREATE TABLE appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                appointment_time TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            );
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        ''')
        accounts = {
            'Doctor':   'Admin123@!',
            'Staff1':   'Staff01$',
            'Staff2':   'Staff02$'
        }
        for uname, pwd in accounts.items():
            hashed = generate_password_hash(pwd)
            conn.execute(
                'INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)',
                (uname, hashed)
            )
        conn.commit()
        conn.close()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    date_filter = request.form.get('filter_date') if request.method == 'POST' else None
    conn = get_db_connection()

    if date_filter:
        appointments = conn.execute('''
            SELECT appointments.id, appointment_time, appointments.patient_id,
                   patients.first_name, patients.last_name, patients.preferred_name, patients.phone, appointments.note
            FROM appointments
            JOIN patients ON appointments.patient_id = patients.id
            WHERE DATE(appointment_time) = ?
            ORDER BY appointment_time
        ''', (date_filter,)).fetchall()
    else:
        appointments = conn.execute('''
            SELECT appointments.id, appointment_time, appointments.patient_id,
                   patients.first_name, patients.last_name, patients.preferred_name, patients.phone, appointments.note
            FROM appointments
            JOIN patients ON appointments.patient_id = patients.id
            ORDER BY appointment_time
        ''').fetchall()

    formatted_appointments = []
    for appt in appointments:
        try:
            dt = datetime.fromisoformat(appt['appointment_time'])
            formatted_time = dt.strftime('%d/%m/%Y %H:%M')
        except ValueError:
            formatted_time = appt['appointment_time']
        appt_dict = dict(appt)
        appt_dict['formatted_time'] = formatted_time
        formatted_appointments.append(appt_dict)

    patients = conn.execute('SELECT * FROM patients').fetchall()
    conn.close()

    return render_template('dashboard.html', appointments=formatted_appointments, patients=patients, filter_date=date_filter)

@app.route('/add', methods=['POST'])
def add_appointment():
    patient_id = request.form['patient_id']
    appointment_time = request.form['appointment_time']
    note = request.form.get('note')

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO appointments (patient_id, appointment_time, note)
        VALUES (?, ?, ?)
    ''', (patient_id, appointment_time, note))
    conn.commit()
    conn.close()

    flash("Appointment added successfully.")
    return redirect(url_for('dashboard'))

@app.route('/add_patient', methods=['POST'])
def add_patient():
    data = request.form
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO patients (
            last_name, first_name, preferred_name, gender, address,
            date_of_birth, phone, email, health_fund,
            medicare_number, medicare_reference, medicare_expiry,
            general_practitioner, referral
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['last_name'], data['first_name'], data.get('preferred_name'),
        data.get('gender'), data.get('address'), data.get('date_of_birth'),
        data.get('phone'), data.get('email'), data.get('health_fund'),
        data.get('medicare_number'), data.get('medicare_reference'),
        data.get('medicare_expiry'), data.get('general_practitioner'),
        data.get('referral')
    ))
    conn.commit()
    conn.close()

    flash("New patient added successfully!")
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:appointment_id>')
def delete_appointment(appointment_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
    conn.commit()
    conn.close()
    flash('Appointment deleted successfully.')
    return redirect(url_for('dashboard'))

@app.route('/edit_appointment/<int:appointment_id>', methods=['POST'])
def edit_appointment(appointment_id):
    new_time = request.form['appointment_time']
    new_note = request.form.get('note', '')
    conn = get_db_connection()
    conn.execute('UPDATE appointments SET appointment_time = ?, note = ? WHERE id = ?', (new_time, new_note, appointment_id))
    conn.commit()
    conn.close()

    flash("Appointment updated successfully!")
    return redirect(url_for('dashboard'))

@app.route('/edit_patient/<int:patient_id>', methods=['POST'])
def edit_patient(patient_id):
    data = request.form
    conn = get_db_connection()
    conn.execute('''
        UPDATE patients SET
            last_name = ?, first_name = ?, preferred_name = ?, gender = ?, address = ?,
            date_of_birth = ?, phone = ?, email = ?, health_fund = ?,
            medicare_number = ?, medicare_reference = ?, medicare_expiry = ?,
            general_practitioner = ?, referral = ?
        WHERE id = ?
    ''', (
        data['last_name'], data['first_name'], data.get('preferred_name'), data.get('gender'),
        data.get('address'), data.get('date_of_birth'), data.get('phone'), data.get('email'),
        data.get('health_fund'), data.get('medicare_number'), data.get('medicare_reference'),
        data.get('medicare_expiry'), data.get('general_practitioner'), data.get('referral'),
        patient_id
    ))
    conn.commit()
    conn.close()

    flash("Patient details updated.")
    return redirect(url_for('dashboard'))

@app.route('/delete_patient/<int:patient_id>')
def delete_patient(patient_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM patients WHERE id = ?', (patient_id,))
    conn.commit()
    conn.close()
    flash('Patient deleted successfully.')
    return redirect(url_for('dashboard'))

@app.route('/patient/<int:patient_id>')
def patientprofile(patient_id):
    conn = get_db_connection()
    patient = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    appointments = conn.execute('''
        SELECT * FROM appointments
        WHERE patient_id = ?
        ORDER BY appointment_time
    ''', (patient_id,)).fetchall()
    conn.close()

    if patient is None:
        return f"<h2>Patient ID {patient_id} not found</h2>", 404

    formatted_appointments = []
    for appt in appointments:
        try:
            dt = datetime.fromisoformat(appt['appointment_time'])
            formatted_time = dt.strftime('%d/%m/%Y %H:%M')
        except ValueError:
            formatted_time = appt['appointment_time']
        appt_dict = dict(appt)
        appt_dict['formatted_time'] = formatted_time
        formatted_appointments.append(appt_dict)

    return render_template('patientprofile.html', patient=patient, appointments=formatted_appointments)

@app.route('/calendar')
def calendar_view():
    conn = get_db_connection()
    patients = conn.execute('SELECT * FROM patients').fetchall()
    conn.close()
    return render_template("calendar.html", patients=patients)

@app.route('/api/events')
def api_events():
    patient_id = request.args.get('patient_id')
    conn = get_db_connection()

    if patient_id:
        appointments = conn.execute('''
            SELECT appointment_time, patients.first_name, patients.last_name,
                   patients.preferred_name, patients.id, appointments.note
            FROM appointments
            JOIN patients ON appointments.patient_id = patients.id
            WHERE patients.id = ?
        ''', (patient_id,)).fetchall()
    else:
        appointments = conn.execute('''
            SELECT appointment_time, patients.first_name, patients.last_name,
                   patients.preferred_name, patients.id, appointments.note
            FROM appointments
            JOIN patients ON appointments.patient_id = patients.id
        ''').fetchall()

    conn.close()

    events = []
    for a in appointments:
        iso_time = a['appointment_time']
        if "T" in iso_time and len(iso_time) == 16:
            iso_time += ":00"
        events.append({
    "title": f"{a['preferred_name'] or a['first_name']} {a['last_name']}",
    "start": iso_time,
    "extendedProps": {
        "patientId": a["id"],
        "note": a["note"] or "",
        "preferredName": a["preferred_name"],
        "firstName": a["first_name"],
        "lastName": a["last_name"]
    }
})

    return jsonify(events)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password.'
    return render_template('login.html', error=error)

#Clears session to log out user securely

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
    
