# phonebook_app.py (Исправленный и проверенный код)
import psycopg2
from config import load_config
import sys

def db_connect():
    """ Establish a database connection """
    config = load_config()
    try:
        return psycopg2.connect(**config)
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"Database connection error: {error}")
        sys.exit(1)

def search_contacts(pattern):
    print(f"\n--- Searching contacts for pattern: '{pattern}' ---")
    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                # ВЫЗОВ ФУНКЦИИ: Используем SELECT
                cur.execute("SELECT * FROM search_contacts_by_pattern(%s);", (pattern,))
                rows = cur.fetchall()
                for row in rows:
                    print(row)
                print(f"Found {len(rows)} matches.")
    except Exception as e:
        print(f"Search failed: {e}")

def add_or_update_contact(first_name, last_name, phone):
    print(f"\n--- Upserting contact {first_name} ---")
    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                # ВЫЗОВ ПРОЦЕДУРЫ: Используем метод callproc()
                cur.callproc("upsert_contact", (first_name, last_name, phone))
                conn.commit() # Не забываем коммитить изменения
                print("Operation successful.")
    except Exception as e:
        print(f"Operation failed: {e}")

def list_contacts_paged(limit, offset):
    print(f"\n--- Listing contacts (Limit {limit}, Offset {offset}) ---")
    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                # ВЫЗОВ ФУНКЦИИ: Используем SELECT
                cur.execute("SELECT * FROM get_contacts_paged(%s, %s);", (limit, offset))
                rows = cur.fetchall()
                for row in rows:
                    print(row)
                print(f"Found {len(rows)} records.")
    except Exception as e:
        print(f"Pagination query failed: {e}")

def remove_contact(identifier):
    print(f"\n--- Deleting contact by name/phone: {identifier} ---")
    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                # ВЫЗОВ ПРОЦЕДУРЫ: Используем метод callproc()
                cur.callproc("delete_contact_by_identifier", (identifier,))
                conn.commit() # Не забываем коммитить изменения
                print("Deletion successful.")
    except Exception as e:
        print(f"Deletion failed: {e}")
        
def bulk_insert_from_list(contacts_list):
    print(f"\n--- Bulk inserting {len(contacts_list)} contacts using procedure ---")
    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                # ВЫЗОВ ПРОЦЕДУРЫ: Используем метод callproc()
                # Передаем список и пустой список для INOUT параметра
                cur.callproc("bulk_insert_contacts", (contacts_list, []))
                
                # Fetchone() получает результат измененного INOUT параметра
                invalid_data_tuple = cur.fetchone()
                
                if invalid_data_tuple:
                   invalid_data = invalid_data_tuple[0] # Извлекаем сам список из кортежа результата
                   print(f"Inserted valid contacts. Found {len(invalid_data)} invalid records:")
                   for record in invalid_data:
                       print(f"  Invalid record: {record}")
                else:
                    print("Found 0 invalid records.")

                conn.commit()
    except Exception as e:
        print(f"Bulk insert failed: {e}")


if __name__ == '__main__':
    # Clear table for demo run
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM contacts;")
            cur.execute("ALTER SEQUENCE contacts_contact_id_seq RESTART WITH 1;") # Сброс счетчика
            conn.commit()

    # Data to test bulk insert (one invalid phone number 'not_a_phone')
    test_contacts = [
        ('David', 'Lee', '4445556666'),
        ('Eve', 'Adams', '7778889999'),
        ('Frank', 'White', 'not_a_phone') # Invalid phone format
    ]
    
    bulk_insert_from_list(test_contacts)
    list_contacts_paged(limit=10, offset=0)

    search_contacts(pattern='Lee') # Search for David Lee

    add_or_update_contact('Eve', 'Adams', '9999999999') # Update Eve's phone number via Upsert
    list_contacts_paged(limit=10, offset=0) # Verify Eve's update and Frank is gone

    remove_contact('David') # Delete David by first name
    list_contacts_paged(limit=10, offset=0) # Final check (only Eve should remain)