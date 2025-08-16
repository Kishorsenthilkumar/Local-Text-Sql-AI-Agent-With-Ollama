    # create_db.py

import sqlite3
import os

DB_NAME = 'my_test_database.db'
DB_PATH = os.path.join(os.path.dirname(__file__), DB_NAME)


def create_and_populate_db():
        """
        Creates a SQLite database file and populates it with sample data.
        """
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            print(f"Connected to database: {DB_PATH}")

            # --- Create Employees table ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Employees (
                    EmployeeID INTEGER PRIMARY KEY,
                    FirstName TEXT NOT NULL,
                    LastName TEXT NOT NULL,
                    DepartmentID INTEGER,
                    Salary REAL,
                    FOREIGN KEY (DepartmentID) REFERENCES Departments(DepartmentID)
                );
            ''')
            print("Table 'Employees' created or already exists.")

            # --- Create Departments table ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Departments (
                    DepartmentID INTEGER PRIMARY KEY,
                    DepartmentName TEXT NOT NULL,
                    Location TEXT
                );
            ''')
            print("Table 'Departments' created or already exists.")

            # --- Insert sample data into Departments ---
            departments_data = [
                (1, 'Sales', 'New York'),
                (2, 'Marketing', 'Los Angeles'),
                (3, 'Engineering', 'San Francisco'),
                (4, 'Human Resources', 'New York')
            ]
            cursor.executemany("INSERT OR IGNORE INTO Departments (DepartmentID, DepartmentName, Location) VALUES (?, ?, ?)", departments_data)
            print("Sample data inserted into 'Departments'.")

            # --- Insert sample data into Employees ---
            employees_data = [
                (101, 'Alice', 'Smith', 1, 60000.00),
                (102, 'Bob', 'Johnson', 2, 75000.00),
                (103, 'Charlie', 'Brown', 1, 62000.00),
                (104, 'Diana', 'Prince', 3, 90000.00),
                (105, 'Eve', 'Adams', 4, 55000.00),
                (106, 'Frank', 'White', 3, 88000.00)
            ]
            cursor.executemany("INSERT OR IGNORE INTO Employees (EmployeeID, FirstName, LastName, DepartmentID, Salary) VALUES (?, ?, ?, ?, ?)", employees_data)
            print("Sample data inserted into 'Employees'.")

            conn.commit()
            print("Database setup complete!")

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    create_and_populate_db()