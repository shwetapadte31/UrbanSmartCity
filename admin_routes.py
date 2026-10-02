from flask import Blueprint, jsonify, request, session

from database import get_db_connection


admin_bp = Blueprint(
    "admin",
    __name__
)


# ============================================================
# ADMIN ACCESS CHECK
# ============================================================

def check_admin_access():

    if "user_id" not in session:

        return (
            False,
            jsonify({
                "success": False,
                "message": "Please login first."
            }),
            401
        )

    if session.get("role") != "admin":

        return (
            False,
            jsonify({
                "success": False,
                "message": "Admin access required."
            }),
            403
        )

    return True, None, None


# ============================================================
# ADMIN ACTIVITY LOGGER
# ============================================================

def log_admin_activity(
    cursor,
    admin_id,
    action,
    target_user_id=None,
    details=None
):

    cursor.execute("""
        INSERT INTO admin_activity_log
        (
            admin_id,
            action,
            target_user_id,
            details
        )
        VALUES (%s, %s, %s, %s);
    """, (
        admin_id,
        action,
        target_user_id,
        details
    ))


# ============================================================
# ADMIN PLATFORM OVERVIEW
# ============================================================

@admin_bp.route(
    "/api/admin/overview",
    methods=["GET"]
)
def admin_overview():

    allowed, response, status = check_admin_access()

    if not allowed:
        return response, status

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # ----------------------------------------------------
        # USER COUNTS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                COUNT(*) AS total_users,

                COUNT(*) FILTER (
                    WHERE role = 'citizen'
                ) AS citizens,

                COUNT(*) FILTER (
                    WHERE role = 'municipality_officer'
                ) AS officers,

                COUNT(*) FILTER (
                    WHERE role = 'admin'
                ) AS admins,

                COUNT(*) FILTER (
                    WHERE role = 'municipality_officer'
                    AND verification_status = 'pending'
                ) AS pending_officers,

                COUNT(*) FILTER (
                    WHERE role = 'municipality_officer'
                    AND verification_status = 'verified'
                ) AS verified_officers

            FROM users;
        """)

        user_row = cursor.fetchone()

        # ----------------------------------------------------
        # COMPLAINT COUNTS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                COUNT(*) AS total,

                COUNT(*) FILTER (
                    WHERE status != 'Resolved'
                ) AS active,

                COUNT(*) FILTER (
                    WHERE status = 'Resolved'
                ) AS resolved,

                COUNT(*) FILTER (
                    WHERE severity = 'Critical'
                ) AS critical,

                COUNT(*) FILTER (
                    WHERE created_at::date = CURRENT_DATE
                ) AS today

            FROM complaints;
        """)

        complaint_row = cursor.fetchone()

        # ----------------------------------------------------
        # RECENT USERS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                name,
                email,
                role,
                verification_status,
                officer_id,
                created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 10;
        """)

        user_rows = cursor.fetchall()

        recent_users = []

        for row in user_rows:

            recent_users.append({

                "id": row[0],

                "name": row[1],

                "email": row[2],

                "role": row[3],

                "verification_status":
                    row[4],

                "officer_id":
                    row[5],

                "created_at":
                    row[6].strftime(
                        "%d %b %Y, %I:%M %p"
                    )
            })

        # ----------------------------------------------------
        # PENDING OFFICERS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                name,
                email,
                officer_id,
                verification_reason,
                verification_status,
                created_at
            FROM users
            WHERE role = 'municipality_officer'
              AND verification_status = 'pending'
            ORDER BY created_at ASC;
        """)

        officer_rows = cursor.fetchall()

        pending_officers = []

        for row in officer_rows:

            pending_officers.append({

                "id": row[0],

                "name": row[1],

                "email": row[2],

                "officer_id": row[3],

                "verification_reason":
                    row[4],

                "verification_status":
                    row[5],

                "created_at":
                    row[6].strftime(
                        "%d %b %Y, %I:%M %p"
                    )
            })

        return jsonify({

            "success": True,

            "users": {

                "total":
                    user_row[0] or 0,

                "citizens":
                    user_row[1] or 0,

                "officers":
                    user_row[2] or 0,

                "admins":
                    user_row[3] or 0,

                "pending_officers":
                    user_row[4] or 0,

                "verified_officers":
                    user_row[5] or 0
            },

            "complaints": {

                "total":
                    complaint_row[0] or 0,

                "active":
                    complaint_row[1] or 0,

                "resolved":
                    complaint_row[2] or 0,

                "critical":
                    complaint_row[3] or 0,

                "today":
                    complaint_row[4] or 0
            },

            "recent_users":
                recent_users,

            "pending_officers":
                pending_officers

        })

    except Exception as error:

        print(
            "Admin overview error:"
        )

        print(error)

        return jsonify({

            "success": False,

            "message":
                "Unable to load admin overview."

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# OFFICER VERIFICATION
# ============================================================

@admin_bp.route(
    "/api/admin/officers/<int:user_id>/verification",
    methods=["POST"]
)
def verify_officer(user_id):

    allowed, response, status = check_admin_access()

    if not allowed:
        return response, status

    data = request.get_json()

    if not data:

        return jsonify({

            "success": False,

            "message":
                "Invalid verification request."

        }), 400

    decision = str(
        data.get(
            "decision",
            ""
        )
    ).strip().lower()

    remarks = str(
        data.get(
            "remarks",
            ""
        )
    ).strip()

    if decision not in [
        "approve",
        "reject"
    ]:

        return jsonify({

            "success": False,

            "message":
                "Invalid verification decision."

        }), 400

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # ----------------------------------------------------
        # CHECK OFFICER
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                name,
                email,
                role,
                verification_status
            FROM users
            WHERE id = %s;
        """, (
            user_id,
        ))

        officer = cursor.fetchone()

        if not officer:

            return jsonify({

                "success": False,

                "message":
                    "User not found."

            }), 404

        if officer[3] != "municipality_officer":

            return jsonify({

                "success": False,

                "message":
                    "Selected user is not a municipality officer."

            }), 400

        # ----------------------------------------------------
        # NEW STATUS
        # ----------------------------------------------------

        if decision == "approve":

            new_status = "verified"

            action = "Officer approved"

            details = (
                f"Municipality officer "
                f"{officer[1]} was approved."
            )

        else:

            new_status = "rejected"

            action = "Officer rejected"

            details = (
                f"Municipality officer "
                f"{officer[1]} was rejected."
            )

        if remarks:

            details += (
                f" Admin remarks: {remarks}"
            )

        # ----------------------------------------------------
        # UPDATE USER
        # ----------------------------------------------------

        cursor.execute("""
            UPDATE users
            SET verification_status = %s
            WHERE id = %s;
        """, (
            new_status,
            user_id
        ))

        # ----------------------------------------------------
        # LOG ACTIVITY
        # ----------------------------------------------------

        log_admin_activity(
            cursor,
            session.get("user_id"),
            action,
            user_id,
            details
        )

        connection.commit()

        return jsonify({

            "success": True,

            "message":
                (
                    "Officer approved successfully."
                    if decision == "approve"
                    else
                    "Officer rejected successfully."
                ),

            "status":
                new_status
        })

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "Officer verification error:"
        )

        print(error)

        return jsonify({

            "success": False,

            "message":
                "Unable to update officer verification."

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# USER LIST
# ============================================================

@admin_bp.route(
    "/api/admin/users",
    methods=["GET"]
)
def get_admin_users():

    allowed, response, status = check_admin_access()

    if not allowed:
        return response, status

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        role = request.args.get(
            "role",
            "all"
        )

        search = request.args.get(
            "search",
            ""
        ).strip()

        if role not in [
            "all",
            "citizen",
            "municipality_officer",
            "admin"
        ]:

            role = "all"

        query = """
            SELECT
                id,
                name,
                email,
                role,
                verification_status,
                officer_id,
                created_at
            FROM users
            WHERE 1 = 1
        """

        params = []

        if role != "all":

            query += """
                AND role = %s
            """

            params.append(
                role
            )

        if search:

            query += """
                AND (
                    LOWER(name) LIKE LOWER(%s)
                    OR LOWER(email) LIKE LOWER(%s)
                    OR LOWER(
                        COALESCE(
                            officer_id,
                            ''
                        )
                    ) LIKE LOWER(%s)
                )
            """

            search_value = (
                "%"
                +
                search
                +
                "%"
            )

            params.extend([
                search_value,
                search_value,
                search_value
            ])

        query += """
            ORDER BY created_at DESC
            LIMIT 200;
        """

        cursor.execute(
            query,
            tuple(params)
        )

        rows = cursor.fetchall()

        users = []

        for row in rows:

            users.append({

                "id":
                    row[0],

                "name":
                    row[1],

                "email":
                    row[2],

                "role":
                    row[3],

                "verification_status":
                    row[4],

                "officer_id":
                    row[5],

                "created_at":
                    row[6].strftime(
                        "%d %b %Y, %I:%M %p"
                    )
            })

        return jsonify({

            "success": True,

            "users":
                users,

            "count":
                len(users)

        })

    except Exception as error:

        print(
            "Admin users error:"
        )

        print(error)

        return jsonify({

            "success": False,

            "message":
                "Unable to load users."

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# ADMIN ACTIVITY LOG
# ============================================================

@admin_bp.route(
    "/api/admin/activity",
    methods=["GET"]
)
def get_admin_activity():

    allowed, response, status = check_admin_access()

    if not allowed:
        return response, status

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                a.id,
                a.action,
                a.details,
                a.created_at,
                u.name,
                t.name
            FROM admin_activity_log a

            LEFT JOIN users u
                ON a.admin_id = u.id

            LEFT JOIN users t
                ON a.target_user_id = t.id

            ORDER BY a.created_at DESC

            LIMIT 50;
        """)

        rows = cursor.fetchall()

        activities = []

        for row in rows:

            activities.append({

                "id":
                    row[0],

                "action":
                    row[1],

                "details":
                    row[2],

                "created_at":
                    row[3].strftime(
                        "%d %b %Y, %I:%M %p"
                    ),

                "admin_name":
                    row[4] or "System",

                "target_name":
                    row[5] or "—"
            })

        return jsonify({

            "success": True,

            "activities":
                activities

        })

    except Exception as error:

        print(
            "Admin activity error:"
        )

        print(error)

        return jsonify({

            "success": False,

            "message":
                "Unable to load admin activity."

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# ADMIN COMPLAINT OVERVIEW
# ============================================================

@admin_bp.route(
    "/api/admin/complaints",
    methods=["GET"]
)
def admin_complaints():

    allowed, response, status = check_admin_access()

    if not allowed:
        return response, status

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
                c.severity,
                c.priority,
                c.status,
                c.address,
                c.created_at,
                d.name,
                u.name
            FROM complaints c

            LEFT JOIN departments d
                ON c.responsible_department_id = d.id

            LEFT JOIN users u
                ON c.user_id = u.id

            ORDER BY c.created_at DESC

            LIMIT 100;
        """)

        rows = cursor.fetchall()

        complaints = []

        for row in rows:

            complaints.append({

                "id":
                    row[0],

                "complaint_number":
                    row[1],

                "problem_type":
                    row[2],

                "severity":
                    row[3],

                "priority":
                    row[4],

                "status":
                    row[5],

                "address":
                    row[6],

                "created_at":
                    row[7].strftime(
                        "%d %b %Y, %I:%M %p"
                    ),

                "department":
                    row[8] or "Not Assigned",

                "citizen":
                    row[9] or "Unknown"
            })

        return jsonify({

            "success":
                True,

            "complaints":
                complaints

        })

    except Exception as error:

        print(
            "Admin complaints error:"
        )

        print(error)

        return jsonify({

            "success":
                False,

            "message":
                "Unable to load complaints."

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()