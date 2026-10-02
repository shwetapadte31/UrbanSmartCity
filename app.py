from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from initialize_database import initialize_database
from database import get_db_connection

from admin_routes import admin_bp
from engagement_routes import engagement_bp
from engagement_service import (
    handle_complaint_submission,
    handle_status_change
)
from intelligence_routes import intelligence_bp
from verification_routes import verification_bp

from ai.processor import process_complaint

import os


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

app.secret_key = "urban-smart-city-secret-key"


# ============================================================
# REGISTER BLUEPRINTS
# ============================================================

app.register_blueprint(verification_bp)
app.register_blueprint(intelligence_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(engagement_bp)


# ============================================================
# PUBLIC PAGES
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/register")
def register():
    return render_template("register.html")


# ============================================================
# CITIZEN DASHBOARD PAGE
# ============================================================

@app.route("/citizen-dashboard")
def citizen_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "citizen":
        return redirect(url_for("login"))

    return render_template(
        "citizen-dashboard.html",
        user_name=session.get("full_name", "Citizen"),
        user_email=session.get("email", "")
    )


# ============================================================
# REPORT PAGE
# ============================================================

@app.route("/report")
def report():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "citizen":
        return redirect(url_for("login"))

    return render_template("report.html")


# ============================================================
# MUNICIPAL DASHBOARD PAGE
# ============================================================

@app.route("/municipal-dashboard")
def municipal_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") not in [
    "municipality_officer",
    "admin"
]:
        return redirect(url_for("login"))

    return render_template(
        "municipal-dashboard.html",
        user_name=session.get(
            "full_name",
            "Municipality Officer"
        ),
        user_email=session.get("email", "")
    )


# ============================================================
# ADMIN DASHBOARD PAGE
# ============================================================

@app.route("/admin-dashboard")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    return render_template(
        "admin_dashboard.html",
        user_name=session.get(
            "full_name",
            "Administrator"
        ),
        user_email=session.get("email", "")
    )


# ============================================================
# REGISTRATION API
# ============================================================

@app.route("/api/register", methods=["POST"])
def register_api():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    account_type = data.get("account_type", "").strip()

    official_email = data.get(
        "official_email",
        ""
    ).strip()

    officer_id = data.get(
        "officer_id",
        ""
    ).strip()

    verification_reason = data.get(
        "verification_reason",
        ""
    ).strip()


    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if not name or not email or not password or not account_type:

        return jsonify({
            "success": False,
            "message": "Please fill all required fields."
        }), 400


    # --------------------------------------------------------
    # PUBLIC ACCOUNT TYPES
    # Admin cannot register publicly.
    # --------------------------------------------------------

    if account_type not in [
        "citizen",
        "municipality_officer"
    ]:

        return jsonify({
            "success": False,
            "message": "Invalid account type."
        }), 400


    # --------------------------------------------------------
    # MUNICIPAL OFFICER VALIDATION
    # --------------------------------------------------------

    if account_type == "municipality_officer":

        if not official_email:

            return jsonify({
                "success": False,
                "message": "Official municipal email is required."
            }), 400

        if not officer_id:

            return jsonify({
                "success": False,
                "message": "Officer ID is required."
            }), 400

        if not verification_reason:

            return jsonify({
                "success": False,
                "message": (
                    "Please provide a reason for "
                    "municipal access."
                )
            }), 400


    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()


        # ----------------------------------------------------
        # CHECK EXISTING EMAIL
        # ----------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM users
            WHERE email = %s
        """, (email,))

        existing_user = cursor.fetchone()


        if existing_user:

            return jsonify({
                "success": False,
                "message": (
                    "An account with this email "
                    "already exists."
                )
            }), 409


        # ----------------------------------------------------
        # PASSWORD HASH
        # ----------------------------------------------------

        password_hash = generate_password_hash(password)


        # ----------------------------------------------------
        # VERIFICATION STATUS
        # ----------------------------------------------------

        if account_type == "citizen":

            verification_status = "verified"
            stored_officer_id = None
            stored_reason = None

        else:

            verification_status = "pending"
            stored_officer_id = officer_id
            stored_reason = verification_reason


        # ----------------------------------------------------
        # INSERT USER
        # ----------------------------------------------------

        cursor.execute("""
    INSERT INTO users (
        name,
        email,
        password_hash,
        role,
        verification_status,
        officer_id,
        verification_reason,
        official_email
    )
    VALUES (
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s
    )
