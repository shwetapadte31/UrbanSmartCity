from database import get_db_connection
from werkzeug.security import generate_password_hash


def create_admin():
    name = "System Administrator"
    email = "admin@urbansmartcity.com"
    password = "Admin@123"

    password_hash = generate_password_hash(password)

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check whether admin already exists
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

        print("Admin account created successfully!")
        print("Email:", email)
        print("Password:", password)

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