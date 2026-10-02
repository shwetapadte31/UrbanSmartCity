from database import get_db_connection


def create_recurring_table():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recurring_problems (

                id SERIAL PRIMARY KEY,

                problem_type VARCHAR(50) NOT NULL,

                address TEXT,

                latitude DECIMAL(10, 7),

                longitude DECIMAL(10, 7),

                complaint_count INTEGER DEFAULT 0,

                risk_level VARCHAR(20),

                first_reported TIMESTAMP,

                last_reported TIMESTAMP,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        connection.commit()

        print(
            "Recurring problems table created successfully!"
        )

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "Error creating recurring problems table:"
        )

        print(error)

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":
    create_recurring_table()