""", (
    name,
    email,
    password_hash,
    account_type,
    verification_status,
    stored_officer_id,
    stored_reason,
    official_email if account_type == "municipality_officer" else None
))

        connection.commit()


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        if account_type == "municipality_officer":

            return jsonify({
                "success": True,
                "message": (
                    "Municipality officer registration "
                    "submitted successfully. Your account "
                    "is pending administrator verification."
                )
            })


        return jsonify({
            "success": True,
            "message": (
                "Citizen account created successfully."
            )
        })


    except Exception as error:

        if connection:
            connection.rollback()

        print("Registration error:")
        print(error)

        return jsonify({
            "success": False,
            "message": "Unable to create account."
        }), 500


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# LOGIN API
# ============================================================

@app.route("/api/login", methods=["POST"])
def api_login():

    data = request.get_json(silent=True) or {}

    email = data.get(
        "email",
        ""
    ).strip().lower()

    password = data.get(
        "password",
        ""
    )


    if not email:

        return jsonify({
            "success": False,
            "message": (
                "Please enter your email address."
            )
        }), 400


    if not password:

        return jsonify({
            "success": False,
            "message": (
                "Please enter your password."
            )
        }), 400


    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()


        # ----------------------------------------------------
        # FIND USER
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                name,
                email,
                password_hash,
                role,
                verification_status
            FROM users
            WHERE LOWER(email) = %s
        """, (email,))

        user = cursor.fetchone()


        if not user:

            return jsonify({
                "success": False,
                "message": "Invalid email or password."
            }), 401


        user_id = user[0]
        full_name = user[1]
        user_email = user[2]
        stored_password = user[3]
        role = user[4]
        verification_status = user[5]


        # ----------------------------------------------------
        # PASSWORD CHECK
        # ----------------------------------------------------

        if not check_password_hash(
            stored_password,
            password
        ):

            return jsonify({
                "success": False,
                "message": "Invalid email or password."
            }), 401


        # ----------------------------------------------------
        # MUNICIPAL OFFICER VERIFICATION
        # ----------------------------------------------------

        if role == "municipality_officer":

            if verification_status != "verified":

                if verification_status == "pending":

                    message = (
                        "Your municipality officer account "
                        "is still waiting for administrator "
                        "approval."
                    )

                elif verification_status == "rejected":

                    message = (
                        "Your municipality officer "
                        "verification request was rejected."
                    )

                else:

                    message = (
                        "Your account is not verified."
                    )


                return jsonify({
                    "success": False,
                    "message": message
                }), 403


        # ----------------------------------------------------
        # CREATE SESSION
        # ----------------------------------------------------

        session["user_id"] = user_id
        session["full_name"] = full_name
        session["email"] = user_email
        session["role"] = role


        # ----------------------------------------------------
        # DASHBOARD
        # ----------------------------------------------------

        if role == "citizen":

            dashboard_url = "/citizen-dashboard"

        elif role == "municipality_officer":

            dashboard_url = "/municipal-dashboard"

        elif role == "admin":

            dashboard_url = "/admin-dashboard"

        else:

            session.clear()

            return jsonify({
                "success": False,
                "message": "Invalid account role."
            }), 403


        print(
            "Login successful:",
            user_email,
            "| Role:",
            role
        )


        return jsonify({
            "success": True,
            "message": "Login successful.",
            "role": role,
            "redirect_url": dashboard_url
        })


    except Exception as error:

        if connection:
            connection.rollback()

        print("Login error:")
        print(error)

        return jsonify({
            "success": False,
            "message": (
                "Unable to process login right now."
            )
        }), 500


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ============================================================
# CITIZEN DASHBOARD API
# ============================================================

