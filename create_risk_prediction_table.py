from database import get_db_connection


def create_risk_prediction_table():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_predictions (

                id SERIAL PRIMARY KEY,

                address TEXT,

                latitude DECIMAL(10, 7),

                longitude DECIMAL(10, 7),

                problem_type VARCHAR(50),

                complaint_count INTEGER DEFAULT 0,

                risk_level VARCHAR(20),

                risk_score DECIMAL(5, 2),

                prediction_date TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        connection.commit()

        print(
            "Risk prediction table created successfully!"
        )

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "Error creating risk prediction table:"
        )

        print(error)

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":
    create_risk_prediction_table()