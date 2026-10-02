import psycopg2


def get_db_connection():

    connection = psycopg2.connect(
        host="localhost",
        database="urban_smartcity",
        user="postgres",
        password="31blossom",
        port="5432"
    )

    return connection


if __name__ == "__main__":

    try:

        connection = get_db_connection()

        print("PostgreSQL connected successfully!")

        connection.close()

    except Exception as error:

        print("Database connection failed:")
        print(error)