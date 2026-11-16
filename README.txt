# HostelSphere - Hostel Management System

## Features included
- Admin dashboard with summary cards
- Student registration with required details, 11-digit phone validation and password confirmation
- Student records: add, view, search, edit and delete
- Room management: add, view, search, edit and delete, including capacity and available-bed calculation
- Fee management: add, view, search, edit and delete, with paid-fee dashboard total
- Attendance: mark, view, search, edit and delete; duplicate attendance for the same roll number/date is prevented
- Complaints: student complaint submission and admin view, search, edit status and delete
- PostgreSQL persistence for all modules (not browser localStorage)
- Student portal displays admin-entered fees, paid payment history, room assignment, attendance and complaints
- Fee and attendance entries are checked against registered student roll numbers; student name and canonical roll number are taken from the student record
- Editing a student's name or roll number keeps related fees, attendance and complaints synchronized
- Room assignment checks room existence/capacity and updates occupied-bed counts; renaming a room keeps student assignments connected

## Requirements
- Python 3.10+
- PostgreSQL and pgAdmin
- Python packages in `requirements.txt`

## Setup (Windows / VS Code)
1. Extract the ZIP.
2. Open the extracted `Hostel-MS` folder in VS Code.
3. Open `db.py` and replace `YOUR_POSTGRES_PASSWORD` with the password for your local PostgreSQL `postgres` user.
4. Open VS Code Terminal in this folder.
5. Install dependencies:
   `python -m pip install -r requirements.txt`
6. Confirm PostgreSQL is running and that the database `hostel_management` exists.
   The application creates/updates its tables automatically when it starts.
7. Start the server:
   `python app.py`
8. Open these pages in Chrome:
   - Admin: http://127.0.0.1:5000/admin
   - Student Registration: http://127.0.0.1:5000/student
   - Student Login: http://127.0.0.1:5000/student-login
   - Student Dashboard (after login): http://127.0.0.1:5000/student-dashboard
   - Student Complaint: http://127.0.0.1:5000/complaint
   - Database test: http://127.0.0.1:5000/test-db

## Demo admin login
- Username: `admin`
- Password: `12345`

Change these demo credentials before using the project outside a classroom/local demonstration. The current admin login is a simple front-end demonstration, not production-grade authentication.

## Important
- Keep the terminal running while using the website.
- Do not open the HTML files by double-clicking them. Use the Flask URLs above.
- Never upload your real database password publicly.
- Student passwords are stored as password hashes, not plain text.
- Existing database tables are preserved; the app adds the extra columns/tables it needs at startup.
