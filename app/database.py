import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=dotenv_path)

# Database credentials
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "polaglot")
DB_USER = os.getenv("DB_USER", "polaglot_user")
DB_PASS = os.getenv("DB_PASS", "")

# Initialize connection pool
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10,
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    if connection_pool:
        print("Database connection pool created successfully")
except Exception as e:
    print(f"Error creating database connection pool: {e}")
    connection_pool = None

def get_connection():
    if connection_pool:
        return connection_pool.getconn()
    return None

def release_connection(conn):
    if connection_pool and conn:
        connection_pool.putconn(conn)

def init_db():
    """Initialize the database tables if they don't exist."""
    conn = get_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            # Create user_state table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_state (
                    user_id BIGINT PRIMARY KEY,
                    mode VARCHAR(50) DEFAULT 'explain',
                    quiz_pending BOOLEAN DEFAULT FALSE,
                    quiz_answer TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            print("Database tables initialized")
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        release_connection(conn)

def save_user_state(user_id, mode=None, quiz_pending=None, quiz_answer=None):
    """Save or update user state in the database."""
    conn = get_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            # Use UPSERT (INSERT ... ON CONFLICT)
            cur.execute("""
                INSERT INTO user_state (user_id, mode, quiz_pending, quiz_answer, last_updated)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    mode = COALESCE(EXCLUDED.mode, user_state.mode),
                    quiz_pending = COALESCE(EXCLUDED.quiz_pending, user_state.quiz_pending),
                    quiz_answer = COALESCE(EXCLUDED.quiz_answer, user_state.quiz_answer),
                    last_updated = CURRENT_TIMESTAMP;
            """, (user_id, mode, quiz_pending, quiz_answer))
            conn.commit()
    except Exception as e:
        print(f"Error saving user state: {e}")
        conn.rollback()
    finally:
        release_connection(conn)

def load_user_state(user_id):
    """Load user state from the database."""
    conn = get_connection()
    if not conn:
        return {}

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT mode, quiz_pending, quiz_answer FROM user_state WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            if row:
                return {
                    "mode": row[0],
                    "quiz_pending": row[1],
                    "quiz_answer": row[2]
                }
    except Exception as e:
        print(f"Error loading user state: {e}")
    finally:
        release_connection(conn)
    
    return {}
