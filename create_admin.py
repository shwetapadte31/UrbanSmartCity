import os
from database import get_db_connection
from werkzeug.security import generate_password_hash


def create_admin():

    name = "System Administrator"

    email = os.getenv(
        "ADMIN_EMAIL",
        "admin@urbansmartcity.com"
    )

    password = os.getenv("ADMIN_PASSWORD")

    if not password:
        print("ADMIN_PASSWORD is not set.")
        return

    password_hash = generate_password_hash(password)

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM users
            WHERE email = %s;
        """, (email,))

        existing_admin = cursor.fetchone()

        if existing_admin:
            print("Admin account already exists.")
            return

        cursor.execute("""
            INSERT INTO users (
                name,
                email,
                password_hash,
                role,
                verification_status
            )
            VALUES (%s, %s, %s, %s, %s);
        """, (
            name,
            email,
            password_hash,
            "admin",
            "verified"
        ))

        connection.commit()

        print("Admin account created successfully.")

    except Exception as error:

        if connection:
            connection.rollback()

        print("Error creating admin:")
        print(error)

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":
    create_admin()