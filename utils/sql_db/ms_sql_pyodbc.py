"""
mssql_module_auto.py

A Python module to interact with Microsoft SQL Server using pyodbc with automatic connection management.

Dependencies:
- pyodbc: pip install pyodbc

Example usage:
    python mssql_module_auto.py
"""

import logging
import pyodbc
from contextlib import contextmanager


class MSSQLDatabase:
    """
    MSSQLDatabase provides context-managed methods to interact with a Microsoft SQL Server database.
    """

    def __init__(
        self,
        server,
        database,
        username=None,
        password=None,
        driver="{ODBC Driver 17 for SQL Server}",
        debug=False,
    ):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.driver = driver
        self.debug = debug

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @contextmanager
    def connect(self):
        """
        Context manager for automatic connection handling.
        """
        conn_str = f"DRIVER={self.driver};SERVER={self.server};DATABASE={self.database};"

        if self.username and self.password:
            conn_str += f"UID={self.username};PWD={self.password}"
        else:
            conn_str += "Trusted_Connection=yes"

        connection = None
        try:
            self.logger.debug("Opening database connection")
            connection = pyodbc.connect(conn_str)
            cursor = connection.cursor()
            yield cursor
            connection.commit()
            self.logger.debug("Transaction committed")
        except pyodbc.Error:
            if connection:
                connection.rollback()
                self.logger.debug("Transaction rolled back")
            self.logger.exception("Database operation failed")
            raise
        finally:
            if connection:
                connection.close()
                self.logger.debug("Database connection closed")

    def fetch_all(self, query, params=None):
        """
        Execute a query and return all rows as a list of tuples.
        """
        if self.debug:
            self.logger.info("Executing query: %s | Params: %s", query, params)

        with self.connect() as cursor:
            cursor.execute(query, params or ())
            rows = cursor.fetchall()

        self.logger.info("Fetched %d rows", len(rows))
        return rows

    def execute(self, query, params=None):
        """
        Execute a query (INSERT/UPDATE/DELETE) with automatic commit.
        """
        if self.debug:
            self.logger.info("Executing statement: %s | Params: %s", query, params)

        with self.connect() as cursor:
            cursor.execute(query, params or ())

        self.logger.info("Statement executed successfully")

    def bulk_insert(self, table: str, file_path: str) -> None:
        """
        Perform a bulk insert from a CSV file into the specified table.
        """
        bulk_sql = f"""
            BULK INSERT {table}
            FROM '{file_path}'
            WITH (
                FORMAT = 'CSV',
                FIRSTROW = 2,
                FIELDTERMINATOR = ',',
                ROWTERMINATOR = '0x0a',
                TABLOCK
            );
        """

        try:
            self.logger.info("Starting bulk insert into table: %s", table)
            self.execute(bulk_sql)
            self.logger.info("Bulk insert completed successfully into table: %s", table)
        except Exception:
            self.logger.exception("Bulk insert failed for table: %s", table)
            raise


if __name__ == "__main__":
    # Example usage
    db = MSSQLDatabase(server="localhost", database="UC_Wiz_Data", username="sa", password="my_laptop")

    # Fetch rows
    rows = db.fetch_all("SELECT 'Test' AS Success")
    for row in rows:
        print(row)