@app.route("/api/citizen-dashboard")
def citizen_dashboard_api():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    if session.get("role") != "citizen":

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403


    connection = None
    cursor = None

    try:

        user_id = session["user_id"]

        connection = get_db_connection()
        cursor = connection.cursor()


        # ----------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                COUNT(*) AS total,

                COUNT(*) FILTER (
                    WHERE status <> 'Resolved'
                ) AS active,

                COUNT(*) FILTER (
                    WHERE status = 'Resolved'
                ) AS resolved,

                COUNT(*) FILTER (
                    WHERE created_at::date = CURRENT_DATE
                ) AS today

            FROM complaints

            WHERE user_id = %s
        """, (user_id,))


        statistics = cursor.fetchone()


        # ----------------------------------------------------
        # CITIZEN COMPLAINTS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                c.id,
                c.complaint_number,
                c.problem_type,
                c.description,
                c.urgency,
                c.severity,
                c.priority,
                c.status,
                c.address,
                c.latitude,
                c.longitude,
                c.image_path,
                c.created_at,
                c.updated_at,
                d.name AS department

            FROM complaints c

            LEFT JOIN departments d
                ON c.responsible_department_id = d.id

            WHERE c.user_id = %s

            ORDER BY c.created_at DESC
        """, (user_id,))


        rows = cursor.fetchall()

        complaints = []


        for row in rows:

            complaints.append({

                "id": row[0],

                "complaint_number": row[1],

                "problem_type": row[2],

                "description": row[3],

                "urgency": row[4],

                "severity": row[5],

                "priority": row[6],

                "status": row[7],

                "address": row[8],

                "latitude": (
                    float(row[9])
                    if row[9] is not None
                    else None
                ),

                "longitude": (
                    float(row[10])
                    if row[10] is not None
                    else None
                ),

                "image_path": row[11],

                "created_at": row[12].strftime(
                    "%d %b %Y, %I:%M %p"
                ),

                "updated_at": (
                    row[13].strftime(
                        "%d %b %Y, %I:%M %p"
                    )
                    if row[13]
                    else None
                ),

                "department": (
                    row[14]
                    or "Not Assigned"
                )
            })


        return jsonify({

            "success": True,

            "statistics": {

                "total": statistics[0] or 0,

                "active": statistics[1] or 0,

                "resolved": statistics[2] or 0,

                "today": statistics[3] or 0
            },

            "complaints": complaints
        })


    except Exception as error:

        print("Citizen dashboard error:")
        print(error)

        return jsonify({
            "success": False,
            "message": (
                "Unable to load citizen dashboard."
            )
        }), 500


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# CITIZEN COMPLAINT DETAILS
# ============================================================

@app.route(
    "/api/complaints/<int:complaint_id>/citizen",
    methods=["GET"]
)
def citizen_complaint_details(complaint_id):

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    if session.get("role") != "citizen":

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403


    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()


        cursor.execute("""
            SELECT
                c.id,
                c.complaint_number,
                c.problem_type,
                c.description,
                c.urgency,
                c.severity,
                c.priority,
                c.status,
                c.address,
                c.latitude,
                c.longitude,
                c.created_at,
                c.updated_at,
                c.image_path,
                d.name

            FROM complaints c

            LEFT JOIN departments d
                ON c.responsible_department_id = d.id

            WHERE c.id = %s
            AND c.user_id = %s
        """, (
            complaint_id,
            session["user_id"]
        ))


        row = cursor.fetchone()


        if not row:

            return jsonify({
                "success": False,
                "message": "Complaint not found."
            }), 404


        complaint = {

            "id": row[0],

            "complaint_number": row[1],

            "problem_type": row[2],

            "description": row[3],

            "urgency": row[4],

            "severity": row[5],

            "priority": row[6],

            "status": row[7],

            "address": row[8],

            "latitude": (
                float(row[9])
                if row[9] is not None
                else None
            ),

            "longitude": (
                float(row[10])
                if row[10] is not None
                else None
            ),

            "created_at": row[11].strftime(
                "%d %b %Y, %I:%M %p"
            ),

            "updated_at": (
                row[12].strftime(
                    "%d %b %Y, %I:%M %p"
                )
                if row[12]
                else None
            ),

            "image_path": row[13],

            "department": (
                row[14]
                or "Not Assigned"
            )
        }


        return jsonify({
            "success": True,
            "complaint": complaint
        })


    except Exception as error:

        print("Citizen complaint details error:")
        print(error)

        return jsonify({
            "success": False,
            "message": (
                "Unable to load complaint details."
            )
        }), 500


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# CREATE CIVIC COMPLAINT
# ============================================================

