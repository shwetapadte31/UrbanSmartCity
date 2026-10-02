from database import get_db_connection
from datetime import timedelta
import math


# ============================================================
# COMMON HELPERS
# ============================================================

def safe_float(value):

    try:
        return float(value)
    except:
        return None


def calculate_distance(lat1, lon1, lat2, lon2):

    if None in [lat1, lon1, lat2, lon2]:
        return None

    radius = 6371

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))

    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radius * c


# ============================================================
# CITY MAP DATA
# ============================================================

def get_city_map_data():

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
                COALESCE(
                    d.name,
                    'Not Assigned'
                ) AS department
            FROM complaints c

            LEFT JOIN departments d
                ON c.responsible_department_id = d.id

            WHERE
                c.latitude IS NOT NULL
                AND c.longitude IS NOT NULL

            ORDER BY c.created_at DESC;
        """)

        rows = cursor.fetchall()

        complaints = []

        for row in rows:

            complaints.append({

                "id": row[0],

                "complaint_number":
                    row[1],

                "problem_type":
                    row[2],

                "description":
                    row[3],

                "urgency":
                    row[4],

                "severity":
                    row[5],

                "priority":
                    row[6],

                "status":
                    row[7],

                "address":
                    row[8] or "Location unavailable",

                "latitude":
                    safe_float(row[9]),

                "longitude":
                    safe_float(row[10]),

                "created_at":
                    row[11].strftime(
                        "%d %b %Y, %I:%M %p"
                    ),

                "department":
                    row[12]

            })

        return complaints

    except Exception as error:

        print("City map data error:")
        print(error)

        return []

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# DUPLICATE COMPLAINT DETECTION
# ============================================================

def detect_duplicate_complaints(complaint_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                problem_type,
                description,
                latitude,
                longitude,
                created_at
            FROM complaints
            WHERE id = %s;
        """, (complaint_id,))

        complaint = cursor.fetchone()

        if not complaint:
            return []

        current_type = complaint[1]
        current_description = complaint[2] or ""

        current_latitude = safe_float(
            complaint[3]
        )

        current_longitude = safe_float(
            complaint[4]
        )

        current_created = complaint[5]

        cursor.execute("""
            SELECT
                id,
                complaint_number,
                problem_type,
                description,
                latitude,
                longitude,
                status,
                created_at
            FROM complaints

            WHERE id != %s

            AND created_at >= %s

            ORDER BY created_at DESC;
        """, (
            complaint_id,
            current_created - timedelta(days=30)
        ))

        rows = cursor.fetchall()

        duplicates = []

        current_words = set(
            word.lower()
            for word in current_description.split()
            if len(word) > 2
        )

        for row in rows:

            other_id = row[0]

            other_type = row[2]

            other_description = row[3] or ""

            other_latitude = safe_float(
                row[4]
            )

            other_longitude = safe_float(
                row[5]
            )

            score = 0

            if current_type == other_type:
                score += 40

            other_words = set(
                word.lower()
                for word in other_description.split()
                if len(word) > 2
            )

            if current_words and other_words:

                common_words = (
                    current_words.intersection(
                        other_words
                    )
                )

                similarity = (
                    len(common_words)
                    /
                    max(
                        len(
                            current_words.union(
                                other_words
                            )
                        ),
                        1
                    )
                )

                score += similarity * 40

            distance = calculate_distance(
                current_latitude,
                current_longitude,
                other_latitude,
                other_longitude
            )

            if distance is not None:

                if distance <= 0.1:
                    score += 20

                elif distance <= 0.5:
                    score += 10

            if score >= 60:

                duplicates.append({

                    "complaint_id":
                        other_id,

                    "complaint_number":
                        row[1],

                    "problem_type":
                        other_type,

                    "description":
                        other_description,

                    "status":
                        row[6],

                    "created_at":
                        row[7].strftime(
                            "%d %b %Y, %I:%M %p"
                        ),

                    "similarity_score":
                        round(score, 2)

                })

        duplicates.sort(
            key=lambda item:
                item["similarity_score"],
            reverse=True
        )

        return duplicates[:5]

    except Exception as error:

        print(
            "Duplicate detection error:"
        )

        print(error)

        return []

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# RECURRING PROBLEMS
# ============================================================

