import os
import sys

# Get the migration filename from the arguments
migration_name = sys.argv[1]

# Check if the file exists
file_path = os.path.join("./database/migrations", f"{migration_name}.sql")

if os.path.isfile(file_path):
    print("Found the file")
else:
    print(f"Could not find the file ${migration_name} in the database/migrations directory")
    sys.exit(1)
