# Project---Scheduling-Tool

Doctor Scheduling System

A browser based scheduling tool for doctors and receptionists to manage patient bookings, view appointment history and streamline clinic operations. This system supports secure login, live appointment tracking and editable patient records.

Instructions
Step 1 - Install dependencies
pip install flask

Step 2 - Run the app
python app.py

Features

User Authentication
  - Login system with password hashing
  - Session-based access control

Patient Management
  - Add, edit, delete patient records
  - Stores full contact, Medicare, and referral information
    
Appointment Booking
  - Create, update, and cancel appointments
  - Attach notes or visit reasons to bookings

Dashboard & Calendar View
  - Filter appointments by date
  - Navigate by patient or time
  - Visual monthly appointment calendar

Patient Profiles
  - See full appointment history for each patient
  - Editable directly from patient card

Libaries & More
- Backend: Flask (Python)
- Database: SQLite
- Frontend: HTML5, Bootstrap 5, Jinja2 templates
- Security: Werkzeug password hashing, session management
