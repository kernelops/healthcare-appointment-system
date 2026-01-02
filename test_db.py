from database.connection import initialize_pool, test_connection

if __name__ == "__main__":
    print("Testing database connection...")
    initialize_pool()
    test_connection()
