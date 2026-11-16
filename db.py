import psycopg


def get_db_connection():
    try:
        connection = psycopg.connect(
            host="localhost",
            port="5432",
            dbname="hostel_management",
            user="postgres",
            password="YOUR_POSTGRES_PASSWORD"  # Replace with your PostgreSQL password
        )
        return connection
    except Exception as error:
        print("Database Connection Failed:", error)
        return None
