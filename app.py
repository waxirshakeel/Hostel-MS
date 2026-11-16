
import os
from datetime import date, datetime
from decimal import Decimal

from flask import Flask, jsonify, request, send_from_directory, session, redirect
from psycopg.rows import dict_row
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db_connection


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "hostelsphere-local-dev-key")


# ==========================================
# DATABASE HELPER FUNCTIONS
# ==========================================

def json_safe(value):
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def query_all(sql, params=()):
    conn = get_db_connection()
    if conn is None:
        raise RuntimeError("Database connection failed. Check db.py password and PostgreSQL.")

    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return json_safe(rows)
    finally:
        conn.close()


def query_one(sql, params=()):
    conn = get_db_connection()
    if conn is None:
        raise RuntimeError("Database connection failed. Check db.py password and PostgreSQL.")

    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            conn.commit()
        return json_safe(row) if row else None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute(sql, params=()):
    conn = get_db_connection()
    if conn is None:
        raise RuntimeError("Database connection failed. Check db.py password and PostgreSQL.")

    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ==========================================
# DATABASE TABLES
# ==========================================

def init_db():
    conn = get_db_connection()
    if conn is None:
        raise RuntimeError("Could not connect to PostgreSQL. Update the password in db.py.")

    try:
        with conn.cursor() as cur:

            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id SERIAL PRIMARY KEY,
                    full_name VARCHAR(100) NOT NULL,
                    roll_number VARCHAR(50) UNIQUE NOT NULL,
                    department VARCHAR(100) NOT NULL,
                    contact_number VARCHAR(11) NOT NULL,
                    guardian_contact VARCHAR(11) NOT NULL,
                    email VARCHAR(150) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    gender VARCHAR(20) NOT NULL,
                    address TEXT NOT NULL,
                    room_number VARCHAR(50),
                    status VARCHAR(20) NOT NULL DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                ALTER TABLE students
                ADD COLUMN IF NOT EXISTS room_number VARCHAR(50)
            """)

            cur.execute("""
                ALTER TABLE students
                ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'Active'
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    room_id SERIAL PRIMARY KEY,
                    room_number VARCHAR(50) UNIQUE NOT NULL,
                    capacity INTEGER NOT NULL CHECK (capacity > 0),
                    occupied_beds INTEGER NOT NULL DEFAULT 0 CHECK (occupied_beds >= 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS fees (
                    fee_id SERIAL PRIMARY KEY,
                    student_name VARCHAR(100) NOT NULL,
                    roll_number VARCHAR(50) NOT NULL,
                    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
                    fee_month VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'Unpaid',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    attendance_id SERIAL PRIMARY KEY,
                    student_name VARCHAR(100) NOT NULL,
                    roll_number VARCHAR(50) NOT NULL,
                    attendance_date DATE NOT NULL,
                    status VARCHAR(20) NOT NULL CHECK (status IN ('Present', 'Absent')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (roll_number, attendance_date)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS complaints (
                    complaint_id SERIAL PRIMARY KEY,
                    student_id INTEGER REFERENCES students(student_id) ON DELETE SET NULL,
                    student_name VARCHAR(100) NOT NULL,
                    roll_number VARCHAR(50) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    subject VARCHAR(200) NOT NULL,
                    details TEXT NOT NULL,
                    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
                    complaint_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                ALTER TABLE complaints
                ADD COLUMN IF NOT EXISTS student_name VARCHAR(100)
            """)

            cur.execute("""
                ALTER TABLE complaints
                ADD COLUMN IF NOT EXISTS roll_number VARCHAR(50)
            """)

            cur.execute("""
                ALTER TABLE complaints
                ADD COLUMN IF NOT EXISTS complaint_date DATE DEFAULT CURRENT_DATE
            """)

            cur.execute("""
                ALTER TABLE complaints
                ALTER COLUMN student_id DROP NOT NULL
            """)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ==========================================
# HTML AND STATIC FILE ROUTES
# ==========================================

@app.route("/")
@app.route("/admin")
def admin_page():
    return send_from_directory(app.root_path, "index.html")


@app.route("/student")
@app.route("/student-register")
def student_page():
    return send_from_directory(app.root_path, "student.html")


@app.route("/complaint")
def complaint_page():
    return send_from_directory(app.root_path, "complaint.html")


@app.route("/style.css")
def stylesheet():
    return send_from_directory(app.root_path, "style.css")


@app.route("/script.js")
def javascript():
    return send_from_directory(app.root_path, "script.js")


@app.route("/student-login.js")
def student_login_js():
    return send_from_directory(app.root_path, "student-login.js")


@app.route("/student-dashboard.js")
def student_dashboard_js():
    return send_from_directory(app.root_path, "student-dashboard.js")


@app.get("/test-db")
def test_database():
    try:
        query_all("SELECT 1 AS connected")
        return "PostgreSQL Database Connected Successfully!"
    except Exception as error:
        return f"Database Connection Failed: {error}", 500


# ==========================================
# STUDENT MANAGEMENT
# ==========================================

@app.get("/api/students")
def get_students():
    try:
        rows = query_all("""
            SELECT student_id, full_name, roll_number, department,
                   contact_number, guardian_contact, email, gender,
                   address, room_number, status, created_at
            FROM students
            ORDER BY student_id DESC
        """)
        return jsonify(rows)
    except Exception as error:
        return jsonify({"message": str(error)}), 500


@app.get("/api/students/pending")
def get_pending_students():
    try:
        rows = query_all("""
            SELECT student_id, full_name, roll_number,
                   department, contact_number, email, status
            FROM students
            WHERE status = 'Pending'
            ORDER BY student_id DESC
        """)
        return jsonify(rows)

    except Exception:
        app.logger.exception("Pending students loading failed")
        return jsonify({"message": "Could not load pending students."}), 500


@app.put("/api/students/<int:student_id>/approval")
def approve_student(student_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    if status not in ("Active", "Rejected"):
        return jsonify({"message": "Invalid approval status."}), 400

    try:
        row = query_one("""
            UPDATE students
            SET status = %s
            WHERE student_id = %s AND status = 'Pending'
            RETURNING student_id
        """, (status, student_id))

        if not row:
            return jsonify({
                "message": "Student not found or already processed."
            }), 404

        return jsonify({
            "message": f"Student {status} successfully.",
            "status": status
        })

    except Exception:
        app.logger.exception("Student approval failed")
        return jsonify({"message": "Could not update student approval."}), 500


@app.post("/api/register")
def register_student():
    data = request.get_json(silent=True) or {}

    required = [
        "full_name", "roll_number", "department",
        "contact_number", "guardian_contact",
        "email", "password", "gender", "address"
    ]

    missing = [
        field for field in required
        if not str(data.get(field, "")).strip()
    ]

    if missing:
        return jsonify({
            "message": "Please complete all registration fields."
        }), 400

    if len(data["contact_number"]) != 11 or not data["contact_number"].isdigit():
        return jsonify({
            "message": "Contact number must contain exactly 11 digits."
        }), 400

    if len(data["guardian_contact"]) != 11 or not data["guardian_contact"].isdigit():
        return jsonify({
            "message": "Guardian contact must contain exactly 11 digits."
        }), 400

    if len(data["password"]) < 8:
        return jsonify({
            "message": "Password must be at least 8 characters."
        }), 400

    try:
        student = query_one("""
            INSERT INTO students
            (full_name, roll_number, department, contact_number,
             guardian_contact, email, password_hash, gender,
             address, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'Pending')
            RETURNING student_id
        """, (
            data["full_name"].strip(),
            data["roll_number"].strip(),
            data["department"].strip(),
            data["contact_number"],
            data["guardian_contact"],
            data["email"].strip().lower(),
            generate_password_hash(data["password"]),
            data["gender"],
            data["address"].strip()
        ))

        return jsonify({
            "message": "Registration submitted! Please wait for Admin Approval.",
            "student_id": student["student_id"],
            "status": "Pending"
        }), 201

    except Exception as error:
        if "unique" in str(error).lower() or "duplicate" in str(error).lower():
            return jsonify({
                "message": "This Roll Number or Email is already registered."
            }), 409

        app.logger.exception("Student registration failed")
        return jsonify({
            "message": "Registration failed. Please try again."
        }), 500


@app.put("/api/students/<int:student_id>")
def update_student(student_id):
    data = request.get_json(silent=True) or {}

    allowed = {
        "full_name": "full_name",
        "roll_number": "roll_number",
        "contact_number": "contact_number",
        "room_number": "room_number",
        "status": "status",
        "department": "department"
    }
    updates = [
        (column, data[key].strip() if isinstance(data[key], str) else data[key])
        for key, column in allowed.items()
        if key in data
    ]
    if not updates:
        return jsonify({"message": "No changes supplied."}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection failed."}), 500

    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT student_id, full_name, roll_number, room_number FROM students WHERE student_id=%s FOR UPDATE",
                (student_id,)
            )
            old_student = cur.fetchone()
            if not old_student:
                return jsonify({"message": "Student not found."}), 404

            values = dict(updates)
            new_roll = values.get("roll_number", old_student["roll_number"])
            new_name = values.get("full_name", old_student["full_name"])
            new_room = values.get("room_number", old_student["room_number"])
            new_room = new_room.strip() if isinstance(new_room, str) else new_room
            new_room = new_room or None

            if new_room:
                cur.execute(
                    "SELECT room_id, capacity FROM rooms WHERE room_number=%s FOR UPDATE",
                    (new_room,)
                )
                room = cur.fetchone()
                if not room:
                    return jsonify({"message": "This room does not exist. Please add it in Room Management first."}), 400
                cur.execute(
                    "SELECT COUNT(*) AS total FROM students WHERE room_number=%s AND student_id<>%s",
                    (new_room, student_id)
                )
                occupied = cur.fetchone()["total"]
                if occupied >= room["capacity"]:
                    return jsonify({"message": "This room is already full."}), 400

            assignments = ", ".join(f"{column}=%s" for column, _ in updates)
            params = [value for _, value in updates]
            if "room_number" in values:
                # Store an empty room assignment as NULL.
                params[[column for column, _ in updates].index("room_number")] = new_room
            cur.execute(
                f"UPDATE students SET {assignments} WHERE student_id=%s",
                tuple(params) + (student_id,)
            )

            # Keep fee, attendance and complaint records connected if the admin edits a student's roll number/name.
            if new_roll != old_student["roll_number"] or new_name != old_student["full_name"]:
                cur.execute(
                    "UPDATE fees SET roll_number=%s, student_name=%s WHERE roll_number=%s",
                    (new_roll, new_name, old_student["roll_number"])
                )
                cur.execute(
                    "UPDATE attendance SET roll_number=%s, student_name=%s WHERE roll_number=%s",
                    (new_roll, new_name, old_student["roll_number"])
                )
                cur.execute(
                    "UPDATE complaints SET roll_number=%s, student_name=%s WHERE student_id=%s",
                    (new_roll, new_name, student_id)
                )

            # Keep room occupancy consistent with actual student assignments.
            affected_rooms = {r for r in (old_student["room_number"], new_room) if r}
            for room_number in affected_rooms:
                cur.execute(
                    "UPDATE rooms SET occupied_beds=(SELECT COUNT(*) FROM students WHERE room_number=%s) WHERE room_number=%s",
                    (room_number, room_number)
                )

        conn.commit()
        return jsonify({"message": "Student updated successfully. Related fee, attendance and room records are synchronized."})

    except Exception:
        conn.rollback()
        app.logger.exception("Student update failed")
        return jsonify({"message": "Could not update student. Check duplicate roll number and room capacity."}), 400
    finally:
        conn.close()


@app.delete("/api/students/<int:student_id>")
def delete_student(student_id):
    try:
        execute(
            "UPDATE complaints SET student_id = NULL WHERE student_id = %s",
            (student_id,)
        )
        execute(
            "DELETE FROM students WHERE student_id = %s",
            (student_id,)
        )
        return jsonify({"message": "Student deleted successfully."})

    except Exception:
        app.logger.exception("Student delete failed")
        return jsonify({"message": "Could not delete student."}), 500


# ==========================================
# ROOM MANAGEMENT
# ==========================================

@app.get("/api/rooms")
def get_rooms():
    try:
        return jsonify(query_all(
            "SELECT * FROM rooms ORDER BY room_number"
        ))
    except Exception as error:
        return jsonify({"message": str(error)}), 500


@app.post("/api/rooms")
def add_room():
    data = request.get_json(silent=True) or {}

    try:
        capacity = int(data.get("capacity", 0))
        occupied = int(data.get("occupied_beds", 0))

        if (
            not data.get("room_number")
            or capacity < 1
            or occupied < 0
            or occupied > capacity
        ):
            return jsonify({
                "message": "Enter valid room number, capacity and occupied beds."
            }), 400

        row = query_one("""
            INSERT INTO rooms (room_number, capacity, occupied_beds)
            VALUES (%s,%s,%s)
            RETURNING *
        """, (
            data["room_number"].strip(),
            capacity,
            occupied
        ))

        return jsonify(row), 201

    except Exception as error:
        if "unique" in str(error).lower() or "duplicate" in str(error).lower():
            return jsonify({
                "message": "This room number already exists."
            }), 409

        return jsonify({
            "message": "Could not save room. Check the values."
        }), 400


@app.put("/api/rooms/<int:room_id>")
def update_room(room_id):
    data = request.get_json(silent=True) or {}
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection failed."}), 500
    try:
        capacity = int(data.get("capacity", 0))
        requested_occupied = int(data.get("occupied_beds", 0))
        new_number = (data.get("room_number") or "").strip()
        if capacity < 1 or requested_occupied < 0 or requested_occupied > capacity or not new_number:
            return jsonify({"message": "Invalid room details."}), 400

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT room_number FROM rooms WHERE room_id=%s FOR UPDATE", (room_id,))
            old_room = cur.fetchone()
            if not old_room:
                return jsonify({"message": "Room not found."}), 404

            old_number = old_room["room_number"]
            cur.execute("SELECT COUNT(*) AS total FROM students WHERE room_number=%s", (old_number,))
            assigned_count = cur.fetchone()["total"]
            if assigned_count > capacity:
                return jsonify({"message": f"{assigned_count} students are assigned to this room; capacity cannot be less than that."}), 400

            # Rename the room and update every student's assigned room at the same time.
            cur.execute("""
                UPDATE rooms SET room_number=%s, capacity=%s, occupied_beds=%s
                WHERE room_id=%s
            """, (new_number, capacity, assigned_count if assigned_count else requested_occupied, room_id))
            if new_number != old_number:
                cur.execute("UPDATE students SET room_number=%s WHERE room_number=%s", (new_number, old_number))

        conn.commit()
        return jsonify({"message": "Room updated successfully. Student room assignments remain connected."})
    except Exception:
        conn.rollback()
        app.logger.exception("Room update failed")
        return jsonify({"message": "Could not update room. Room number may already exist."}), 400
    finally:
        conn.close()


@app.delete("/api/rooms/<int:room_id>")
def delete_room(room_id):
    try:
        execute(
            "DELETE FROM rooms WHERE room_id=%s",
            (room_id,)
        )
        return jsonify({"message": "Room deleted successfully."})

    except Exception:
        return jsonify({"message": "Could not delete room."}), 400


# ==========================================
# ADMIN FEES MANAGEMENT
# ==========================================

@app.get("/api/fees")
def get_fees():
    try:
        return jsonify(query_all(
            "SELECT * FROM fees ORDER BY fee_id DESC"
        ))
    except Exception as error:
        return jsonify({"message": str(error)}), 500


@app.post("/api/fees")
def add_fee():
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get("amount", 0))
        roll_number = (data.get("roll_number") or "").strip()
        fee_month = (data.get("fee_month") or "").strip()
        if not roll_number or not fee_month or amount <= 0:
            return jsonify({"message": "Enter a valid student roll number, fee month and amount."}), 400

        student = query_one("""
            SELECT full_name, roll_number FROM students
            WHERE LOWER(TRIM(roll_number)) = LOWER(TRIM(%s))
        """, (roll_number,))
        if not student:
            return jsonify({"message": "Student roll number not found. Register the student first."}), 404

        status = data.get("status", "Unpaid")
        if status not in ("Paid", "Unpaid"):
            return jsonify({"message": "Fee status must be Paid or Unpaid."}), 400

        row = query_one("""
            INSERT INTO fees (student_name, roll_number, amount, fee_month, status)
            VALUES (%s,%s,%s,%s,%s) RETURNING *
        """, (student["full_name"], student["roll_number"], amount, fee_month, status))
        return jsonify(row), 201
    except Exception:
        app.logger.exception("Fee creation failed")
        return jsonify({"message": "Could not save fee record."}), 400


@app.put("/api/fees/<int:fee_id>")
def update_fee(fee_id):
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get("amount", 0))
        roll_number = (data.get("roll_number") or "").strip()
        fee_month = (data.get("fee_month") or "").strip()
        status = data.get("status")
        if amount <= 0 or not roll_number or not fee_month or status not in ("Paid", "Unpaid"):
            return jsonify({"message": "Invalid fee details."}), 400

        student = query_one("""
            SELECT full_name, roll_number FROM students
            WHERE LOWER(TRIM(roll_number)) = LOWER(TRIM(%s))
        """, (roll_number,))
        if not student:
            return jsonify({"message": "Student roll number not found."}), 404

        execute("""
            UPDATE fees SET student_name=%s, roll_number=%s, amount=%s,
                fee_month=%s, status=%s WHERE fee_id=%s
        """, (student["full_name"], student["roll_number"], amount, fee_month, status, fee_id))
        return jsonify({"message": "Fee updated successfully."})
    except Exception:
        app.logger.exception("Fee update failed")
        return jsonify({"message": "Could not update fee."}), 400


@app.delete("/api/fees/<int:fee_id>")
def delete_fee(fee_id):
    try:
        execute(
            "DELETE FROM fees WHERE fee_id=%s",
            (fee_id,)
        )
        return jsonify({"message": "Fee record deleted successfully."})

    except Exception:
        return jsonify({"message": "Could not delete fee record."}), 400


# ==========================================
# ADMIN ATTENDANCE MANAGEMENT
# ==========================================

@app.get("/api/attendance")
def get_attendance():
    try:
        return jsonify(query_all("""
            SELECT * FROM attendance
            ORDER BY attendance_date DESC, attendance_id DESC
        """))
    except Exception as error:
        return jsonify({"message": str(error)}), 500


@app.post("/api/attendance")
def add_attendance():
    data = request.get_json(silent=True) or {}
    try:
        roll_number = (data.get("roll_number") or "").strip()
        attendance_date = data.get("attendance_date")
        status = data.get("status")
        if not roll_number or not attendance_date:
            return jsonify({"message": "Enter student roll number and attendance date."}), 400
        if status not in ("Present", "Absent"):
            return jsonify({"message": "Choose Present or Absent."}), 400

        student = query_one("""
            SELECT full_name, roll_number FROM students
            WHERE LOWER(TRIM(roll_number)) = LOWER(TRIM(%s))
        """, (roll_number,))
        if not student:
            return jsonify({"message": "Student roll number not found. Register the student first."}), 404

        row = query_one("""
            INSERT INTO attendance (student_name, roll_number, attendance_date, status)
            VALUES (%s,%s,%s,%s) RETURNING *
        """, (student["full_name"], student["roll_number"], attendance_date, status))
        return jsonify(row), 201
    except Exception as error:
        if "unique" in str(error).lower() or "duplicate" in str(error).lower():
            return jsonify({"message": "Attendance for this student and date already exists."}), 409
        app.logger.exception("Attendance creation failed")
        return jsonify({"message": "Could not save attendance. Check date and details."}), 400


@app.put("/api/attendance/<int:attendance_id>")
def update_attendance(attendance_id):
    data = request.get_json(silent=True) or {}
    try:
        roll_number = (data.get("roll_number") or "").strip()
        attendance_date = data.get("attendance_date")
        status = data.get("status")
        if not roll_number or not attendance_date or status not in ("Present", "Absent"):
            return jsonify({"message": "Complete attendance details and choose Present or Absent."}), 400

        student = query_one("""
            SELECT full_name, roll_number FROM students
            WHERE LOWER(TRIM(roll_number)) = LOWER(TRIM(%s))
        """, (roll_number,))
        if not student:
            return jsonify({"message": "Student roll number not found."}), 404

        execute("""
            UPDATE attendance SET student_name=%s, roll_number=%s,
                attendance_date=%s, status=%s WHERE attendance_id=%s
        """, (student["full_name"], student["roll_number"], attendance_date, status, attendance_id))
        return jsonify({"message": "Attendance updated successfully."})
    except Exception:
        app.logger.exception("Attendance update failed")
        return jsonify({"message": "Could not update attendance. Duplicate date may exist."}), 400


@app.delete("/api/attendance/<int:attendance_id>")
def delete_attendance(attendance_id):
    try:
        execute(
            "DELETE FROM attendance WHERE attendance_id=%s",
            (attendance_id,)
        )
        return jsonify({"message": "Attendance deleted successfully."})

    except Exception:
        return jsonify({"message": "Could not delete attendance."}), 400


# ==========================================
# ADMIN COMPLAINT MANAGEMENT
# ==========================================

@app.get("/api/complaints")
def get_complaints():
    try:
        return jsonify(query_all(
            "SELECT * FROM complaints ORDER BY complaint_id DESC"
        ))
    except Exception as error:
        return jsonify({"message": str(error)}), 500


@app.post("/api/complaints")
def add_complaint():
    data = request.get_json(silent=True) or {}

    required = (
        "student_name", "roll_number", "category",
        "subject", "details"
    )

    if any(
        not str(data.get(key, "")).strip()
        for key in required
    ):
        return jsonify({
            "message": "Please complete all complaint fields."
        }), 400

    try:
        student = query_one(
            "SELECT student_id FROM students WHERE roll_number=%s",
            (data["roll_number"].strip(),)
        )

        row = query_one("""
            INSERT INTO complaints
            (student_id, student_name, roll_number, category,
             subject, details, status, complaint_date)
            VALUES (%s,%s,%s,%s,%s,%s,'Pending',CURRENT_DATE)
            RETURNING complaint_id, student_name, roll_number,
                      category, subject, details, status, complaint_date
        """, (
            student["student_id"] if student else None,
            data["student_name"].strip(),
            data["roll_number"].strip(),
            data["category"],
            data["subject"].strip(),
            data["details"].strip()
        ))

        return jsonify(row), 201

    except Exception:
        app.logger.exception("Complaint submit failed")
        return jsonify({
            "message": "Could not submit complaint."
        }), 500


@app.put("/api/complaints/<int:complaint_id>")
def update_complaint(complaint_id):
    data = request.get_json(silent=True) or {}

    try:
        if data.get("status") not in ("Pending", "Resolved"):
            return jsonify({
                "message": "Status must be Pending or Resolved."
            }), 400

        execute("""
            UPDATE complaints
            SET student_name=%s, roll_number=%s, category=%s,
                subject=%s, details=%s, status=%s
            WHERE complaint_id=%s
        """, (
            data["student_name"].strip(),
            data["roll_number"].strip(),
            data["category"].strip(),
            data["subject"].strip(),
            data["details"].strip(),
            data["status"],
            complaint_id
        ))

        return jsonify({"message": "Complaint updated successfully."})

    except Exception:
        return jsonify({"message": "Could not update complaint."}), 400


@app.delete("/api/complaints/<int:complaint_id>")
def delete_complaint(complaint_id):
    try:
        execute(
            "DELETE FROM complaints WHERE complaint_id=%s",
            (complaint_id,)
        )
        return jsonify({"message": "Complaint deleted successfully."})

    except Exception:
        return jsonify({"message": "Could not delete complaint."}), 400


# ==========================================
# STUDENT LOGIN
# ==========================================

@app.route("/api/student-login", methods=["POST"])
def student_login():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({
            "message": "Email and password are required."
        }), 400

    student = query_one("""
        SELECT student_id, full_name, email, password_hash, status
        FROM students
        WHERE LOWER(email) = LOWER(%s)
    """, (email,))

    if not student or not check_password_hash(
        student["password_hash"], password
    ):
        return jsonify({
            "message": "Invalid email or password."
        }), 401

    if student["status"] != "Active":
        return jsonify({
            "message": "Your account is not approved by Admin yet."
        }), 403

    session.clear()
    session["student_id"] = student["student_id"]
    session["student_name"] = student["full_name"]

    return jsonify({"message": "Login successful!"}), 200


@app.route("/student-login")
def student_login_page():
    return send_from_directory(app.root_path, "student-login.html")


@app.route("/student-dashboard")
def student_dashboard_page():
    if "student_id" not in session:
        return redirect("/student-login")

    return send_from_directory(app.root_path, "student-dashboard.html")


# ==========================================
# STUDENT PROFILE
# ==========================================

@app.route("/api/student/me", methods=["GET"])
def get_logged_in_student():
    if "student_id" not in session:
        return jsonify({"message": "Please login first."}), 401

    student = query_one("""
        SELECT student_id, full_name, email, roll_number,
               department, contact_number, guardian_contact,
               gender, address, room_number, status
        FROM students
        WHERE student_id = %s AND status = 'Active'
    """, (session["student_id"],))

    if not student:
        session.clear()
        return jsonify({
            "message": "Student account not found."
        }), 404

    return jsonify(student), 200


# ==========================================
# STUDENT LOGOUT
# ==========================================

@app.route("/api/student-logout", methods=["POST"])
def student_logout():
    session.clear()
    return jsonify({"message": "Logout successful!"}), 200


# ==========================================
# STUDENT ROOM DETAILS
# ==========================================

@app.route("/api/student/room", methods=["GET"])
def get_student_room():
    if "student_id" not in session:
        return jsonify({"message": "Please login first."}), 401

    student = query_one("""
        SELECT room_number
        FROM students
        WHERE student_id = %s AND status = 'Active'
    """, (session["student_id"],))

    if not student:
        return jsonify({"message": "Student not found."}), 404

    if not student["room_number"]:
        return jsonify({
            "message": "No room assigned to you yet."
        }), 404

    room = query_one("""
        SELECT room_id, room_number, capacity, occupied_beds
        FROM rooms
        WHERE room_number = %s
    """, (student["room_number"],))

    if not room:
        return jsonify({
            "message": "Room details not found."
        }), 404

    room["available_beds"] = room["capacity"] - room["occupied_beds"]
    return jsonify(room), 200


# ==========================================
# STUDENT FEES
# ==========================================

@app.get("/api/student/fees")
def get_student_fees():
    if "student_id" not in session:
        return jsonify({"message": "Please login first."}), 401

    student = query_one("""
        SELECT roll_number
        FROM students
        WHERE student_id = %s AND status = 'Active'
    """, (session["student_id"],))

    if not student:
        return jsonify({"message": "Student not found."}), 404

    fees = query_all("""
        SELECT fee_id, amount, fee_month, status, created_at
        FROM fees
        WHERE roll_number = %s
        ORDER BY fee_id DESC
    """, (student["roll_number"],))

    return jsonify(fees), 200


# ==========================================
# STUDENT PAYMENT HISTORY
# ==========================================

@app.get("/api/student/payment-history")
def get_student_payment_history():
    if "student_id" not in session:
        return jsonify({"message": "Please login first."}), 401

    student = query_one("""
        SELECT roll_number
        FROM students
        WHERE student_id = %s AND status = 'Active'
    """, (session["student_id"],))

    if not student:
        return jsonify({"message": "Student not found."}), 404

    payments = query_all("""
        SELECT fee_id, amount, fee_month, status, created_at
        FROM fees
        WHERE roll_number = %s AND status = 'Paid'
        ORDER BY fee_id DESC
    """, (student["roll_number"],))

    return jsonify(payments), 200


# ==========================================
# STUDENT ATTENDANCE
# ==========================================

@app.get("/api/student/attendance")
def get_student_attendance():
    if "student_id" not in session:
        return jsonify({"message": "Please login first."}), 401

    student = query_one("""
        SELECT roll_number
        FROM students
        WHERE student_id = %s AND status = 'Active'
    """, (session["student_id"],))

    if not student:
        return jsonify({"message": "Student not found."}), 404

    records = query_all("""
        SELECT attendance_date, status
        FROM attendance
        WHERE roll_number = %s
        ORDER BY attendance_date DESC
    """, (student["roll_number"],))

    return jsonify(records), 200


# ==========================================
# STUDENT COMPLAINTS
# ==========================================

@app.get("/api/student/complaints")
def get_my_complaints():
    if "student_id" not in session:
        return jsonify({"message": "Please login first."}), 401

    complaints = query_all("""
        SELECT complaint_id, category, subject, details,
               status, complaint_date
        FROM complaints
        WHERE student_id = %s
        ORDER BY complaint_id DESC
    """, (session["student_id"],))

    return jsonify(complaints), 200


@app.post("/api/student/complaints")
def submit_student_complaint():
    if "student_id" not in session:
        return jsonify({"message": "Please login first."}), 401

    data = request.get_json(silent=True) or {}

    category = (data.get("category") or "").strip()
    subject = (data.get("subject") or "").strip()
    details = (data.get("details") or "").strip()

    if not category or not subject or not details:
        return jsonify({
            "message": "Please complete all complaint fields."
        }), 400

    student = query_one("""
        SELECT student_id, full_name, roll_number
        FROM students
        WHERE student_id = %s AND status = 'Active'
    """, (session["student_id"],))

    if not student:
        return jsonify({"message": "Student not found."}), 404

    complaint = query_one("""
        INSERT INTO complaints
            (student_id, student_name, roll_number, category, subject, details)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING complaint_id, category, subject, details,
                  status, complaint_date
    """, (
        student["student_id"],
        student["full_name"],
        student["roll_number"],
        category,
        subject,
        details
    ))

    return jsonify({
        "message": "Complaint submitted successfully!",
        "complaint": complaint
    }), 201


# ==========================================
# RUN PROJECT
# ==========================================

if __name__ == "__main__":
    try:
        init_db()
        print("Database tables are ready.")
    except Exception as error:
        print("Database setup failed:", error)
        print("Open db.py and enter your PostgreSQL password.")

    app.run(debug=True)
