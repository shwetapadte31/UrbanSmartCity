from flask import Blueprint, request, jsonify, session

from database import get_db_connection
from engagement_service import handle_citizen_verification


verification_bp = Blueprint(
    "verification",
    __name__
)


# =================================================
# LOGIN CHECK
# =================================================

def require_login():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    return None


# =================================================
# CITIZEN CHECK
# =================================================

def require_citizen():

    if session.get("role") != "citizen":

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    return None


# =================================================
# COMPLAINT HISTORY
# =================================================

@verification_bp.route(
    "/api/complaints/<int:complaint_id>/history",
    methods=["GET"]
)
def complaint_history(complaint_id):

    login_error = require_login()

    if login_error:
        return login_error

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # -------------------------------------------------
        # Get complaint
        # -------------------------------------------------

        cursor.execute("""
            SELECT
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

        citizen_id = complaint[0]

        # -------------------------------------------------
        # Citizen can only see own history
        # -------------------------------------------------

        if session.get("role") == "citizen":

            if session.get("user_id") != citizen_id:

                return jsonify({
                    "success": False,
                    "message": "Access denied."
                }), 403

        # -------------------------------------------------
        # Get history
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                old_status,
                new_status,
                remarks,
                changed_by,
                created_at
            FROM complaint_history
            WHERE complaint_id = %s
            ORDER BY created_at ASC
        """, (
            complaint_id,
        ))

        rows = cursor.fetchall()

        history = []

        for row in rows:

            history.append({
                "id": row[0],
                "old_status": row[1],
                "new_status": row[2],
                "remarks": row[3],
                "changed_by": row[4],
                "created_at":
                    row[5].strftime(
                        "%d %b %Y, %I:%M %p"
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
            "message":
                "Unable to load complaint history."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =================================================
# CITIZEN VERIFICATION
# =================================================

@verification_bp.route(
    "/api/complaints/<int:complaint_id>/verify",
    methods=["POST"]
)
def verify_complaint(complaint_id):

    login_error = require_login()

    if login_error:
        return login_error

    citizen_error = require_citizen()

    if citizen_error:
        return citizen_error

    data = request.get_json(silent=True) or {}

    decision = data.get("decision")
    remarks = data.get("remarks", "").strip()

    allowed_decisions = [
        "resolved",
        "still_exists"
    ]

    if decision not in allowed_decisions:

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

        # -------------------------------------------------
        # Get complaint
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                user_id,
                complaint_number,
                status
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

        citizen_id = complaint[0]
        complaint_number = complaint[1]
        current_status = complaint[2]

        # -------------------------------------------------
        # Ownership check
        # -------------------------------------------------

        if citizen_id != session.get("user_id"):

            return jsonify({
                "success": False,
                "message":
                    "You can only verify your own complaint."
            }), 403

        # -------------------------------------------------
        # Verification allowed only after resolution
        # -------------------------------------------------

        if current_status != "Resolution Submitted":

            return jsonify({
                "success": False,
                "message":
                    "Complaint can be verified only after "
                    "resolution has been submitted."
            }), 400

        # -------------------------------------------------
        # Save verification
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO complaint_verification (
                complaint_id,
                citizen_id,
                decision,
                remarks
            )
            VALUES (
                %s,
                %s,
                %s,
                %s
            )
        """, (
            complaint_id,
            citizen_id,
            decision,
            remarks
        ))

        # -------------------------------------------------
        # Determine new complaint status
        # -------------------------------------------------

        if decision == "resolved":

            new_status = "Resolved"

            history_message = (
                "Citizen verified that the problem "
                "has been resolved."
            )

        else:

            new_status = "In Process"

            history_message = (
                "Citizen reported that the problem "
                "still exists."
            )

        # -------------------------------------------------
        # Update complaint
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Add history
        # -------------------------------------------------

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
            current_status,
            new_status,
            history_message,
            session["user_id"]
        ))

        # -------------------------------------------------
        # Civic Engagement
        # -------------------------------------------------

        handle_citizen_verification(
            connection,
            citizen_id,
            complaint_id,
            complaint_number,
            decision
        )

        # -------------------------------------------------
        # Commit
        # -------------------------------------------------

        connection.commit()

        return jsonify({
            "success": True,
            "message":
                (
                    "Complaint marked as resolved."
                    if decision == "resolved"
                    else
                    "Complaint has been sent back to in-process."
                ),
            "status": new_status,
            "decision": decision
        })

    except Exception as error:

        if connection:
            connection.rollback()

        print("Complaint verification error:")
        print(error)

        return jsonify({
            "success": False,
            "message":
                "Unable to process complaint verification."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()