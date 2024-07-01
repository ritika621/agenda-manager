import xlrd
import argparse
from db_table import db_table
from datetime import datetime

#defining SQLite Database table schema(s) 
#session_id in subsessions and speakers tables acts as a foreign key to reference the id of the session the record references
#subsession_id in speakers table acts a foreign key to reference the id of the subsession it references
sessions = db_table("sessions", { "session_id": "INTEGER PRIMARY KEY AUTOINCREMENT", "date": "DATE NOT NULL", "time_start": "TIME NOT NULL", "time_end": "TIME NOT NULL" , "title": "TEXT NOT NULL", "location" : "TEXT", "description" : "TEXT" })
subsessions = db_table("subsessions", { "subsession_id": "INTEGER PRIMARY KEY AUTOINCREMENT", "session_id": "INTEGER NOT NULL", "date": "DATE NOT NULL", "time_start": "TIME NOT NULL", "time_end": "TIME NOT NULL" , "title": "TEXT NOT NULL", "location" : "TEXT", "description" : "TEXT" })
speakers = db_table("speakers", {"speaker_id": "INTEGER PRIMARY KEY AUTOINCREMENT", "session_id" : "INTEGER NOT NULL", "subsession_id": "INTEGER NOT NULL", "speaker": "TEXT"})


#opening an excel file
def readExcelFile(): 
    parser = argparse.ArgumentParser(description="Open and store an xls file from terminal.")
    parser.add_argument("filename", type=str, help="The name of the file to open")
    args = parser.parse_args()
    book = xlrd.open_workbook(args.filename)
    return book


def storeParsedContent():
    #retrieve data from the excel file and store it
    bookData = readExcelFile()
    bookData = bookData.sheet_by_index(0)
    sessionCount = 0
    subsessionCount = 0

    #Parsing row by row for each record in the table
    for rx in range(15, bookData.nrows):
        #extracting all fields and converting them into desired format if needed
        currentRow = bookData.row(rx)
        date = currentRow[0].value
        dateFormatted = datetime.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')
        startTime = currentRow[1].value
        startTimeFormat = datetime.strptime(startTime, '%I:%M %p').strftime('%H:%M:%S')
        endTime = currentRow[2].value
        endTimeFormat = datetime.strptime(endTime, '%I:%M %p').strftime('%H:%M:%S')
        sessionType = currentRow[3].value
        #escaping ' as it is a delimiter in SQL
        sessionTitle = currentRow[4].value
        sessionTitle = sessionTitle.replace("'", "''")
        location = currentRow[5].value
        location = location.replace("'", "''")
        description = currentRow[6].value
        description = description.replace("'", "''")
        #splitting up the speakers and storing in a list of speakers
        speakersSplit = currentRow[7].value.split(';')
        speakersList = [name.strip() for name in speakersSplit]
        
        #inserting in sessions table
        if sessionType == "Session":
            sessionCount += 1
            sessions.insert({"date": dateFormatted, "time_start": startTimeFormat, "time_end": endTimeFormat, 
                             "title": sessionTitle, "location" : location,  "description": description})
            for s in speakersList:
                if(s == ''):
                    continue
                #escaping ' as it is a delimiter in SQL
                s = s.replace("'", "''")
                #inserting each speaker into speakers table with corresponding session_id
                speakers.insert({"session_id": sessionCount, "subsession_id": None, "speaker": s})
        
        #inserting in subsessions table
        else:
            subsessionCount += 1
            subsessions.insert({"session_id":sessionCount,"date": dateFormatted, "time_start": startTimeFormat, "time_end": endTimeFormat, 
                             "title": sessionTitle, "location" : location,  "description": description})
            for s in speakersList:
                if(s == ''):
                    continue
                #escaping ' as it is a delimiter in SQL
                s = s.replace("'", "''")
                #inserting each speaker into speakers table with corresponding subsession_id
                speakers.insert({"session_id": None, "subsession_id": subsessionCount, "speaker": s})

if __name__ == "__main__":
    storeParsedContent()