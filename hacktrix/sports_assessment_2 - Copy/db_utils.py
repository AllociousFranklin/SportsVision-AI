import mysql.connector

def create_database_and_tables():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="sql123"
    )
    cursor = conn.cursor()

    # Create database
    cursor.execute("CREATE DATABASE IF NOT EXISTS sports_assessment")
    cursor.execute("USE sports_assessment")

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        age INT,
        height_cm FLOAT,
        weight_kg FLOAT,
        email VARCHAR(100) UNIQUE,
        password VARCHAR(255),
        role ENUM('Player', 'Coach') NOT NULL DEFAULT 'Player',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pushups (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            video_path VARCHAR(255),
            total_pushups INT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vertical_jumps (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            video_path VARCHAR(255),
            jump_height_cm FLOAT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS punches (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            video_path VARCHAR(255),
            total_punches INT,
            duration_sec FLOAT,
            punches_per_sec FLOAT,
            punches_per_min FLOAT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


def get_connection():
    create_database_and_tables()
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="sql123",
        database="sports_assessment"
    )


def save_pushup_result(user_id, video_path, total_pushups):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO pushups (user_id, video_path, total_pushups)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (user_id, video_path, total_pushups))
    conn.commit()
    cursor.close()
    conn.close()


def save_jump_result(user_id, video_path, jump_height_cm):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO vertical_jumps (user_id, video_path, jump_height_cm)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (user_id, video_path, jump_height_cm))
    conn.commit()
    cursor.close()
    conn.close()


def save_punch_result(user_id, video_path, total_punches, duration_sec, punches_per_sec, punches_per_min):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO punches (user_id, video_path, total_punches, duration_sec, punches_per_sec, punches_per_min)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (user_id, video_path, total_punches, duration_sec, punches_per_sec, punches_per_min))
    conn.commit()
    cursor.close()
    conn.close()

