from database import get_db_connection


def create_verification_table():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaint_verification (

                id SERIAL PRIMARY KEY,

                complaint_id INTEGER NOT NULL
                    REFERENCES complaints(id)
                    ON DELETE CASCADE,

                citizen_id INTEGER NOT NULL
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                decision VARCHAR(30) NOT NULL
                    CHECK (
                        decision IN (
                            'resolved',
                            'still_exists'
                        )
                    ),

                remarks TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        connection.commit()

        print("Complaint verification table created successfully!")

    except Exception as error:

        if connection:
            connection.rollback()

        print("Error creating complaint verification table:")
        print(error)

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":
    create_verification_table()