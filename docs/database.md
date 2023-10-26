# Database

## Migrations

Migrations can be run using `migrate.py` in the root directory using the following steps:

1. In `database/migrations` create a new `.sql` migration file
2. Run `python migrate.py {migration_file_name}` in the terminal
3. Log-in to Planetscale, review the changes on the dev branch and create a deploy request
4. If all ok, approve the deploy request
5. Once deploy is finalised, run `python deploy_migration.py` to sync the data in the migrations table in the master db
   with dev

### Notes

Migration files should be named using the following format:

`YYYY-MM-DD_description_of_change.sql`

This is set in `migrate.py` but make sure to only run migrations on the dev branch on Planetscale. Only make changes to
the master db usign Planetscale's deploy requests.

