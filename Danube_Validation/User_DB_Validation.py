import pandas as pd
from dotenv import load_dotenv
from source_and_destination_table import userDataBaseValidations
import os
import psycopg2

# Define your database connection parameters
def execute_query(query, connection):
    cur = connection.cursor()
    cur.execute(query)
    result = cur.fetchone()[0]
    cur.close()
    return result

def validate_tables(config1, config2):
    conn = None
    conn1 = None
    df = pd.DataFrame(columns=['Source Table', 'Destination Table', 'Source Count', 'Destination Count', 'Result', 'Comments'], dtype=object)
    try:
        # Connect to the databases
        conn = psycopg2.connect(**config1)
        conn1 = psycopg2.connect(**config2)

        for validation in userDataBaseValidations:
            source_count = execute_query(validation["source_query"], conn1)
            dest_count = execute_query(validation["dest_query"], conn)

            def count_check(source_count, dest_count):
                if source_count == dest_count:
                    return 'count matches'
                else:
                    return 'count mismatch'

            def comment(source_count, dest_count):
                if source_count > dest_count:
                    value = abs(source_count - dest_count)
                    return f'Number of records not migrated : {value}'
                elif source_count < dest_count:
                    return 'Destination count is greater than Source Count'
                else:
                    return 'All records are migrated'

            # Append the validation result to the DataFrame
            new_row = {
                'Source Table': validation['source_table'],
                'Destination Table': validation['dest_table'],
                'Source Count': source_count,
                'Destination Count': dest_count,
                'Result': count_check(source_count, dest_count),  # You can fill this later based on your validation logic
                'Comments': comment(source_count,dest_count)  # You can add comments here
            }
            df = df.append(new_row, ignore_index=True)

    except psycopg2.Error as e:
        print("Error executing SQL statement:", e)
    finally:
        # Close the connections if they are open
        if conn:
            conn.close()
        if conn1:
            conn1.close()

    return df

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    V1_config = {
        'dbname': os.getenv('dbname1'),
        'user': os.getenv('user1'),
        'password': os.getenv('password1'),
        'host': os.getenv('host1'),
        'port': os.getenv('port1')  # Fixed the key for port1
    }

    V2_config = {
        'dbname': os.getenv('dbname2'),
        'user': os.getenv('user2'),
        'password': os.getenv('password2'),
        'host': os.getenv('host2'),
        'port': os.getenv('port2')  # Fixed the key for port2
    }

    # Validate tables
    validation_results = validate_tables(V1_config, V2_config)

    # Display the validation results DataFrame
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(validation_results)

    validation_results.to_csv('D:/DB_Results/user_db.csv', index=False)
