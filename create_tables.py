from database import get_db_connection


def create_tables():

    connection = get_db_connection()

    cursor = connection.cursor()


    # ==========================================
    # DEPARTMENTS TABLE
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (

            id SERIAL PRIMARY KEY,

            name VARCHAR(100) NOT NULL UNIQUE,

            description TEXT

        );
    """)


    # ==========================================
    # USERS TABLE
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id SERIAL PRIMARY KEY,

            name VARCHAR(100) NOT NULL,

            email VARCHAR(150) NOT NULL UNIQUE,

            password_hash TEXT NOT NULL,
role VARCHAR(30) NOT NULL
    CHECK (
        role IN (
            'citizen',
            'municipality_officer',
            'admin'
        )
    ),
verification_status VARCHAR(20) NOT NULL DEFAULT 'verified'
    CHECK (
        verification_status IN (
            'pending',
            'verified',
            'rejected'
        )
    ),
department_id INTEGER
    REFERENCES departments(id),
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
           

        );
    """)


    # ==========================================
    # COMPLAINTS TABLE
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (

            id SERIAL PRIMARY KEY,

            complaint_number VARCHAR(30) UNIQUE,

            user_id INTEGER NOT NULL
                REFERENCES users(id),

            problem_type VARCHAR(50) NOT NULL,

            description TEXT NOT NULL,

            urgency VARCHAR(20),

            severity VARCHAR(20),

            priority VARCHAR(20),

            responsible_department_id INTEGER
                REFERENCES departments(id),

            latitude DECIMAL(10, 7),

            longitude DECIMAL(10, 7),

            address TEXT,

            image_path TEXT,

            status VARCHAR(30) DEFAULT 'Reported',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        );
    """)


    # ==========================================
    # COMPLAINT HISTORY TABLE
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaint_history (

            id SERIAL PRIMARY KEY,

            complaint_id INTEGER NOT NULL
                REFERENCES complaints(id)
                ON DELETE CASCADE,

            old_status VARCHAR(30),

            new_status VARCHAR(30),

            changed_by INTEGER
                REFERENCES users(id),

            remarks TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        );
    """)


    # ==========================================
    # INSERT DEPARTMENTS
    # ==========================================

    departments = [

        (
            "Roads & Public Works",
            "Road construction, potholes and road damage"
        ),

        (
            "Sanitation & Waste Management",
            "Garbage collection and waste management"
        ),

        (
            "Water Supply",
            "Water leakage and water supply problems"
        ),

        (
            "Drainage & Sewerage",
            "Drainage and sewerage related problems"
        ),

        (
            "Street Lighting",
            "Streetlight installation and maintenance"
        ),

        (
            "Traffic Management",
            "Traffic and traffic management problems"
        ),

        (
            "Urban Infrastructure",
            "General infrastructure related problems"
        )

    ]


    for department in departments:

        cursor.execute("""
            INSERT INTO departments
                (name, description)

            VALUES (%s, %s)

            ON CONFLICT (name)
            DO NOTHING;
        """, department)


    connection.commit()

    cursor.close()

    connection.close()


    print("Database tables created successfully!")
    print("Departments added successfully.")


if __name__ == "__main__":

    try:

        create_tables()

    except Exception as error:

        print("Error creating database tables:")
        print(error)