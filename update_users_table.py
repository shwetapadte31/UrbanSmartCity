from database import get_db_connection


def update_users_table():

    connection = get_db_connection()
    cursor = connection.cursor()

    # Add verification_status column
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS verification_status VARCHAR(20)
        DEFAULT 'verified';
    """)

    # Allow admin role
    cursor.execute("""
        ALTER TABLE users
        DROP CONSTRAINT IF EXISTS users_role_check;
    """)

    cursor.execute("""
        ALTER TABLE users
        ADD CONSTRAINT users_role_check
        CHECK (
            role IN (
                'citizen',
                'municipality_officer',
                'admin'
            )
        );
    """)

    # Add verification status constraint
    cursor.execute("""
        ALTER TABLE users
        DROP CONSTRAINT IF EXISTS users_verification_status_check;
    """)

    cursor.execute("""
        ALTER TABLE users
        ADD CONSTRAINT users_verification_status_check
        CHECK (
            verification_status IN (
                'pending',
                'verified',
                'rejected'
            )
        );
    """)
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS officer_id VARCHAR(50);
    """)

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS verification_reason TEXT;
    """)
    connection.commit()

    cursor.close()
    connection.close()

    print("Users table updated successfully!")


if __name__ == "__main__":

    try:
        update_users_table()

    except Exception as error:

        print("Error updating users table:")
        print(error)
