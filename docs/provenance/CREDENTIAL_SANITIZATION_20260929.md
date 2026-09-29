# Legacy ePMP credential sanitization — 2026-09-29

The provenance audit found legacy ePMP scripts with embedded database credentials and a Telegram bot token.

## Changes applied

- PostgreSQL credentials were moved to `/home/carlos/.config/atmoslink/epmp_db.env`.
- Telegram credentials were moved to `/home/carlos/.config/atmoslink/epmp_telegram.env`.
- The secret directory is mode `0700`; both secret files are mode `0600`.
- `auto_csv_pipeline.sh` sources only the database environment file and no longer injects a literal PostgreSQL password.
- `db_writer.py`, `db_writer_predictivo.py`, and `ia_operador.py` obtain `EPMP_DB_URL` from the environment.
- `alertas_automaticas.py` obtains Telegram credentials from environment variables.
- `run_alertas_automaticas.sh` sources only the Telegram environment file before standalone alert execution.
- Original pre-migration files are preserved outside Git under a protected provenance backup directory.
- `.radio_pass` files remain outside Git. Only `epmp.conf`, which points to the password-file path, is versioned.

## Verification

Shell syntax checks and Python compilation passed. A read-only PostgreSQL `SELECT 1` succeeded using the protected database environment. The active cron pipeline completed normally at 2026-09-29 15:05 local time under `set -e`, after the database and Telegram secrets had been separated into least-privilege files. The model, prediction, database, predictive-database, and operator steps all advanced normally.

No secret value is intentionally stored in this repository. The repository contains only placeholder environment examples.
