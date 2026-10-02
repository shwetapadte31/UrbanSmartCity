from flask import Blueprint, jsonify, session
from database import get_db_connection

from collections import defaultdict
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import math

try:
    from sklearn.linear_model import LinearRegression
except ImportError:
    LinearRegression = None


intelligence_bp = Blueprint(
    "intelligence",
    __name__
)


# =========================================================
# ACCESS CONTROL
# =========================================================

def check_intelligence_access():

    if "user_id" not in session:
        return False, jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    if session.get("role") not in [
        "municipality_officer",
        "admin"
    ]:
        return False, jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    return True, None, None


# =========================================================
# HELPERS
# =========================================================

def safe_date(value):

    if isinstance(value, datetime):
        return value

    if value:
        try:
            return datetime.fromisoformat(
                str(value)
            )
        except Exception:
            pass

    return datetime.now()


def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    if (
        lat1 is None
        or lon1 is None
        or lat2 is None
        or lon2 is None
    ):
        return None

    try:

        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)

        earth_radius = 6371

        d_lat = math.radians(
            lat2 - lat1
        )

        d_lon = math.radians(
            lon2 - lon1
        )

        a = (
            math.sin(d_lat / 2) ** 2
            +
            math.cos(math.radians(lat1))
            *
            math.cos(math.radians(lat2))
            *
            math.sin(d_lon / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        return earth_radius * c

    except Exception:

        return None


def text_similarity(
    text1,
    text2
):

    text1 = str(text1 or "").lower().strip()
    text2 = str(text2 or "").lower().strip()

    if not text1 or not text2:
        return 0

    return round(
        SequenceMatcher(
            None,
            text1,
            text2
        ).ratio() * 100,
        2
    )


def get_risk_level(score):

    if score >= 75:
        return "Critical"

    if score >= 50:
        return "High"

    if score >= 25:
        return "Medium"

    return "Low"


def get_locality_name(address):

    if not address:
        return "Unknown Locality"

    address = str(address).strip()

    parts = [
        part.strip()
        for part in address.split(",")
        if part.strip()
    ]

    if parts:
        return parts[-1]

    return address


def get_recommended_action(
    problem_type
):

    actions = {

        "Pothole":
            "Inspect the road and schedule pothole repair.",

        "Road Damage":
            "Inspect damaged road and arrange maintenance or resurfacing.",

        "Garbage":
            "Arrange waste collection and inspect the affected area.",

        "Water Leakage":
            "Inspect the water pipeline and stop the leakage.",

        "Drainage":
            "Inspect and clear blocked drainage or sewer lines.",

        "Waterlogging":
            "Inspect drainage capacity and remove accumulated water.",

        "Streetlight":
            "Inspect the streetlight and restore proper lighting.",

        "Traffic":
            "Inspect the traffic issue and coordinate traffic management.",

        "Infrastructure":
            "Inspect the damaged infrastructure and schedule repair."

    }

    return actions.get(
        problem_type,
        "Inspect the reported issue and assign the appropriate municipal department."
    )


# =========================================================
# LOAD COMPLAINT DATA
# =========================================================

def load_complaints():

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
                d.name
            FROM complaints c
            LEFT JOIN departments d
                ON c.responsible_department_id = d.id
            ORDER BY c.created_at ASC;
        """)

        rows = cursor.fetchall()

        complaints = []

        for row in rows:

            complaints.append({

                "id": row[0],

                "complaint_number":
                    row[1],

                "problem_type":
                    row[2] or "Infrastructure",

                "description":
                    row[3] or "",

                "urgency":
                    row[4] or "Medium",

                "severity":
                    row[5] or "Low",

                "priority":
                    row[6] or "Low",

                "status":
                    row[7] or "Reported",

                "address":
                    row[8] or "Unknown Location",

                "latitude":
                    float(row[9])
                    if row[9] is not None
                    else None,

                "longitude":
                    float(row[10])
                    if row[10] is not None
                    else None,

                "created_at":
                    row[11],

                "updated_at":
                    row[12],

                "department":
                    row[13] or "Not Assigned"

            })

        return complaints

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# DUPLICATE DETECTION
# =========================================================

@intelligence_bp.route(
    "/api/intelligence/duplicates/<int:complaint_id>"
)
def detect_duplicates(complaint_id):

    allowed, response, status = (
        check_intelligence_access()
    )

    if not allowed:
        return response, status

    complaints = load_complaints()

    target = None

    for complaint in complaints:

        if complaint["id"] == complaint_id:
            target = complaint
            break

    if not target:

        return jsonify({
            "success": False,
            "message": "Complaint not found."
        }), 404

    duplicates = []

    target_date = safe_date(
        target["created_at"]
    )

    for complaint in complaints:

        if complaint["id"] == complaint_id:
            continue

        other_date = safe_date(
            complaint["created_at"]
        )

        days_difference = abs(
            (
                target_date -
                other_date
            ).total_seconds()
        ) / 86400

        if days_difference > 30:
            continue

        score = 0

        if (
            complaint["problem_type"]
            ==
            target["problem_type"]
        ):
            score += 35

        distance = calculate_distance(
            target["latitude"],
            target["longitude"],
            complaint["latitude"],
            complaint["longitude"]
        )

        if distance is not None:

            if distance <= 0.1:
                score += 40

            elif distance <= 0.3:
                score += 30

            elif distance <= 0.5:
                score += 20

        similarity = text_similarity(
            target["description"],
            complaint["description"]
        )

        if similarity >= 70:
            score += 25

        elif similarity >= 50:
            score += 15

        if score >= 55:

            duplicates.append({

                "id":
                    complaint["id"],

                "complaint_number":
                    complaint["complaint_number"],

                "problem_type":
                    complaint["problem_type"],

                "status":
                    complaint["status"],

                "address":
                    complaint["address"],

                "similarity":
                    similarity,

                "distance_km":
                    round(distance, 3)
                    if distance is not None
                    else None,

                "match_score":
                    min(score, 100)

            })

    duplicates.sort(
        key=lambda item:
        item["match_score"],
        reverse=True
    )

    return jsonify({

        "success": True,

        "complaint_id":
            complaint_id,

        "duplicate_count":
            len(duplicates),

        "duplicates":
            duplicates[:10]

    })


# =========================================================
# RECURRING PROBLEMS
# =========================================================

@intelligence_bp.route(
    "/api/intelligence/recurring"
)
def recurring_problems():

    allowed, response, status = (
        check_intelligence_access()
    )

    if not allowed:
        return response, status

    complaints = load_complaints()

    groups = defaultdict(list)

    for complaint in complaints:

        locality = get_locality_name(
            complaint["address"]
        )

        key = (
            locality,
            complaint["problem_type"]
        )

        groups[key].append(
            complaint
        )

    recurring = []

    for (
        key,
        items
    ) in groups.items():

        if len(items) < 2:
            continue

        locality, problem_type = key

        active_count = sum(
            1
            for item in items
            if item["status"] != "Resolved"
        )

        resolved_count = sum(
            1
            for item in items
            if item["status"] == "Resolved"
        )

        latest = max(
            items,
            key=lambda item:
            safe_date(item["created_at"])
        )

        recurring.append({

            "locality":
                locality,

            "problem_type":
                problem_type,

            "count":
                len(items),

            "active":
                active_count,

            "resolved":
                resolved_count,

            "latest_report":
                latest["complaint_number"],

            "status":
                "Recurring Issue"

        })

    recurring.sort(
        key=lambda item:
        item["count"],
        reverse=True
    )

    return jsonify({

        "success": True,

        "count":
            len(recurring),

        "recurring":
            recurring[:20]

    })


# =========================================================
# COMPLAINT TRENDS
# =========================================================

@intelligence_bp.route(
    "/api/intelligence/trends"
)
def complaint_trends():

    allowed, response, status = (
        check_intelligence_access()
    )

    if not allowed:
        return response, status

    complaints = load_complaints()

    daily = defaultdict(int)

    for complaint in complaints:

        date_value = safe_date(
            complaint["created_at"]
        ).date()

        daily[
            date_value.isoformat()
        ] += 1

    dates = sorted(
        daily.keys()
    )

    trends = []

    for date_value in dates:

        trends.append({

            "date":
                date_value,

            "count":
                daily[date_value]

        })

    problem_counts = defaultdict(int)

    for complaint in complaints:

        problem_counts[
            complaint["problem_type"]
        ] += 1

    categories = []

    for problem_type, count in sorted(
        problem_counts.items(),
        key=lambda item:
        item[1],
        reverse=True
    ):

        categories.append({

            "problem_type":
                problem_type,

            "count":
                count

        })

    return jsonify({

        "success": True,

        "trends":
            trends,

        "categories":
            categories

    })


# =========================================================
# FORECASTING
# =========================================================

@intelligence_bp.route(
    "/api/intelligence/forecast"
)
def complaint_forecast():

    allowed, response, status = (
        check_intelligence_access()
    )

    if not allowed:
        return response, status

    complaints = load_complaints()

    daily = defaultdict(int)

    for complaint in complaints:

        date_value = safe_date(
            complaint["created_at"]
        ).date()

        daily[
            date_value
        ] += 1

    if not daily:

        return jsonify({

            "success": True,

            "historical":
                [],

            "forecast":
                []

        })

    sorted_dates = sorted(
        daily.keys()
    )

    historical = []

    for index, date_value in enumerate(
        sorted_dates
    ):

        historical.append({

            "date":
                date_value.isoformat(),

            "count":
                daily[date_value]

        })

    forecast = []

    values = [
        daily[date_value]
        for date_value in sorted_dates
    ]

    if (
        LinearRegression
        and len(values) >= 3
    ):

        x = [
            [index]
            for index in range(
                len(values)
            )
        ]

        model = LinearRegression()

        model.fit(
            x,
            values
        )

        last_date = sorted_dates[-1]

        for i in range(1, 8):

            future_date = (
                last_date +
                timedelta(days=i)
            )

            prediction = model.predict(
                [[
                    len(values) + i - 1
                ]]
            )[0]

            forecast.append({

                "date":
                    future_date.isoformat(),

                "predicted_count":
                    max(
                        0,
                        round(
                            float(
                                prediction
                            )
                        )
                    )

            })

    else:

        recent_values = values[-7:]

        average = (
            sum(recent_values)
            /
            len(recent_values)
        )

        last_date = sorted_dates[-1]

        for i in range(1, 8):

            future_date = (
                last_date +
                timedelta(days=i)
            )

            forecast.append({

                "date":
                    future_date.isoformat(),

                "predicted_count":
                    round(average)

            })

    return jsonify({

        "success": True,

        "historical":
            historical,

        "forecast":
            forecast

    })


# =========================================================
# RISK INTELLIGENCE
# =========================================================

@intelligence_bp.route(
    "/api/intelligence/risk"
)
def risk_prediction():

    allowed, response, status = (
        check_intelligence_access()
    )

    if not allowed:
        return response, status

    complaints = load_complaints()

    locality_groups = defaultdict(list)

    for complaint in complaints:

        locality = get_locality_name(
            complaint["address"]
        )

        locality_groups[
            locality
        ].append(complaint)

    risk_data = []

    for locality, items in locality_groups.items():

        total = len(items)

        critical = sum(
            1
            for item in items
            if item["severity"]
            == "Critical"
        )

        high = sum(
            1
            for item in items
            if item["severity"]
            == "High"
        )

        active = sum(
            1
            for item in items
            if item["status"]
            != "Resolved"
        )

        recent = 0

        now = datetime.now()

        for item in items:

            created = safe_date(
                item["created_at"]
            )

            if (
                now - created
            ).days <= 30:

                recent += 1

        score = 0

        score += min(
            total * 5,
            30
        )

        score += min(
            critical * 15,
            30
        )

        score += min(
            high * 8,
            20
        )

        score += min(
            active * 3,
            15
        )

        score += min(
            recent * 2,
            10
        )

        score = min(
            score,
            100
        )

        risk_data.append({

            "locality":
                locality,

            "total_complaints":
                total,

            "critical":
                critical,

            "high":
                high,

            "active":
                active,

            "recent":
                recent,

            "risk_score":
                score,

            "risk_level":
                get_risk_level(score)

        })

    risk_data.sort(
        key=lambda item:
        item["risk_score"],
        reverse=True
    )

    return jsonify({

        "success": True,

        "risk":
            risk_data[:20]

    })


# =========================================================
# LOCALITY INTELLIGENCE
# =========================================================

@intelligence_bp.route(
    "/api/intelligence/localities"
)
def locality_intelligence():

    allowed, response, status = (
        check_intelligence_access()
    )

    if not allowed:
        return response, status

    complaints = load_complaints()

    locality_groups = defaultdict(list)

    for complaint in complaints:

        locality = get_locality_name(
            complaint["address"]
        )

        locality_groups[
            locality
        ].append(complaint)

    localities = []

    for locality, items in locality_groups.items():

        total = len(items)

        resolved = sum(
            1
            for item in items
            if item["status"]
            == "Resolved"
        )

        active = total - resolved

        critical = sum(
            1
            for item in items
            if item["severity"]
            == "Critical"
        )

        resolution_rate = 0

        if total > 0:

            resolution_rate = round(
                (
                    resolved /
                    total
                ) * 100
            )

        score = (
            100
            - min(
                active * 5,
                50
            )
            - min(
                critical * 10,
                30
            )
            + min(
                resolution_rate * 0.2,
                20
            )
        )

        score = round(
            max(
                0,
                min(
                    100,
                    score
                )
            )
        )

        localities.append({

            "locality":
                locality,

            "total":
                total,

            "active":
                active,

            "resolved":
                resolved,

            "critical":
                critical,

            "resolution_rate":
                resolution_rate,

            "score":
                score

        })

    localities.sort(
        key=lambda item:
        item["score"]
    )

    return jsonify({

        "success": True,

        "localities":
            localities[:20]

    })


# =========================================================
# DEPARTMENT PERFORMANCE
# =========================================================

@intelligence_bp.route(
    "/api/intelligence/departments"
)
def department_performance():

    allowed, response, status = (
        check_intelligence_access()
    )

    if not allowed:
        return response, status

    complaints = load_complaints()

    department_groups = defaultdict(list)

    for complaint in complaints:

        department = (
            complaint["department"]
            or "Not Assigned"
        )

        department_groups[
            department
        ].append(complaint)

    departments = []

    for department, items in department_groups.items():

        total = len(items)

        resolved = sum(
            1
            for item in items
            if item["status"]
            == "Resolved"
        )

        active = total - resolved

        critical = sum(
            1
            for item in items
            if item["severity"]
            == "Critical"
        )

        resolution_rate = 0

        if total > 0:

            resolution_rate = round(
                (
                    resolved /
                    total
                ) * 100
            )

        departments.append({

            "department":
                department,

            "name":
                department,

            "total":
                total,

            "count":
                total,

            "resolved":
                resolved,

            "active":
                active,

            "critical":
                critical,

            "resolution_rate":
                resolution_rate

        })

    departments.sort(
        key=lambda item:
        item["total"],
        reverse=True
    )

    return jsonify({

        "success": True,

        "departments":
            departments

    })


# =========================================================
# MUNICIPAL RECOMMENDATIONS
# =========================================================

@intelligence_bp.route(
    "/api/intelligence/recommendations"
)
def municipal_recommendations():

    allowed, response, status = (
        check_intelligence_access()
    )

    if not allowed:
        return response, status

    complaints = load_complaints()

    recommendations = []

    problem_groups = defaultdict(list)

    for complaint in complaints:

        problem_groups[
            complaint["problem_type"]
        ].append(complaint)

    for problem_type, items in problem_groups.items():

        active = [
            item
            for item in items
            if item["status"]
            != "Resolved"
        ]

        critical = [
            item
            for item in items
            if item["severity"]
            == "Critical"
        ]

        if not active:
            continue

        action = get_recommended_action(
            problem_type
        )

        if critical:

            level = "Critical"

            action = (
                "Immediate attention required. "
                +
                action
            )

        elif len(active) >= 5:

            level = "High"

            action = (
                "High recurring workload detected. "
                +
                action
            )

        else:

            level = "Medium"

        recommendations.append({

            "problem_type":
                problem_type,

            "active":
                len(active),

            "critical":
                len(critical),

            "priority":
                level,

            "recommendation":
                action

        })

    recommendations.sort(
        key=lambda item: (
            item["critical"],
            item["active"]
        ),
        reverse=True
    )

    return jsonify({

        "success": True,

        "recommendations":
            recommendations

    })


# =========================================================
# INTELLIGENCE OVERVIEW
# =========================================================

@intelligence_bp.route(
    "/api/intelligence/overview"
)
def intelligence_overview():

    allowed, response, status = (
        check_intelligence_access()
    )

    if not allowed:
        return response, status

    complaints = load_complaints()

    total = len(
        complaints
    )

    active = sum(
        1
        for complaint in complaints
        if complaint["status"]
        != "Resolved"
    )

    resolved = sum(
        1
        for complaint in complaints
        if complaint["status"]
        == "Resolved"
    )

    critical = sum(
        1
        for complaint in complaints
        if complaint["severity"]
        == "Critical"
    )

    high = sum(
        1
        for complaint in complaints
        if complaint["severity"]
        == "High"
    )

    today = sum(
        1
        for complaint in complaints
        if safe_date(
            complaint["created_at"]
        ).date()
        == datetime.now().date()
    )

    resolution_rate = 0

    if total > 0:

        resolution_rate = round(
            (
                resolved /
                total
            ) * 100
        )

    return jsonify({

        "success": True,

        "overview": {

            "total":
                total,

            "active":
                active,

            "resolved":
                resolved,

            "critical":
                critical,

            "high":
                high,

            "today":
                today,

            "resolution_rate":
                resolution_rate

        }

    })