def detect_recurring_problems():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                problem_type,
                address,
                latitude,
                longitude,
                COUNT(*) AS complaint_count
            FROM complaints

            WHERE created_at >=
                CURRENT_TIMESTAMP - INTERVAL '90 days'

            GROUP BY
                problem_type,
                address,
                latitude,
                longitude

            HAVING COUNT(*) >= 2

            ORDER BY
                complaint_count DESC;
        """)

        rows = cursor.fetchall()

        recurring = []

        for row in rows:

            recurring.append({

                "problem_type":
                    row[0],

                "address":
                    row[1] or
                    "Location unavailable",

                "latitude":
                    safe_float(row[2]),

                "longitude":
                    safe_float(row[3]),

                "complaint_count":
                    row[4]

            })

        return recurring

    except Exception as error:

        print(
            "Recurring problem error:"
        )

        print(error)

        return []

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# TREND ANALYTICS
# ============================================================

def get_complaint_trends():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                DATE(created_at),
                COUNT(*)

            FROM complaints

            WHERE created_at >=
                CURRENT_TIMESTAMP - INTERVAL '30 days'

            GROUP BY DATE(created_at)

            ORDER BY DATE(created_at);
        """)

        daily_rows = cursor.fetchall()

        daily = []

        for row in daily_rows:

            daily.append({

                "date":
                    row[0].strftime("%d %b"),

                "count":
                    row[1]

            })

        cursor.execute("""
            SELECT
                problem_type,
                COUNT(*)

            FROM complaints

            WHERE created_at >=
                CURRENT_TIMESTAMP - INTERVAL '30 days'

            GROUP BY problem_type

            ORDER BY COUNT(*) DESC;
        """)

        category_rows = cursor.fetchall()

        categories = []

        for row in category_rows:

            categories.append({

                "problem_type":
                    row[0],

                "count":
                    row[1]

            })

        return {

            "daily":
                daily,

            "categories":
                categories

        }

    except Exception as error:

        print(
            "Trend analytics error:"
        )

        print(error)

        return {

            "daily": [],

            "categories": []

        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# RISK PREDICTION
# ============================================================

def calculate_risk_predictions():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                address,
                problem_type,
                COUNT(*) AS complaint_count,
                latitude,
                longitude

            FROM complaints

            WHERE created_at >=
                CURRENT_TIMESTAMP - INTERVAL '90 days'

            GROUP BY
                address,
                problem_type,
                latitude,
                longitude

            HAVING COUNT(*) >= 2

            ORDER BY
                complaint_count DESC;
        """)

        rows = cursor.fetchall()

        predictions = []

        for row in rows:

            count = row[2]

            if count >= 8:

                risk = "High"
                risk_score = 90

            elif count >= 5:

                risk = "Medium"
                risk_score = 65

            else:

                risk = "Low"
                risk_score = 40

            predictions.append({

                "address":
                    row[0] or
                    "Location unavailable",

                "problem_type":
                    row[1],

                "complaint_count":
                    count,

                "latitude":
                    safe_float(row[3]),

                "longitude":
                    safe_float(row[4]),

                "risk_level":
                    risk,

                "risk_score":
                    risk_score

            })

        return predictions

    except Exception as error:

        print(
            "Risk prediction error:"
        )

        print(error)

        return []

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# URBAN IMPROVEMENT SCORE
# ============================================================

def calculate_urban_improvement_score():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT

                COUNT(*),

                COUNT(*) FILTER (
                    WHERE status = 'Resolved'
                ),

                COUNT(*) FILTER (
                    WHERE severity = 'Critical'
                ),

                COUNT(*) FILTER (
                    WHERE
                        priority = 'High'
                        OR priority = 'Critical'
                )

            FROM complaints;
        """)

        result = cursor.fetchone()

        total = result[0] or 0

        resolved = result[1] or 0

        critical = result[2] or 0

        high_priority = result[3] or 0

        if total == 0:

            return {

                "score": 100,

                "resolution_score": 100,

                "safety_score": 100,

                "priority_score": 100

            }

        resolution_score = (
            resolved / total
        ) * 100

        critical_penalty = min(
            critical * 3,
            30
        )

        priority_penalty = min(
            high_priority * 1.5,
            25
        )

        safety_score = max(
            0,
            100 - critical_penalty
        )

        priority_score = max(
            0,
            100 - priority_penalty
        )

        final_score = (

            resolution_score * 0.5

            +

            safety_score * 0.3

            +

            priority_score * 0.2

        )

        return {

            "score":
                round(final_score, 2),

            "resolution_score":
                round(resolution_score, 2),

            "safety_score":
                round(safety_score, 2),

            "priority_score":
                round(priority_score, 2)

        }

    except Exception as error:

        print(
            "Urban improvement score error:"
        )

        print(error)

        return {

            "score": 0,

            "resolution_score": 0,

            "safety_score": 0,

            "priority_score": 0

        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# RECOMMENDATIONS
# ============================================================

def get_recommendation(problem_type):

    recommendations = {

        "Pothole": {

            "cause":
                "Road surface deterioration, heavy traffic or water seepage.",

            "action":
                "Inspect the affected road section and schedule pothole repair."

        },

        "Road Damage": {

            "cause":
                "Road wear, construction activity or repeated heavy traffic.",

            "action":
                "Inspect the road and prioritize resurfacing or structural repair."

        },

        "Garbage": {

            "cause":
                "Missed collection, insufficient bins or improper waste disposal.",

            "action":
                "Schedule waste collection and inspect the nearby collection point."

        },

        "Water Leakage": {

            "cause":
                "Damaged pipeline, loose connection or underground pipe failure.",

            "action":
                "Inspect the water network and repair the affected pipeline."

        },

        "Drainage": {

            "cause":
                "Blocked drain, accumulated waste or insufficient drainage capacity.",

            "action":
                "Inspect and clean the drainage network."

        },

        "Waterlogging": {

            "cause":
                "Blocked drainage, heavy rainfall or inadequate storm-water capacity.",

            "action":
                "Clear drainage channels and inspect the storm-water network."

        },

        "Streetlight": {

            "cause":
                "Lamp failure, electrical fault or damaged lighting equipment.",

            "action":
                "Inspect the streetlight connection and replace faulty equipment."

        },

        "Traffic": {

            "cause":
                "Traffic congestion, road obstruction or inadequate traffic management.",

            "action":
                "Inspect the location and evaluate traffic-control measures."

        },

        "Infrastructure": {

            "cause":
                "Damage or deterioration of public infrastructure.",

            "action":
                "Conduct a site inspection and assign the appropriate maintenance team."

        }

    }

    return recommendations.get(

        problem_type,

        {

            "cause":
                "The available complaint information is insufficient to determine the exact cause.",

            "action":
                "Conduct a municipal inspection and assign the appropriate department."

        }

    )


# ============================================================
# DEPARTMENT PERFORMANCE
# ============================================================

def get_department_performance():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT

                COALESCE(
                    d.name,
                    'Unassigned'
                ),

                COUNT(c.id),

                COUNT(c.id) FILTER (
                    WHERE c.status = 'Resolved'
                ),

                COUNT(c.id) FILTER (
                    WHERE c.status != 'Resolved'
                )

            FROM complaints c

            LEFT JOIN departments d
                ON c.responsible_department_id = d.id

            GROUP BY d.name

            ORDER BY COUNT(c.id) DESC;
        """)

        rows = cursor.fetchall()

        performance = []

        for row in rows:

            total = row[1] or 0

            resolved = row[2] or 0

            resolution_rate = 0

            if total > 0:

                resolution_rate = (
                    resolved / total
                ) * 100

            performance.append({

                "department":
                    row[0],

                "total":
                    total,

                "resolved":
                    resolved,

                "pending":
                    row[3] or 0,

                "resolution_rate":
                    round(
                        resolution_rate,
                        2
                    )

            })

        return performance

    except Exception as error:

        print(
            "Department performance error:"
        )

        print(error)

        return []

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# CITY STATUS
# ============================================================

def get_city_status():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT

                COUNT(*),

                COUNT(*) FILTER (
                    WHERE status != 'Resolved'
                ),

                COUNT(*) FILTER (
                    WHERE severity = 'Critical'
                ),

                COUNT(*) FILTER (
                    WHERE created_at >= CURRENT_DATE
                ),

                COUNT(*) FILTER (
                    WHERE
                        status = 'Resolved'
                        AND updated_at >= CURRENT_DATE
                ),

                COUNT(*) FILTER (
                    WHERE status = 'In Process'
                )

            FROM complaints;
        """)

        row = cursor.fetchone()

        return {

            "total":
                row[0] or 0,

            "active":
                row[1] or 0,

            "critical":
                row[2] or 0,

            "today":
                row[3] or 0,

            "resolved_today":
                row[4] or 0,

            "in_process":
                row[5] or 0

        }

    except Exception as error:

        print(
            "City status error:"
        )

        print(error)

        return {

            "total": 0,

            "active": 0,

            "critical": 0,

            "today": 0,

            "resolved_today": 0,

            "in_process": 0

        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# COMPLETE INTELLIGENCE SUMMARY
# ============================================================

def get_intelligence_summary():

    return {

        "city_status":
            get_city_status(),

        "trends":
            get_complaint_trends(),

        "recurring_problems":
            detect_recurring_problems(),

        "risk_predictions":
            calculate_risk_predictions(),

        "urban_improvement":
            calculate_urban_improvement_score(),

        "department_performance":
            get_department_performance(),

        "map_data":
            get_city_map_data()

    }