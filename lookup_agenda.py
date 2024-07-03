import argparse
from datetime import datetime
import import_agenda
import textwrap

# Parse command line arguments and return the required column and value 
def parseArguments(): 
    parser = argparse.ArgumentParser(description="lookup conditions")
    parser.add_argument("column", type=str, help="column name to lookup")
    parser.add_argument("value", type=str, nargs=argparse.REMAINDER, help="value to lookup")
    args = parser.parse_args()
    args.value =  ' '.join(args.value)
    
    # Format the value if it is date or time 
    if (args.column == 'time_start' or args.column == 'time_end'):
       args.value =  datetime.strptime(args.value, '%I:%M %p').strftime('%H:%M:%S')
    if (args.column == 'date'):
        args.value = datetime.strptime(args.value, '%m/%d/%Y').strftime('%Y-%m-%d') 

    args.value = args.value.replace("'", "''")
    return args.column, args.value


# Retrieve records that match the lookup conditions provided (column and value)
def retrieve_records(data):
    column, value = parseArguments()

    # If looking for a speaker, retrieve session ids and subsession ids of the required speaker from the speakers table
    if (column == "speaker"):
        speakers_result = import_agenda.speakers.select(['session_id', 'subsession_id', 'speaker'], {column: value})
        # Retrieve all the unique session ids and subsession ids with the speaker
        session_ids = list({sp["session_id"] for sp in speakers_result if "session_id" in sp})
        subsession_ids = list({sp["subsession_id"] for sp in speakers_result if "subsession_id" in sp})
        sessions_result = []
        subsessions_result = []

        # Retrieve all sessions with the speaker
        for id in session_ids:
            session = import_agenda.sessions.select(['session_id','date', 'time_start', 'time_end', 'title', 'location', 'description'], {"session_id": id})
            sessions_result += session

        # Retrieve all subsessions with the speaker 
        for id in subsession_ids:
            subsession = import_agenda.subsessions.select(['subsession_id','date', 'time_start', 'time_end', 'title', 'location', 'description'], {"subsession_id": id})
            subsessions_result += subsession
              
    else:
        # Retrieve all matching records from sessions and subsessions
        sessions_result = import_agenda.sessions.select(['session_id','date', 'time_start', 'time_end', 'title', 'location', 'description'], {column: value})
        subsessions_result = import_agenda.subsessions.select(['subsession_id','date', 'time_start', 'time_end', 'title', 'location', 'description'], {column: value})
    
    all_subsessions = []
    related_subsessions = []

    # Iterate through every matched session to include all its subsessions and to retrieve the correspodning speakers
    for result in sessions_result:
        id = result['session_id']

        # Convert time and data values from DATE and TIME types back to input format (HH:MM AM/PM) and (MM/DD/YYYY)
        start_time = result['time_start']
        result['time_start'] = datetime.strptime(start_time, "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
        end_time = result['time_end']
        result['time_end'] = datetime.strptime(end_time, "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
        result_date = result['date']
        result['date'] = datetime.strptime(result_date, "%Y-%m-%d").strftime("%m/%d/%Y")

        # Retrieve all the speakers for the session, separate them with commas and add them to the session data
        related_speakers = import_agenda.speakers.select(['speaker'], {'session_id': id})
        speakers_list = []
        for item in related_speakers:
            speakers_list.append(item['speaker'])
        speakers_string = ', '.join(speakers_list)
        related_speakers = {'speakers': speakers_string}
        result.update(related_speakers)
        result.update({'type': "Session"})
        data.append(format_data(result))
        

        # Retrieve all the subsessions for the matched session
        related_subsessions = import_agenda.subsessions.select(['subsession_id','date', 'time_start', 'time_end', 'title', 'location', 'description'], {'session_id': id})
        title = result['title']
        # Iterate through every subsession to update the time and date formats and retrieve the corresponding speakers
        for result in related_subsessions:
            all_subsessions.append(result)
            id = result['subsession_id']
            # Convert time and data values from DATE and TIME types back to input format (HH:MM AM/PM) and (MM/DD/YYYY)
            start_time = result['time_start']
            result['time_start'] = datetime.strptime(start_time, "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
            end_time = result['time_end']
            result['time_end'] = datetime.strptime(end_time, "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
            result_date = result['date']
            result['date'] = datetime.strptime(result_date, "%Y-%m-%d").strftime("%m/%d/%Y")

            # Retrieve all the speakers for the subsessions, separate them with commas and add them to the subsession data
            related_speakers = import_agenda.speakers.select(['speaker'], {'subsession_id': id})
            speakers_list = []
            for item in related_speakers:
                speakers_list.append(item['speaker'])
            speakers_string = ', '.join(speakers_list)
            related_speakers = {'speakers': speakers_string}
            result.update(related_speakers)
            result.update({'type': "Subsession of " + title})
            data.append(format_data(result))

    # Iterate through the matched subsessions to update the time and date formats and retrieve the corresponding speakers
    for result in subsessions_result:
        # Only add the subsession to the final output if it is not already included from the subsessions of the matched sessions
        if (result not in all_subsessions):
            id = result['subsession_id']

            # Convert time and data values from DATE and TIME types back to input format (HH:MM AM/PM) and (MM/DD/YYYY)
            start_time = result['time_start']
            result['time_start'] = datetime.strptime(start_time, "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
            end_time = result['time_end']
            result['time_end'] = datetime.strptime(end_time, "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
            result_date = result['date']
            result['date'] = datetime.strptime(result_date, "%Y-%m-%d").strftime("%m/%d/%Y")

            # Retrieve all the speakers for the session, separate them with commas and add them to the session data
            related_speakers = import_agenda.speakers.select(['speaker'], {'subsession_id': id})
            speakers_list = []
            for item in related_speakers:
                speakers_list.append(item['speaker'])
            speakers_string = ', '.join(speakers_list)
            related_speakers = {'speakers': speakers_string}
            result.update(related_speakers)
            result.update({'type': "Subsession"})
            data.append(format_data(result))
    
    #Close all connections
    import_agenda.speakers.close()
    import_agenda.sessions.close()
    import_agenda.subsessions.close()

# Remove session_id and subsession_id from final output
def format_data(dict):
    dict.pop('session_id', None)
    dict.pop('subsession_id', None)
    return dict

def print_results(data):
    #Define widths for each field's column in output
    col_widths = {
        "date": 12,
        "time_start": 10,
        "time_end": 10,
        "title": 25,
        "location": 20,
        "description": 30,
        "speakers": 15,
        "type": 10
    }

    # Define header with the column names and print
    header = f"{'date'.ljust(col_widths['date'])} | {'time_start'.ljust(col_widths['time_start'])} | {'time_end'.ljust(col_widths['time_end'])} | {'title'.ljust(col_widths['title'])} | {'location'.ljust(col_widths['location'])} | {'description'.ljust(col_widths['description'])} | {'speakers'.ljust(col_widths['speakers'])} | {'type'.ljust(col_widths['type'])}"
    print(header)   
    print("-" * len(header))

# Print each data row
    for row in data:
        format_row(row, col_widths, header)

# Function to format a row
def format_row(row, col_widths, header):
        #  Wrap the content in each column to the specified width
        wrapped_columns = {key: textwrap.wrap(str(value), width = col_widths[key]) for key, value in row.items()}
        max_lines = max(len(v) for v in wrapped_columns.values())
    
        # Print each line of the row with columns appropriately aligned
        for i in range(max_lines):
            line_parts = []
            for key in col_widths.keys():
                value_lines = wrapped_columns.get(key, [])
                line_parts.append(value_lines[i] if i < len(value_lines) else "")
            line = " | ".join(part.ljust(col_widths[key]) for key, part in zip(col_widths.keys(), line_parts))
            print(line)
        print("-" * len(header))

if __name__ == "__main__":
    data = []
    retrieve_records(data)
    if (len(data) > 0) :
        print_results(data)
    else:
        print("No matched results")