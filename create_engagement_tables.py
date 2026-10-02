from database import get_db_connection


def create_engagement_tables():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # =================================================
        # CIVIC POINTS
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS civic_points (
                id SERIAL PRIMARY KEY,

                user_id INTEGER NOT NULL
                    UNIQUE
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                points INTEGER NOT NULL DEFAULT 0,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # =================================================
        # REWARDS
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rewards (
                id SERIAL PRIMARY KEY,

                name VARCHAR(100) NOT NULL,

                description TEXT,

                points_required INTEGER NOT NULL,

                icon VARCHAR(20)
                    DEFAULT '🏅',

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # =================================================
        # MAKE REWARD NAME UNIQUE
        # =================================================

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            rewards_name_unique
            ON rewards(name);
        """)

        # =================================================
        # USER REWARDS
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_rewards (
                id SERIAL PRIMARY KEY,

                user_id INTEGER NOT NULL
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                reward_id INTEGER NOT NULL
                    REFERENCES rewards(id)
                    ON DELETE CASCADE,

                earned_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(
                    user_id,
                    reward_id
                )
            );
        """)

        # =================================================
        # NOTIFICATIONS
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,

                user_id INTEGER NOT NULL
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                title VARCHAR(150) NOT NULL,

                message TEXT NOT NULL,

                notification_type VARCHAR(50)
                    DEFAULT 'general',

                complaint_id INTEGER
                    REFERENCES complaints(id)
                    ON DELETE CASCADE,

                is_read BOOLEAN
                    DEFAULT FALSE,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # =================================================
        # DEFAULT REWARDS
        # =================================================

        rewards = [

            (
                "Civic Contributor",
                "Earned by actively reporting civic problems.",
                50,
                "🏅"
            ),

            (
                "Community Helper",
                "Earned by making regular civic contributions.",
                100,
                "🌟"
            ),

            (
                "Urban Champion",
                "Earned by becoming a highly active civic contributor.",
                250,
                "🏆"
            )

        ]

        for reward in rewards:

            cursor.execute("""
                INSERT INTO rewards
                (
                    name,
                    description,
                    points_required,
                    icon
                )
                VALUES
                (%s, %s, %s, %s)
                ON CONFLICT (name)
                DO NOTHING;
            """, reward)

        connection.commit()

        print(
            "Engagement tables created successfully!"
        )

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "Engagement table error:"
        )

        print(error)

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":

    create_engagement_tables()