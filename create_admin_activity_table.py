from database import get_db_connection


def create_admin_activity_table():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_activity_log (

                id SERIAL PRIMARY KEY,

                admin_id INTEGER NOT NULL
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                action VARCHAR(100) NOT NULL,

                target_user_id INTEGER
                    REFERENCES users(id)
                    ON DELETE SET NULL,

                details TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        connection.commit()

        print(
            "Admin activity log table created successfully!"
        )

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "Error creating admin activity table:"
        )

        print(error)

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":
    create_admin_activity_table()