from database import get_db_connection


def add_official_email_column():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS official_email VARCHAR(150);
        """)

        connection.commit()

        print("official_email column added successfully!")

    except Exception as error:

        if connection:
            connection.rollback()

        print("Error adding official_email:")
        print(error)

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":
    add_official_email_column()