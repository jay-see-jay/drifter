import os
import sys

from datetime import datetime

from services.database import Database
from stubs.internal import Migration

# Get the migration filename from the arguments
migration_name = sys.argv[1]

# Check if the file exists
file_path = os.path.join("./database/migrations", f"{migration_name}.sql")

if not os.path.isfile(file_path):
    print(f"Could not find the file {migration_name} in the migrations directory")
    sys.exit(1)

date_string, name = migration_name.split("_", 1)

date = datetime.strptime(date_string, "%Y-%m-%d")

migration = Migration(name=name, date=date, completed_at=None)

if not migration.id == migration_name:
    print(f"Migration name is not in the correct format: {migration_name}")
    sys.exit(1)

db = Database('development')

check_query = """
    SELECT * FROM migrations
    WHERE name = %s AND completed_at IS NOT NULL;
"""
check_variables = (migration.name,)
try:
    result = db.query(check_query, check_variables)
    if len(result) > 0:
        print('Migration has already been completed')
        sys.exit(1)
except Exception as e:
    print('Could not access db to check if migration has run before')
    sys.exit(1)

with open(file_path, 'r') as file:
    query = file.read()

print('Running migration...')
try:
    db.query(query, ())
except Exception as e:
    print(f'Failed to run migration: {e}')
    sys.exit(1)

print('Updating migration status...')

insert = """
    INSERT INTO migrations (name, date, completed_at)
    VALUES (%s, %s, %s)
"""
variables = (migration.name, migration.date, datetime.now())

try:
    db.query(insert, variables)
except Exception as e:
    print(f'Failed to update migration record: {e}')
