import logging
from utils.db_utils import get_database_schema
from typing import Optional

logger = logging.getLogger(__name__)

class DBHandler():
    def __init__(self, connection):
        """
        Initializes the database handler.

        Args:
            connection: psycopg2 connection to the database.
        """
        self.conn = connection


    def run_query(self, query: str, params: Optional[tuple] = None, many: bool = False, fetch: bool = False, columns: bool = False, rollback: bool = False) -> list[tuple]:
        """
        Executes SQL queries, handling parameters, multiple executions and data retrieval.
    
        Args:
            query (str): SQL query.
            params (tuple): Parameters with values for placeholders.
            many (bool): Default false, set true to execute batch of queries.
            fetch (bool): Default false, set true to retrieve query's results.
            columns (bool): Default false, set true to retrieve query's results and columns' names.
            rollback (bool): If True, rollback the transaction on exception.
        
        Returns:
            list: If fetch is set true returns a list of tuples with query's result.
            If columns is set true returns a list of tuples with query's result and a list of columns' names.
            None: If fetch is false.
        """
        try:
            with self.conn.cursor() as cursor:
                if many:
                    cursor.executemany(query, params)
                elif params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
    
                self.conn.commit()
    
                if fetch:
                    result = cursor.fetchall()
                    if columns:
                        columns_names = [desc[0] for desc in cursor.description]
                        return result, columns_names
                    return result
        except Exception as e:
            if rollback:
                self.conn.rollback()
            raise e

    def execute_sql_insertion(self, query: str, params: tuple) -> None:
        """
        Executes an SQL insertion with the provided parameter tuple using the general query runner.

        Args:
            query (str): SQL query.
            params (tuple): Tuple with placeholders' values.
        
        Returns:
            None:
        """
        self.run_query(query, params=params)
    
    def execute_many_sql_insertion(self, query: str, data: list[tuple]) -> None:
        """
        Handles many SQL insertions with a list of tuples of parameters and runs those with the general query runner.

        Args:
            query (str): SQL query.
            data (list[tuple]): List of data to add.
        
        Returns:
            None:
        """
        self.run_query(query, params=data, many=True)
    
    def execute_query(self, query: str) -> list[tuple]:
        """
        Handles an SQL query and retrieves results with the general query runner.

        Args:
            query (str): SQL query.

        Returns:
            list: SQL query's result.
        """
        result: list[tuple] = self.run_query(query, fetch=True)
        return result
    
    def execute_query_with_columns(self, query: str, params: tuple) -> tuple[list[tuple], list[str]]:
        """
        Handles an SQL query with the general query runner and retrieves both results columns' names and results.

        Args:
            query (str): SQL query.
            params (tuple): Tuple with placeholders' values.
        
        Returns:
            tuple: Query results and columns' names.
        """
        result, columns = self.run_query(query, params=params, fetch=True, columns=True)
        return result, columns
    
    def get_schema(self) -> str:
        """
        Retrieves the database schema, listing each table and its corresponding columns.

        Returns:
            list (dict[str, str]): A list of dictionaries containing table and column names,
                                  structured for frontend display.
        """
        schema = get_database_schema(self.conn)
        # print(f"Database schema retrieved: {schema}")
        return schema
    
    def close_connection(self) -> None:
        """
        Closes the database connection.

        Returns:
            None
        """
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")
        else:
            logger.warning("No database connection to close.")
    
    def connection_rollback(self) -> None:
        """
        Rolls back the current transaction in case of an error.

        Returns:
            None
        """
        if self.conn:
            self.conn.rollback()
            logger.info("Database transaction rolled back.")
        else:
            logger.warning("No database connection to roll back.")