@app.route("/api/complaints", methods=["POST"])
def create_complaint():

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": (
                "Please login before submitting "
                "a complaint."
            )
        }), 401


    # --------------------------------------------------------
    # CITIZEN ONLY
    # --------------------------------------------------------

    if session.get("role") != "citizen":

        return jsonify({
            "success": False,
            "message": (
                "Only citizen accounts can submit "
                "civic reports."
            )
        }), 403


    # --------------------------------------------------------
    # FORM DATA
    # --------------------------------------------------------

    problem_type = request.form.get(
        "problem_type",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    urgency = request.form.get(
        "urgency",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    latitude = request.form.get(
        "latitude"
    )

    longitude = request.form.get(
        "longitude"
    )


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not problem_type:

        return jsonify({
            "success": False,
            "message": (
                "Please select the problem type."
            )
        }), 400


    if not description:

        return jsonify({
            "success": False,
            "message": (
                "Please describe the problem."
            )
        }), 400


    if len(description) < 10:

        return jsonify({
            "success": False,
            "message": (
                "Please provide more details "
                "about the problem."
            )
        }), 400


    if not urgency:

        return jsonify({
            "success": False,
            "message": (
                "Please select the urgency."
            )
        }), 400


    if not location:

        return jsonify({
            "success": False,
            "message": (
                "Please enter the problem location."
            )
        }), 400


    if not latitude or not longitude:

        return jsonify({
            "success": False,
            "message": (
                "Please select the problem "
                "location on the map."
            )
        }), 400


    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    image = request.files.get(
        "problemImage"
    )

    image_path = None

    allowed_extensions = {
        "jpg",
        "jpeg",
        "png",
        "webp"
    }


    if image and image.filename:

        original_filename = image.filename


        if "." not in original_filename:

            return jsonify({
                "success": False,
                "message": "Invalid image file."
            }), 400


        extension = (
            original_filename
            .rsplit(".", 1)[1]
            .lower()
        )


        if extension not in allowed_extensions:

            return jsonify({
                "success": False,
                "message": (
                    "Only JPG, JPEG, PNG and WEBP "
                    "images are allowed."
                )
            }), 400


        image.seek(
            0,
            os.SEEK_END
        )

        file_size = image.tell()

        image.seek(0)


        max_size = 5 * 1024 * 1024


        if file_size > max_size:

            return jsonify({
                "success": False,
                "message": (
                    "Image size must not exceed 5 MB."
                )
            }), 400


    # --------------------------------------------------------
    # AI PROCESSING
    # --------------------------------------------------------

    try:

        ai_result = process_complaint(
            description,
            urgency
        )

    except Exception as error:

        print("AI processing error:")
        print(error)

        return jsonify({
            "success": False,
            "message": (
                "Unable to process the complaint "
                "using AI."
            )
        }), 500


    ai_problem_type = ai_result[
        "problem_type"
    ]

    ai_confidence = ai_result[
        "confidence"
    ]

    severity = ai_result[
        "severity"
    ]

    priority = ai_result[
        "priority"
    ]

    department_name = ai_result[
        "department"
    ]


    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()


        # ----------------------------------------------------
        # FIND DEPARTMENT
        # ----------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM departments
            WHERE name = %s
        """, (
            department_name,
        ))


        department = cursor.fetchone()


        if not department:

            return jsonify({
                "success": False,
                "message": (
                    "AI-assigned department "
                    "was not found."
                )
            }), 500


        department_id = department[0]


        # ----------------------------------------------------
        # INSERT COMPLAINT
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO complaints (
                complaint_number,
                user_id,
                problem_type,
                description,
                urgency,
                severity,
                priority,
                responsible_department_id,
                latitude,
                longitude,
                address,
                image_path,
                status
            )
            VALUES (
                NULL,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'Reported'
            )
            RETURNING id
        """, (
            session["user_id"],
            ai_problem_type,
            description,
            urgency,
            severity,
            priority,
            department_id,
            latitude,
            longitude,
            location,
            image_path
        ))


        saved_id = cursor.fetchone()[0]


        # ----------------------------------------------------
        # GENERATE COMPLAINT NUMBER
        # ----------------------------------------------------

        complaint_number = (
            "USC-" +
            str(saved_id).zfill(6)
        )


        cursor.execute("""
            UPDATE complaints
            SET complaint_number = %s
            WHERE id = %s
        """, (
            complaint_number,
            saved_id
        ))


        # ----------------------------------------------------
        # SAVE IMAGE
        # ----------------------------------------------------

        if image and image.filename:

            upload_folder = os.path.join(
                app.static_folder,
                "uploads"
            )


            os.makedirs(
                upload_folder,
                exist_ok=True
            )


            safe_filename = secure_filename(
                image.filename
            )


            filename = (
                complaint_number +
                "_" +
                safe_filename
            )


            image.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )


            image_path = (
                "uploads/" +
                filename
            )


            cursor.execute("""
                UPDATE complaints
                SET image_path = %s
                WHERE id = %s
            """, (
                image_path,
                saved_id
            ))


        # ----------------------------------------------------
        # COMPLAINT HISTORY
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO complaint_history (
                complaint_id,
                old_status,
                new_status,
                remarks,
                changed_by
            )
            VALUES (
                %s,
                NULL,
                'Reported',
                %s,
                %s
            )
        """, (
            saved_id,
            (
                "Complaint submitted by citizen. "
                "AI classification completed."
            ),
            session["user_id"]
        ))


        # ----------------------------------------------------
        # CIVIC ENGAGEMENT
        # ----------------------------------------------------

        handle_complaint_submission(
            connection,
            session["user_id"],
            saved_id,
            complaint_number
        )


        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        connection.commit()


        return jsonify({

            "success": True,

            "message": (
                "Civic report submitted successfully."
            ),

            "complaint_id": saved_id,

            "complaint_number": complaint_number,

            "status": "Reported",

            "problem_type": ai_problem_type,

            "ai_confidence": ai_confidence,

            "severity": severity,

            "priority": priority,

            "department": department_name,

            "image_path": image_path
        }), 201


    except Exception as error:

        if connection:
            connection.rollback()

        print("Complaint creation error:")
        print(error)

        return jsonify({
            "success": False,
            "message": (
                "Unable to submit the civic "
                "report right now."
            )
        }), 500


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# UPDATE COMPLAINT STATUS
# ============================================================

@app.route(
    "/api/complaints/<int:complaint_id>/status",
    methods=["POST"]
)
def update_complaint_status(complaint_id):

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    if session.get("role") not in [
        "municipality_officer",
        "admin"
    ]:

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403


    data = request.get_json(
        silent=True
    ) or {}

    new_status = data.get(
        "status"
    )


    allowed_statuses = [
        "Reported",
        "Assigned",
        "In Process",
        "Resolution Submitted",
        "Resolved"
    ]


    if new_status not in allowed_statuses:

        return jsonify({
            "success": False,
            "message": "Invalid status."
        }), 400


    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()


        # ----------------------------------------------------
        # GET CURRENT STATUS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                status,
                complaint_number,
                user_id
            FROM complaints
            WHERE id = %s
        """, (
            complaint_id,
        ))


        complaint = cursor.fetchone()


        if not complaint:

            return jsonify({
                "success": False,
                "message": "Complaint not found."
            }), 404


        old_status = complaint[0]
        complaint_number = complaint[1]
        citizen_id = complaint[2]


        if old_status == new_status:

            return jsonify({
                "success": False,
                "message": (
                    "Complaint is already "
                    "in this status."
                )
            }), 400


        # ----------------------------------------------------
        # UPDATE STATUS
        # ----------------------------------------------------

        cursor.execute("""
            UPDATE complaints

            SET
                status = %s,
                updated_at = CURRENT_TIMESTAMP

            WHERE id = %s
        """, (
            new_status,
            complaint_id
        ))


        # ----------------------------------------------------
        # HISTORY
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO complaint_history (
                complaint_id,
                old_status,
                new_status,
                remarks,
                changed_by
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            complaint_id,
            old_status,
            new_status,
            (
                f"Complaint status changed "
                f"from {old_status} "
                f"to {new_status}."
            ),
            session["user_id"]
        ))


        # ----------------------------------------------------
        # CIVIC ENGAGEMENT
        # ----------------------------------------------------

        handle_status_change(
            connection,
            citizen_id,
            complaint_id,
            complaint_number,
            old_status,
            new_status
        )


        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        connection.commit()


        return jsonify({

            "success": True,

            "message": (
                "Complaint status updated successfully."
            ),

            "complaint_number":
                complaint_number,

            "old_status":
                old_status,

            "status":
                new_status
        })


    except Exception as error:

        if connection:
            connection.rollback()

        print("Status update error:")
        print(error)

        return jsonify({
            "success": False,
            "message": (
                "Unable to update complaint status."
            )
        }), 500


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# MUNICIPAL DASHBOARD API
# ============================================================

