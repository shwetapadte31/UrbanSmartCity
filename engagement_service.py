from datetime import datetime


# =========================================================
# ADD CIVIC POINTS
# =========================================================

def add_civic_points(
    connection,
    user_id,
    points
):

    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO civic_points
            (
                user_id,
                points,
                updated_at
            )
            VALUES
            (%s, %s, CURRENT_TIMESTAMP)

            ON CONFLICT (user_id)

            DO UPDATE SET
                points =
                    civic_points.points
                    +
                    EXCLUDED.points,

                updated_at =
                    CURRENT_TIMESTAMP

            RETURNING points;
        """, (
            user_id,
            points
        ))

        total_points = (
            cursor.fetchone()[0]
        )

        return total_points

    finally:

        cursor.close()


# =========================================================
# CREATE NOTIFICATION
# =========================================================

def create_notification(
    connection,
    user_id,
    title,
    message,
    notification_type="general",
    complaint_id=None
):

    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO notifications
            (
                user_id,
                title,
                message,
                notification_type,
                complaint_id
            )
            VALUES
            (%s, %s, %s, %s, %s);
        """, (
            user_id,
            title,
            message,
            notification_type,
            complaint_id
        ))

    finally:

        cursor.close()


# =========================================================
# AUTOMATIC REWARD CHECK
# =========================================================

def check_and_award_rewards(
    connection,
    user_id
):

    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                COALESCE(points, 0)
            FROM civic_points
            WHERE user_id = %s;
        """, (
            user_id,
        ))

        row = cursor.fetchone()

        if not row:
            return []

        points = row[0]

        cursor.execute("""
            SELECT
                r.id,
                r.name,
                r.points_required
            FROM rewards r
            LEFT JOIN user_rewards ur
                ON ur.reward_id = r.id
                AND ur.user_id = %s
            WHERE
                r.points_required <= %s
                AND ur.id IS NULL
            ORDER BY
                r.points_required ASC;
        """, (
            user_id,
            points
        ))

        rewards = cursor.fetchall()

        awarded = []

        for reward in rewards:

            reward_id = reward[0]
            reward_name = reward[1]

            cursor.execute("""
                INSERT INTO user_rewards
                (
                    user_id,
                    reward_id
                )
                VALUES
                (%s, %s)
                ON CONFLICT
                (
                    user_id,
                    reward_id
                )
                DO NOTHING;
            """, (
                user_id,
                reward_id
            ))

            if cursor.rowcount > 0:

                awarded.append(
                    reward_name
                )

                create_notification(

                    connection,

                    user_id,

                    "New Civic Reward Unlocked",

                    (
                        f"Congratulations! "
                        f"You unlocked the "
                        f"'{reward_name}' reward."
                    ),

                    "reward"

                )

        return awarded

    finally:

        cursor.close()


# =========================================================
# COMPLETE ENGAGEMENT ACTION
# =========================================================

def award_points_and_rewards(
    connection,
    user_id,
    points
):

    total_points = add_civic_points(
        connection,
        user_id,
        points
    )

    rewards = check_and_award_rewards(
        connection,
        user_id
    )

    return {
        "points_added": points,
        "total_points": total_points,
        "rewards": rewards
    }


# =========================================================
# COMPLAINT SUBMISSION
# =========================================================

def handle_complaint_submission(
    connection,
    user_id,
    complaint_id,
    complaint_number
):

    result = award_points_and_rewards(
        connection,
        user_id,
        10
    )

    create_notification(

        connection,

        user_id,

        "Civic Report Submitted",

        (
            f"Your civic report "
            f"{complaint_number} "
            f"has been submitted successfully "
            f"and is now being processed."
        ),

        "complaint_submitted",

        complaint_id

    )

    return result


# =========================================================
# STATUS CHANGE
# =========================================================

def handle_status_change(
    connection,
    user_id,
    complaint_id,
    complaint_number,
    old_status,
    new_status
):

    status_messages = {

        "Assigned":
            "Your complaint has been assigned to the appropriate municipal team.",

        "In Process":
            "Municipal officials have started working on your complaint.",

        "Resolution Submitted":
            "A resolution has been submitted for your complaint. Please verify whether the problem is actually resolved.",

        "Resolved":
            "Your complaint has been marked as resolved."

    }

    message = status_messages.get(

        new_status,

        (
            f"Your complaint status changed "
            f"from {old_status} "
            f"to {new_status}."
        )

    )

    create_notification(

        connection,

        user_id,

        f"Complaint {new_status}",

        (
            f"Complaint {complaint_number}: "
            f"{message}"
        ),

        "status_update",

        complaint_id

    )


# =========================================================
# CITIZEN VERIFICATION
# =========================================================

def handle_citizen_verification(
    connection,
    user_id,
    complaint_id,
    complaint_number,
    decision
):

    if decision == "resolved":

        result = award_points_and_rewards(
            connection,
            user_id,
            20
        )

        create_notification(

            connection,

            user_id,

            "Complaint Verified",

            (
                f"You confirmed that "
                f"complaint {complaint_number} "
                f"has been resolved. "
                f"You earned 20 civic points."
            ),

            "verification",

            complaint_id

        )

        return result

    if decision == "still_exists":

        result = award_points_and_rewards(
            connection,
            user_id,
            5
        )

        create_notification(

            connection,

            user_id,

            "Complaint Reopened",

            (
                f"You reported that "
                f"complaint {complaint_number} "
                f"still exists. "
                f"The municipality will review it again."
            ),

            "verification",

            complaint_id

        )

        return result

    return {
        "points_added": 0,
        "total_points": 0,
        "rewards": []
    }