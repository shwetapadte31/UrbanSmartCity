from ai.classifier import predict_problem_type


# -----------------------------------------
# Department mapping
# -----------------------------------------

DEPARTMENT_MAP = {

    "Pothole":
        "Roads & Public Works",

    "Road Damage":
        "Roads & Public Works",

    "Garbage":
        "Sanitation & Waste Management",

    "Water Leakage":
        "Water Supply",

    "Drainage":
        "Drainage & Sewerage",

    "Waterlogging":
        "Drainage & Sewerage",

    "Streetlight":
        "Street Lighting",

    "Traffic":
        "Traffic Management",

    "Infrastructure":
        "Urban Infrastructure"
}


# -----------------------------------------
# Severity detection
# -----------------------------------------

def calculate_severity(description, urgency):

    text = description.lower()

    critical_words = [
        "dangerous",
        "life threatening",
        "accident",
        "emergency",
        "collapsed",
        "major flooding"
    ]

    high_words = [
        "deep",
        "severe",
        "large",
        "heavy",
        "overflowing",
        "blocked",
        "broken"
    ]

    if urgency.lower() == "critical":
        return "Critical"

    for word in critical_words:
        if word in text:
            return "Critical"

    if urgency.lower() == "high":
        return "High"

    for word in high_words:
        if word in text:
            return "High"

    if urgency.lower() == "medium":
        return "Medium"

    return "Low"


# -----------------------------------------
# Priority calculation
# -----------------------------------------

def calculate_priority(severity, confidence):

    if severity == "Critical":
        return "Critical"

    if severity == "High":
        return "High"

    if severity == "Medium":
        return "Medium"

    if confidence < 50:
        return "Medium"

    return "Low"


# -----------------------------------------
# Main AI processing function
# -----------------------------------------

def process_complaint(description, urgency):

    problem_type, confidence = predict_problem_type(
        description
    )

    department = DEPARTMENT_MAP.get(
        problem_type,
        "Urban Infrastructure"
    )

    severity = calculate_severity(
        description,
        urgency
    )

    priority = calculate_priority(
        severity,
        confidence
    )

    return {
        "problem_type": problem_type,
        "confidence": round(confidence, 2),
        "severity": severity,
        "priority": priority,
        "department": department
    }


# -----------------------------------------
# Test
# -----------------------------------------

if __name__ == "__main__":

    description = (
        "There is a very deep and dangerous "
        "pothole near the school"
    )

    urgency = "High"

    result = process_complaint(
        description,
        urgency
    )

    print("\nAI Complaint Processing")
    print("-----------------------")

    print(
        "Problem Type:",
        result["problem_type"]
    )

    print(
        "Confidence:",
        result["confidence"],
        "%"
    )

    print(
        "Severity:",
        result["severity"]
    )

    print(
        "Priority:",
        result["priority"]
    )

    print(
        "Department:",
        result["department"]
    )