@app.route("/api/municipal-dashboard")
def municipal_dashboard_api():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    if session.get("role") not in [
        "municipality_officer",
        "admin"
    ]:

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403


    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()


        # ----------------------------------------------------
        # CITY STATISTICS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT

                COUNT(*) AS total,

                COUNT(*) FILTER (
                    WHERE status <> 'Resolved'
                ) AS active,

                COUNT(*) FILTER (
                    WHERE severity = 'Critical'
                ) AS critical,

                COUNT(*) FILTER (
                    WHERE status = 'Reported'
                ) AS reported,

                COUNT(*) FILTER (
                    WHERE status = 'In Process'
                ) AS in_process,

                COUNT(*) FILTER (
                    WHERE status = 'Resolved'
                ) AS resolved,

                COUNT(*) FILTER (
                    WHERE created_at::date = CURRENT_DATE
                ) AS today

            FROM complaints
        """)


        statistics = cursor.fetchone()


        # ----------------------------------------------------
        # COMPLAINTS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT

                c.id,
                c.complaint_number,
                c.problem_type,
                c.description,
                c.urgency,
                c.severity,
                c.priority,
                c.status,
                c.address,
                c.latitude,
                c.longitude,
                c.created_at,
                d.name AS department

            FROM complaints c

            LEFT JOIN departments d
                ON c.responsible_department_id = d.id

            ORDER BY c.created_at DESC
        """)


        rows = cursor.fetchall()

        complaints = []


        for row in rows:

            complaints.append({

                "id": row[0],

                "complaint_number": row[1],

                "problem_type": row[2],

                "description": row[3],

                "urgency": row[4],

                "severity": row[5],

                "priority": row[6],

                "status": row[7],

                "address": row[8],

                "latitude": (
                    float(row[9])
                    if row[9] is not None
                    else None
                ),

                "longitude": (
                    float(row[10])
                    if row[10] is not None
                    else None
                ),

                "created_at": row[11].strftime(
                    "%d %b %Y, %I:%M %p"
                ),

                "department": (
                    row[12]
                    or "Not Assigned"
                )
            })


        # ----------------------------------------------------
        # DEPARTMENT STATISTICS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                d.name,
                COUNT(c.id) AS complaint_count

            FROM departments d

            LEFT JOIN complaints c
                ON c.responsible_department_id = d.id

            GROUP BY d.id, d.name

            ORDER BY complaint_count DESC
        """)


        department_rows = cursor.fetchall()

        departments = []


        for row in department_rows:

            departments.append({

                "name": row[0],

                "count": row[1]
            })


        return jsonify({

            "success": True,

            "statistics": {

                "total":
                    statistics[0] or 0,

                "active":
                    statistics[1] or 0,

                "critical":
                    statistics[2] or 0,

                "reported":
                    statistics[3] or 0,

                "in_process":
                    statistics[4] or 0,

                "resolved":
                    statistics[5] or 0,

                "today":
                    statistics[6] or 0
            },

            "complaints":
                complaints,

            "departments":
                departments
        })


    except Exception as error:

        print("Municipal dashboard error:")
        print(error)

        return jsonify({
            "success": False,
            "message": (
                "Unable to load municipal dashboard."
            )
        }), 500


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# MUNICIPAL / ADMIN COMPLAINT DETAILS
# ============================================================

@app.route(
    "/api/complaints/<int:complaint_id>"
)
def get_complaint_details(complaint_id):

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    if session.get("role") not in [
        "municipality_officer",
        "admin"
    ]:

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403


    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()


        cursor.execute("""
            SELECT

                c.id,
                c.complaint_number,
                c.problem_type,
                c.description,
                c.urgency,
                c.severity,
                c.priority,
                c.status,
                c.address,
                c.latitude,
                c.longitude,
                c.created_at,
                c.updated_at,
                c.image_path,
                d.name AS department

            FROM complaints c

            LEFT JOIN departments d
                ON c.responsible_department_id = d.id

            WHERE c.id = %s
        """, (
            complaint_id,
        ))


        row = cursor.fetchone()


        if not row:

            return jsonify({
                "success": False,
                "message": "Complaint not found."
            }), 404


        complaint = {

            "id": row[0],

            "complaint_number": row[1],

            "problem_type": row[2],

            "description": row[3],

            "urgency": row[4],

            "severity": row[5],

            "priority": row[6],

            "status": row[7],

            "address": row[8],

            "latitude": (
                float(row[9])
                if row[9] is not None
                else None
            ),

            "longitude": (
                float(row[10])
                if row[10] is not None
                else None
            ),

            "created_at": row[11].strftime(
                "%d %b %Y, %I:%M %p"
            ),

            "updated_at": (
                row[12].strftime(
                    "%d %b %Y, %I:%M %p"
                )
                if row[12]
                else None
            ),

            "image_path": row[13],

            "department": (
                row[14]
                or "Not Assigned"
            )
        }


        return jsonify({
            "success": True,
            "complaint": complaint
        })


    except Exception as error:

        print("Complaint details error:")
        print(error)

        return jsonify({
            "success": False,
            "message": (
                "Unable to load complaint details."
            )
        }), 500


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

# ============================================================
# COMPLAINT HISTORY API
# ============================================================

@app.route(
    "/api/complaints/<int:complaint_id>/history",
    methods=["GET"]
)
def get_complaint_history(complaint_id):

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    if session.get("role") not in [
        "municipality_officer",
        "admin"
    ]:

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403


    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()


        cursor.execute("""
            SELECT
                ch.id,
                ch.old_status,
                ch.new_status,
                ch.remarks,
                ch.changed_by,
                ch.created_at,
                u.name

            FROM complaint_history ch

            LEFT JOIN users u
                ON ch.changed_by = u.id

            WHERE ch.complaint_id = %s

            ORDER BY ch.created_at ASC
        """, (
            complaint_id,
        ))


        rows = cursor.fetchall()

        history = []


        for row in rows:

            history.append({

                "id": row[0],

                "old_status": (
                    row[1]
                    or None
                ),

                "new_status": row[2],

                "remarks": (
                    row[3]
                    or ""
                ),

                "changed_by": row[4],

                "created_at": row[5].strftime(
                    "%d %b %Y, %I:%M %p"
                ),

                "user_name": (
                    row[6]
                    or "System"
                )
            })


        return jsonify({

            "success": True,

            "history": history
        })


    except Exception as error:

        print("Complaint history error:")
        print(error)

        return jsonify({
            "success": False,
            "message": (
                "Unable to load complaint history."
            )
        }), 500


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()
# ============================================================
# CITIZEN COMPLAINT HISTORY
# ============================================================

@app.route(
    "/api/complaints/<int:complaint_id>/citizen-history",
    methods=["GET"]
)
def citizen_complaint_history(complaint_id):

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    if session.get("role") != "citizen":

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403


    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()


        # ----------------------------------------------------
        # FIRST VERIFY OWNERSHIP
        # ----------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM complaints
            WHERE id = %s
            AND user_id = %s
        """, (
            complaint_id,
            session["user_id"]
        ))


        complaint = cursor.fetchone()


        if not complaint:

            return jsonify({
                "success": False,
                "message": "Complaint not found."
            }), 404


        # ----------------------------------------------------
        # LOAD HISTORY
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                ch.id,
                ch.old_status,
                ch.new_status,
                ch.remarks,
                ch.created_at,
                u.name

            FROM complaint_history ch

            LEFT JOIN users u
                ON ch.changed_by = u.id

            WHERE ch.complaint_id = %s

            ORDER BY ch.created_at ASC
        """, (
            complaint_id,
        ))


        rows = cursor.fetchall()

        history = []


        for row in rows:

            history.append({

                "id": row[0],

                "old_status": (
                    row[1]
                    or None
                ),

                "new_status": row[2],

                "remarks": (
                    row[3]
                    or ""
                ),

                "created_at": row[4].strftime(
                    "%d %b %Y, %I:%M %p"
                ),

                "changed_by": (
                    row[5]
                    or "System"
                )
            })


        return jsonify({

            "success": True,

            "history": history
        })


    except Exception as error:

        print("Citizen complaint history error:")
        print(error)

        return jsonify({
            "success": False,
            "message": (
                "Unable to load complaint history."
            )
        }), 500


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()            



# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({
        "success": False,
        "message": "Page not found."
    }), 404


@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({
        "success": False,
        "message": "Internal server error."
    }), 500


# ============================================================
# RUN APPLICATION
# ============================================================
if __name__ == "__main__":

    try:
        initialize_database()
    except Exception as error:
        print("Database initialization error:")
        print(error)

    app.run(debug=True)