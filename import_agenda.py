import xlrd
import argparse
from db_table import db_table

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

