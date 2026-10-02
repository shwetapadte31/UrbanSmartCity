from create_tables import create_tables
from create_verification_table import create_verification_table
from create_admin_activity_table import create_admin_activity_table
from create_recurring_table import create_recurring_table
from create_risk_prediction_table import create_risk_prediction_table
from create_engagement_tables import create_engagement_tables


def initialize_database():

    print("Starting database initialization...")

    create_tables()
    create_verification_table()
    create_admin_activity_table()
    create_recurring_table()
    create_risk_prediction_table()
    create_engagement_tables()

    print("====================================")
    print("DATABASE INITIALIZATION COMPLETE")
    print("====================================")


if __name__ == "__main__":
    initialize_database()