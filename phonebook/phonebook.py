# phonebook_app.py
import psycopg2
from config import load_config
import csv
import sys

def db_connect():
    """ Establish a database connection """
    config = load_config()
    try:
        conn = psycopg2.connect(**config)
        return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"Database connection error: {error}")
        sys.exit(1)

# --- Insert Data (Console Input) ---
def insert_contact_from_console():
    """ Insert one contact from user console input """
    print("\n--- Entering new contact from console ---")
    first_name = input("Enter first name: ")
    last_name = input("Enter last name (optional): ")
    phone_number = input("Enter phone number: ")

    sql = """INSERT INTO contacts(first_name, last_name, phone_number)
             VALUES(%s, %s, %s) RETURNING contact_id;"""
    
    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (first_name, last_name if last_name else None, phone_number))
                contact_id = cur.fetchone()[0]
                conn.commit()
                print(f"Inserted contact ID: {contact_id}")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Insert failed: {error}")

# --- Insert Data (CSV File Input) ---
def insert_contacts_from_csv(csv_file_path):
    """ Upload data from a CSV file into the PhoneBook """
    sql = """INSERT INTO contacts(first_name, last_name, phone_number)
             VALUES(%s, %s, %s);"""
    
    contacts_to_insert = []
    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # Skip header row
            for row in reader:
                contacts_to_insert.append(tuple(row))
    except IOError as e:
        print(f"Error reading CSV file: {e}")
        return

    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(sql, contacts_to_insert)
            conn.commit()
            print(f"Successfully inserted {len(contacts_to_insert)} contacts from CSV.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"CSV upload failed: {error}")

# --- Update Data ---
def update_contact_phone(target_name, new_phone_number):
    """ Update a contact's phone number by first name """
    sql = """UPDATE contacts SET phone_number = %s WHERE first_name = %s;"""
    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (new_phone_number, target_name))
                conn.commit()
                print(f"Updated {cur.rowcount} record(s) for {target_name}.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Update failed: {error}")

# --- Query Data (Read) ---
def query_contacts(filter_name=None, filter_phone=None):
    """ Query data with optional filters """
    sql = "SELECT first_name, last_name, phone_number FROM contacts WHERE TRUE"
    params = []
    
    if filter_name:
        sql += " AND first_name ILIKE %s"
        params.append(f'%{filter_name}%')
        
    if filter_phone:
        sql += " AND phone_number ILIKE %s"
        params.append(f'%{filter_phone}%')

    sql += " ORDER BY last_name, first_name;"

    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                rows = cur.fetchall()
                print(f"\nFound {len(rows)} matching contacts:")
                for row in rows:
                    print(row)
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Query failed: {error}")

# --- Delete Data ---
def delete_contact(target_value, by_phone=False):
    """ Delete a contact by username (first_name) or phone number """
    if by_phone:
        sql = "DELETE FROM contacts WHERE phone_number = %s;"
    else:
        sql = "DELETE FROM contacts WHERE first_name = %s;"
        
    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (target_value,))
                conn.commit()
                print(f"Deleted {cur.rowcount} record(s).")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Deletion failed: {error}")


if __name__ == '__main__':
    # You must create contacts.csv file first for this to work
    print("--- 1. Inserting data from CSV ---")
    insert_contacts_from_csv('contacts.csv')

    print("\n--- 2. Inserting one contact from console (follow prompts) ---")
    # UNCOMMENT THE NEXT LINE TO TEST CONSOLE INPUT INTERACTIVELY
    # insert_contact_from_console() 

    print("\n--- 3. Querying all data ---")
    query_contacts()

    print("\n--- 4. Updating Zhansiya's phone number ---")
    update_contact_phone('Zhansiya', '11111111')
    query_contacts(filter_name='Bob')

    print("\n--- 5. Deleting Erke by name ---")
    delete_contact('Erke', by_phone=False)
    query_contacts() # Verify Alice is gone
