import pyodbc

# Azure SQL connection string
connection_string = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=tcp:keyboarddb.database.windows.net,1433;"
    "Database=keyboarddb;"
    "Uid=CloudSAd21ee598;"
    "Pwd=Tellron1632;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

conn = None
cursor = None

try:
    # Connect to the database
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    print("✅ Connected to the database.")

    # Step 1: Create the table if it doesn't exist
    cursor.execute("""
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Animals'
    )
    BEGIN
        CREATE TABLE Animals (
            ID INT IDENTITY(1,1) PRIMARY KEY,
            Name VARCHAR(100)
        )
    END
    """)
    conn.commit()
    print("✅ Checked or created 'Animals' table.")

    # Step 2: Insert data
    animals = ['Dog', 'Cat']
    for animal in animals:
        cursor.execute("INSERT INTO Animals (Name) VALUES (?)", animal)
    conn.commit()
    print("✅ Inserted animals into table.")

    # Step 3: Fetch and print all data
    cursor.execute("SELECT * FROM Animals")
    rows = cursor.fetchall()
    print("\n📋 All animals in the database:")
    for row in rows:
        print(f"ID: {row.ID}, Name: {row.Name}")

except Exception as e:
    print("❌ Error:", e)

finally:
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()
    print("\n🔒 Connection closed.")
