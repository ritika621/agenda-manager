import argparse
from datetime import datetime
import import_agenda
import textwrap


# Create a new table by performing a left join with sessions and speakers
query = "CREATE TABLE IF NOT EXISTS sessions_results AS SELECT sessions.*, GROUP_CONCAT(speakers.speaker, ', ') AS speaker FROM sessions LEFT JOIN speakers ON sessions.session_id = speakers.session_id GROUP BY sessions.session_id;"
sessions_results = import_agenda.sessions.execute_query(True, query, ['session_id','date', 'time_start', 'time_end', 'title', 'location', 'description', 'speaker'])

# Create a new table by performing an inner join with subsessions and speakers
query = "CREATE TABLE IF NOT EXISTS subsessions_results AS SELECT subsessions.*, GROUP_CONCAT(speakers.speaker, ', ') AS speaker FROM subsessions LEFT JOIN speakers ON subsessions.subsession_id = speakers.subsession_id GROUP BY subsessions.subsession_id;"
subsessions_results = import_agenda.subsessions.execute_query(True, query, ['subsession_id', 'session_id', 'date', 'time_start', 'time_end', 'title', 'location', 'description', 'speaker'])

# Parse command line arguments and return the required column and value 
def parse_arguments(): 
    parser = argparse.ArgumentParser(description="lookup conditions")
    parser.add_argument("column", type=str, help="column name to lookup")
    parser.add_argument("value", type=str, nargs=argparse.REMAINDER, help="value to lookup")
    args = parser.parse_args()
    args.value = ' '.join(args.value)

    # Format the value if it is date or time to search through database
    if (args.column == 'time_start' or args.column == 'time_end'):
       args.value =  datetime.strptime(args.value, '%I:%M %p').strftime('%H:%M:%S')
    if(args.column == 'date'):
        args.value = datetime.strptime(args.value, '%m/%d/%Y').strftime('%Y-%m-%d') 

    args.value = args.value.replace("'", "''")
    return args.column, args.value


# Retrieve records that match the lookup conditions provided (column and value)
def retrieve_records():
    column, value = parse_arguments()
   
    # Create a new table that matches every session and subsession to the column and value and checks for the subsessions of every matched session
    if (column == 'speaker'):
        query = "CREATE TABLE IF NOT EXISTS all_sessions AS SELECT NULL AS subsession_id, sessions_results.*, NULL AS type FROM sessions_results WHERE " + column +  " LIKE '%" + value + "%' UNION ALL SELECT subsessions_results.*, NULL AS type  FROM subsessions_results WHERE session_id IN (SELECT session_id FROM sessions_results WHERE " + column + " LIKE '%" + value + "%') OR " + column +  " LIKE '%" + value + "%';"
    else:
        query = "CREATE TABLE IF NOT EXISTS all_sessions AS SELECT NULL AS subsession_id, sessions_results.*, NULL AS type FROM sessions_results WHERE " + column +  " = '" + value + "' UNION ALL SELECT subsessions_results.*, NULL AS type  FROM subsessions_results WHERE session_id IN (SELECT session_id FROM sessions_results WHERE " +  column +  " = '" + value + "') OR " + column +  " = '" + value + "';"
    combined_results = sessions_results.execute_query(True, query, ['subsession_id', 'session_id', 'date', 'time_start', 'time_end', 'title', 'location', 'description', 'speaker', 'type'])
    
    # Update type for a session or a Subsession of a matched Session
    query = "UPDATE all_sessions SET type = 'Session' WHERE subsession_id IS NULL;"
    all_sessions = combined_results.execute_query(False, query, ['subsession_id', 'session_id', 'date', 'time_start', 'time_end', 'title', 'location', 'description', 'speaker', 'type'])
  
    # Update type for subsessions of matched sessions
    query = "UPDATE all_sessions SET type = 'Subsession of ' || (SELECT title FROM all_sessions AS s WHERE s.session_id = all_sessions.session_id AND s.subsession_id IS NULL) WHERE subsession_id IS NOT NULL;"
    all_sessions = combined_results.execute_query(False, query, ['subsession_id', 'session_id', 'date', 'time_start', 'time_end', 'title', 'location', 'description', 'speaker', 'type'])

    # Update type for matched subsessions
    query = "UPDATE all_sessions SET type = 'Subsession' WHERE subsession_id IS NOT NULL AND session_id NOT IN (SELECT session_id FROM all_sessions WHERE subsession_id IS NULL);"
    all_sessions = combined_results.execute_query(False, query, ['subsession_id', 'session_id', 'date', 'time_start', 'time_end', 'title', 'location', 'description', 'speaker', 'type'])
    
    all_sessions = combined_results.select()

    # Delete all_sessions as it is a temporary table and will change everytime we run this file
    query = "DROP TABLE all_sessions"
    combined_results.execute_query(False, query, ['subsession_id', 'session_id', 'date', 'time_start', 'time_end', 'title', 'location', 'description', 'speaker'])
    
    # Format each matched record
    for dict in all_sessions:
       format_data(dict)

    # Close all connections
    import_agenda.sessions.close()
    import_agenda.subsessions.close()
    combined_results.close() 
    sessions_results.close()
    subsessions_results.close()

    return all_sessions


# Remove session_id and subsession_id from final output and convert date and time type data back into the input format
def format_data(dict):
    dict.pop('session_id', None)
    dict.pop('subsession_id', None)
    dict['time_start'] = datetime.strptime(dict['time_start'], "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
    dict['time_end'] = datetime.strptime( dict['time_end'], "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
    dict['date'] = datetime.strptime(dict['date'], "%Y-%m-%d").strftime("%m/%d/%Y")
    return dict


def print_results(data):
    # Define widths for each field's column in output
    colWidths = {
        "date": 12,
        "time_start": 10,
        "time_end": 10,
        "title": 25,
        "location": 20,
        "description": 30,
        "speaker": 15,
        "type": 10
    }

    # Define header with the column names and print
    header = f"{'date'.ljust(colWidths['date'])} | {'time_start'.ljust(colWidths['time_start'])} | {'time_end'.ljust(colWidths['time_end'])} | {'title'.ljust(colWidths['title'])} | {'location'.ljust(colWidths['location'])} | {'description'.ljust(colWidths['description'])} | {'speaker'.ljust(colWidths['speaker'])} | {'type'.ljust(colWidths['type'])}"
    print(header)   
    print("-" * len(header))

# Print each data row
    for row in data:
        formatRow(row, colWidths, header)


# Function to format a row
def formatRow(row, colWidths, header):
        #  Wrap the content in each column to the specified width
        wrappedColumns = {key: textwrap.wrap(str(value), width = colWidths[key]) for key, value in row.items()}
        maxLines = max(len(v) for v in wrappedColumns.values())
    
        # Print each line of the row with columns appropriately aligned
        for i in range(maxLines):
            lineParts = []
            for key in colWidths.keys():
                value_lines = wrappedColumns.get(key, [])
                lineParts.append(value_lines[i] if i < len(value_lines) else "")
            line = " | ".join(part.ljust(colWidths[key]) for key, part in zip(colWidths.keys(), lineParts))
            print(line)
        print("-" * len(header))


if __name__ == "__main__":
    data = []
    data = retrieve_records()
    if (len(data) > 0) :
        print_results(data)
    else:
        print("No matched results")