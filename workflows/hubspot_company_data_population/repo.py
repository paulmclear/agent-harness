"""SQLite repository for HubSpot company data population workflow."""

class HubSpotCompanyRepository:

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Initialize the SQLite database, creating or migrating the table as needed."""
        import sqlite3

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    hubspot_id TEXT UNIQUE,
                    data TEXT
                )
            """)
            self._migrate_if_needed(conn)

    def _migrate_if_needed(self, conn):
        """Migrate from legacy schema (name UNIQUE) to current (hubspot_id UNIQUE).

        SQLite cannot drop a column constraint in place, so this rebuilds the table
        when the old unique-on-name constraint is detected. Deduplicates by hubspot_id,
        keeping the most recent row (highest id).
        """
        cursor = conn.cursor()

        def unique_columns():
            cols = set()
            for _, idx_name, is_unique, _, _ in cursor.execute(
                "PRAGMA index_list(companies)"
            ).fetchall():
                if not is_unique:
                    continue
                idx_cols = [r[2] for r in cursor.execute(
                    f"PRAGMA index_info({idx_name!r})"
                ).fetchall()]
                if len(idx_cols) == 1:
                    cols.add(idx_cols[0])
            return cols

        uniques = unique_columns()
        if "hubspot_id" in uniques and "name" not in uniques:
            return  # already on the current schema

        print("[repo] migrating companies table to hubspot_id-unique schema")
        cursor.executescript("""
            CREATE TABLE companies_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                hubspot_id TEXT UNIQUE,
                data TEXT
            );
            INSERT INTO companies_new (id, name, hubspot_id, data)
            SELECT id, name, hubspot_id, data
            FROM companies
            WHERE hubspot_id IS NOT NULL
              AND id IN (
                SELECT MAX(id) FROM companies
                WHERE hubspot_id IS NOT NULL
                GROUP BY hubspot_id
              );
            DROP TABLE companies;
            ALTER TABLE companies_new RENAME TO companies;
        """)

    def add_company(self, name: str, hubspot_id: str, data: dict):
        """Insert a company, or update its name/data if the hubspot_id already exists."""
        import sqlite3
        import json

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO companies (name, hubspot_id, data)
                VALUES (?, ?, ?)
                ON CONFLICT(hubspot_id) DO UPDATE SET
                    name = excluded.name,
                    data = excluded.data
            """, (name, hubspot_id, json.dumps(data)))

    def output_normalised_data(self) -> list[dict]:
        """Output all companies in the repository with normalised data."""
        import sqlite3
        import json

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, hubspot_id, data FROM companies")
            rows = cursor.fetchall()

        normal_data = []
        for name, hubspot_id, data_json in rows:
            data = json.loads(data_json) if data_json else {}
            normal_data.append({
                "hubspot_id": hubspot_id,
                "name": name,
                "sector": data.get("sector"),
                "sub_sector": data.get("sub_sector"),
                "confidence": data.get("confidence"),
                "rationale": data.get("rationale"),
                "flags": ", ".join(data.get("flags") or []),
            })

        return normal_data
