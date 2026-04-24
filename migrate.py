import argparse
import mariadb
import sys

def run_migration(host, user, password, database):
    try:
        conn = mariadb.connect(host=host, user=user, password=password, database=database)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)")
        conn.commit()
    except mariadb.Error:
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn: conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-host', required=True)
    parser.add_argument('--db-user', required=True)
    parser.add_argument('--db-password', required=True)
    parser.add_argument('--db-name', required=True)
    args = parser.parse_args()
    run_migration(args.db_host, args.db_user, args.db_password, args.db_name)