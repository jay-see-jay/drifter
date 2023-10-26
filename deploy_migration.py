from services.database import Database
from stubs.internal import Migration

dev_db = Database('development')

dev_results = dev_db.query(
    'SELECT * FROM migrations;',
    ()
)

dev_migrations = [
    Migration(
        name=result['name'],
        date=result['date'],
        completed_at=result['completed_at'],
    )
    for result in dev_results
]

main_db = Database('production')

main_results = main_db.query(
    'SELECT date_name FROM migrations;',
    ()
)

main_migrations = [
    result['date_name']
    for result in main_results
]

for migration in dev_migrations:
    if migration.date_name in main_migrations:
        print(f'{migration.name} is already in the main branch')
    else:
        main_db.query(
            'INSERT INTO migrations (name, date, completed_at) VALUES (%s, %s, %s);',
            (migration.name, migration.date, migration.completed_at),
        )
