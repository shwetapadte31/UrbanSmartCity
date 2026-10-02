from flask import Blueprint, jsonify, session

from database import get_db_connection


engagement_bp = Blueprint(
    "engagement",
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
# CIVIC POINTS
# =================================================

@engagement_bp.route(
    "/api/civic-points",
    methods=["GET"]
)
def civic_points():

    login_error = require_login()

    if login_error:
        return login_error

    citizen_error = require_citizen()

    if citizen_error:
        return citizen_error

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                points,
                updated_at
            FROM civic_points
            WHERE user_id = %s
        """, (
            session["user_id"],
        ))

        result = cursor.fetchone()

        points = result[0] if result else 0

        updated_at = None

        if result and result[1]:

            updated_at = result[1].strftime(
                "%d %b %Y, %I:%M %p"
            )

        return jsonify({
            "success": True,
            "points": points,
            "updated_at": updated_at
        })

    except Exception as error:

        print("Civic points error:")
        print(error)

        return jsonify({
            "success": False,
            "message": "Unable to load civic points."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =================================================
# REWARDS
# =================================================

@engagement_bp.route(
    "/api/rewards",
    methods=["GET"]
)
def rewards():

    login_error = require_login()

    if login_error:
        return login_error

    citizen_error = require_citizen()

    if citizen_error:
        return citizen_error

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # Get user's points
        cursor.execute("""
            SELECT points
            FROM civic_points
            WHERE user_id = %s
        """, (
            session["user_id"],
        ))

        points_result = cursor.fetchone()

        current_points = (
            points_result[0]
            if points_result
            else 0
        )

        # Get rewards
        cursor.execute("""
            SELECT
                r.id,
                r.name,
                r.description,
                r.points_required,
                r.icon,
                CASE
                    WHEN ur.id IS NOT NULL
                    THEN TRUE
                    ELSE FALSE
                END AS earned
            FROM rewards r
            LEFT JOIN user_rewards ur
                ON ur.reward_id = r.id
                AND ur.user_id = %s
            ORDER BY r.points_required ASC
        """, (
            session["user_id"],
        ))

        rows = cursor.fetchall()

        reward_list = []

        for row in rows:

            required_points = row[3]

            if required_points > 0:

                progress = min(
                    100,
                    round(
                        (
                            current_points /
                            required_points
                        ) * 100
                    )
                )

            else:

                progress = 100

            reward_list.append({

                "id": row[0],

                "name": row[1],

                "description": row[2],

                "points_required": required_points,

                "icon": row[4],

                "earned": row[5],

                "progress": progress
            })

        return jsonify({
            "success": True,
            "current_points": current_points,
            "rewards": reward_list
        })

    except Exception as error:

        print("Rewards error:")
        print(error)

        return jsonify({
            "success": False,
            "message": "Unable to load rewards."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =================================================
# NOTIFICATIONS
# =================================================

@engagement_bp.route(
    "/api/notifications",
    methods=["GET"]
)
def notifications():

    login_error = require_login()

    if login_error:
        return login_error

    citizen_error = require_citizen()

    if citizen_error:
        return citizen_error

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                title,
                message,
                notification_type,
                complaint_id,
                is_read,
                created_at
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 30
        """, (
            session["user_id"],
        ))

        rows = cursor.fetchall()

        notification_list = []

        for row in rows:

            notification_list.append({

                "id": row[0],

                "title": row[1],

                "message": row[2],

                "notification_type": row[3],

                "complaint_id": row[4],

                "is_read": row[5],

                "created_at":
                    row[6].strftime(
                        "%d %b %Y, %I:%M %p"
                    )
            })

        return jsonify({
            "success": True,
            "notifications": notification_list
        })

    except Exception as error:

        print("Notifications error:")
        print(error)

        return jsonify({
            "success": False,
            "message": "Unable to load notifications."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =================================================
# UNREAD NOTIFICATION COUNT
# =================================================

@engagement_bp.route(
    "/api/notifications/unread-count",
    methods=["GET"]
)
def unread_notification_count():

    login_error = require_login()

    if login_error:
        return login_error

    citizen_error = require_citizen()

    if citizen_error:
        return citizen_error

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM notifications
            WHERE user_id = %s
            AND is_read = FALSE
        """, (
            session["user_id"],
        ))

        count = cursor.fetchone()[0]

        return jsonify({
            "success": True,
            "unread_count": count
        })

    except Exception as error:

        print("Unread notification count error:")
        print(error)

        return jsonify({
            "success": False,
            "message":
                "Unable to load notification count."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =================================================
# MARK NOTIFICATION AS READ
# =================================================

@engagement_bp.route(
    "/api/notifications/<int:notification_id>/read",
    methods=["POST"]
)
def mark_notification_read(notification_id):

    login_error = require_login()

    if login_error:
        return login_error

    citizen_error = require_citizen()

    if citizen_error:
        return citizen_error

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE notifications
            SET is_read = TRUE
            WHERE id = %s
            AND user_id = %s
        """, (
            notification_id,
            session["user_id"]
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message":
                "Notification marked as read."
        })

    except Exception as error:

        if connection:
            connection.rollback()

        print("Mark notification error:")
        print(error)

        return jsonify({
            "success": False,
            "message":
                "Unable to update notification."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =================================================
# MARK ALL NOTIFICATIONS AS READ
# =================================================

@engagement_bp.route(
    "/api/notifications/read-all",
    methods=["POST"]
)
def mark_all_notifications_read():

    login_error = require_login()

    if login_error:
        return login_error

    citizen_error = require_citizen()

    if citizen_error:
        return citizen_error

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE notifications
            SET is_read = TRUE
            WHERE user_id = %s
            AND is_read = FALSE
        """, (
            session["user_id"],
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message":
                "All notifications marked as read."
        })

    except Exception as error:

        if connection:
            connection.rollback()

        print("Mark all notifications error:")
        print(error)

        return jsonify({
            "success": False,
            "message":
                "Unable to update notifications."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()