import xlrd
import argparse
from db_table import db_table
from datetime import datetime

# Define SQLite Database table schema(s) 
# session_id in subsessions and speakers tables acts as a foreign key to reference the id of the session the record references
# subsession_id in speakers table acts a foreign key to reference the id of the subsession it references
sessions = db_table("sessions", { "session_id": "INTEGER PRIMARY KEY AUTOINCREMENT", "date": "DATE NOT NULL", "time_start": "TIME NOT NULL", "time_end": "TIME NOT NULL" , "title": "TEXT NOT NULL", "location" : "TEXT", "description" : "TEXT" })
subsessions = db_table("subsessions", { "subsession_id": "INTEGER PRIMARY KEY AUTOINCREMENT", "session_id": "INTEGER NOT NULL", "date": "DATE NOT NULL", "time_start": "TIME NOT NULL", "time_end": "TIME NOT NULL" , "title": "TEXT NOT NULL", "location" : "TEXT", "description" : "TEXT" })
speakers = db_table("speakers", {"speaker_id": "INTEGER PRIMARY KEY AUTOINCREMENT", "session_id" : "INTEGER NOT NULL", "subsession_id": "INTEGER NOT NULL", "speaker": "TEXT"})

# Open an excel file
def read_excel_file(): 
    parser = argparse.ArgumentParser(description="Open and store an xls file from terminal.")
    parser.add_argument("filename", type=str, help="The name of the file to open")
    args = parser.parse_args()
    book = xlrd.open_workbook(args.filename)
    return book


def store_parsed_content():
    # Retrieve data from the excel file and store it
    book_data = read_excel_file()
    book_data = book_data.sheet_by_index(0)
    session_count = 0
    subsession_count = 0

    # Parse row by row for each record in the table
    for rx in range(15, book_data.nrows):
        # Extract all fields and convert them into desired format if needed
        current_row = book_data.row(rx)
        date = current_row[0].value
        date_formatted = datetime.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')
        start_time = current_row[1].value
        start_time_format = datetime.strptime(start_time, '%I:%M %p').strftime('%H:%M:%S')
        end_time = current_row[2].value
        end_time_format = datetime.strptime(end_time, '%I:%M %p').strftime('%H:%M:%S')
        session_type = current_row[3].value
        # Escape ' as it is a delimiter in SQL
        session_title = current_row[4].value
        session_title = session_title.replace("'", "''")
        location = current_row[5].value
        location = location.replace("'", "''")
        description = current_row[6].value
        description = description.replace("'", "''")
        # Split up the speakers and store in a list of speakers
        speakers_split = current_row[7].value.split(';')
        speakers_list = [name.strip() for name in speakers_split]
        
        # Insert in sessions table
        if session_type == "Session":
            session_count += 1
            sessions.insert({"date": date_formatted, "time_start": start_time_format, "time_end": end_time_format, 
                             "title": session_title, "location" : location,  "description": description})
            for s in speakers_list:
                if(s == ''):
                    continue
                # Escape ' as it is a delimiter in SQL
                s = s.replace("'", "''")
                # Insert each speaker into speakers table with corresponding session_id
                speakers.insert({"session_id": session_count, "subsession_id": None, "speaker": s})
        
        # Insert in subsessions table
        else:
            subsession_count += 1
            subsessions.insert({"session_id":session_count,"date": date_formatted, "time_start": start_time_format, "time_end": end_time_format, 
                             "title": session_title, "location" : location,  "description": description})
            for s in speakers_list:
                if(s == ''):
                    continue
                # Escape ' as it is a delimiter in SQL
                s = s.replace("'", "''")
                # Insert each speaker into speakers table with corresponding subsession_id
                speakers.insert({"session_id": None, "subsession_id": subsession_count, "speaker": s})

    # Close all connections
    speakers.close()
    sessions.close()
    subsessions.close()


if __name__ == "__main__":
    store_parsed_content()
