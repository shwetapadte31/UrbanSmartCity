# ============================================================
# URBAN SMART CITY
# AI PROBLEM CLASSIFIER
# ============================================================

import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from ai.training_data import TRAINING_DATA


# ============================================================
# PREPROCESSING
# ============================================================

def clean_text(text):

    text = str(text).lower()

    text = re.sub(
        r"[^a-zA-Z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# PREPARE DATA
# ============================================================

texts = [
    clean_text(item[0])
    for item in TRAINING_DATA
]

labels = [
    item[1]
    for item in TRAINING_DATA
]


# ============================================================
# TF-IDF
# ============================================================

vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    min_df=1,
    sublinear_tf=True
)


X = vectorizer.fit_transform(
    texts
)


# ============================================================
# MACHINE LEARNING MODEL
# ============================================================

model = LogisticRegression(
    max_iter=2000
)


model.fit(
    X,
    labels
)


# ============================================================
# KEYWORD FALLBACK
# ============================================================

KEYWORD_RULES = {

    "Pothole": [
        "pothole",
        "deep hole",
        "road hole"
    ],

    "Garbage": [
        "garbage",
        "waste",
        "dustbin",
        "trash",
        "rubbish"
    ],

    "Water Leakage": [
        "water leak",
        "leaking pipe",
        "pipe burst",
        "water pipeline",
        "pipeline leak"
    ],

    "Drainage": [
        "drain",
        "drainage",
        "sewer",
        "sewage",
        "blocked drain"
    ],

    "Waterlogging": [
        "waterlogged",
        "waterlogging",
        "flooded",
        "flooding",
        "rainwater",
        "water accumulation"
    ],

    "Streetlight": [
        "streetlight",
        "street light",
        "street lamp",
        "lamp post",
        "dark road"
    ],

    "Traffic": [
        "traffic",
        "congestion",
        "traffic jam",
        "traffic signal",
        "signal"
    ],

    "Road Damage": [
        "damaged road",
        "broken road",
        "road damage",
        "road crack",
        "cracked road",
        "resurfacing"
    ],

    "Infrastructure": [
        "footpath",
        "railing",
        "public structure",
        "public property",
        "infrastructure"
    ]

}


# ============================================================
# KEYWORD PREDICTION
# ============================================================

def keyword_prediction(text):

    text = clean_text(text)


    scores = {}


    for category, keywords in KEYWORD_RULES.items():

        score = 0


        for keyword in keywords:

            keyword = clean_text(
                keyword
            )


            if keyword in text:

                if " " in keyword:
                    score += 2
                else:
                    score += 1


        scores[category] = score


    best_category = max(
            scores,
            key=scores.get
        )


    best_score =scores[best_category]


    if best_score > 0:

        return (
            best_category,
            best_score
        )


    return (
        None,
        0
    )


# ============================================================
# MAIN PREDICTION
# ============================================================

def predict_problem_type(
    description
):

    text =clean_text(
            description
        )


    if not text:

        return (
            "Infrastructure",
            0
        )


    # --------------------------------------------------------
    # Keyword check
    # --------------------------------------------------------

    keyword_type, keyword_score =keyword_prediction(
            text
        )


    # --------------------------------------------------------
    # ML prediction
    # --------------------------------------------------------

    vector =vectorizer.transform(
            [text]
        )


    probabilities =model.predict_proba(
            vector
        )[0]


    best_index =probabilities.argmax()


    ml_type =model.classes_[
            best_index
        ]


    ml_confidence =float(
            probabilities[
                best_index
            ]
        ) * 100


    # --------------------------------------------------------
    # Combine ML + keyword intelligence
    # --------------------------------------------------------

    if keyword_type:

        if keyword_score >= 2:

            return (
                keyword_type,
                round(
                    max(
                        ml_confidence,
                        85
                    ),
                    2
                )
            )


        if (
            keyword_type ==
            ml_type
        ):

            return (
                ml_type,
                round(
                    max(
                        ml_confidence,
                        80
                    ),
                    2
                )
            )


    # --------------------------------------------------------
    # ML result
    # --------------------------------------------------------

    return (
        ml_type,
        round(
            ml_confidence,
            2
        )
    )