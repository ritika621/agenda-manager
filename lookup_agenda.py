import argparse
from datetime import datetime
import import_agenda


#parse command line arguments and return the required column and value 
def parseArguments(): 
    parser = argparse.ArgumentParser(description="lookup conditions")
    parser.add_argument("column", type=str, help="column name to lookup")
    parser.add_argument("value", type=str, nargs=argparse.REMAINDER, help="value to lookup")
    args = parser.parse_args()
    args.value =  ' '.join(args.value)
    
    #format the value if it is date or time 
    if (args.column == 'time_start' or args.column == 'time_end'):
       args.value =  datetime.strptime(args.value, '%I:%M %p').strftime('%H:%M:%S')
    if(args.column == 'date'):
        args.value = datetime.strptime(args.value, '%m/%d/%Y').strftime('%Y-%m-%d') 

    return args.column, args.value


#retrieve records that match the lookup conditions provided (column and value)
def retrieveRecords(data):
    column, value = parseArguments()

    #if looking for a speaker, retrieve session ids and subsession ids of the required speaker from the speakers table
    if (column == "speaker"):
        speakersResult = import_agenda.speakers.select(['session_id', 'subsession_id', 'speaker'], {column: value})
        #retrieve all the unique session ids and subsession ids with the speaker
        session_ids = list({sp["session_id"] for sp in speakersResult if "session_id" in sp})
        subsession_ids = list({sp["subsession_id"] for sp in speakersResult if "subsession_id" in sp})
        sessionsResult = []
        subsessionsResult = []

        #retrieve all sessions with the speaker
        for id in session_ids:
            session = import_agenda.sessions.select(['session_id','date', 'time_start', 'time_end', 'title', 'location', 'description'], {"session_id": id})
            sessionsResult += session

        #retrieve all subsessions with the speaker 
        for id in subsession_ids:
            subsession = import_agenda.subsessions.select(['subsession_id','date', 'time_start', 'time_end', 'title', 'location', 'description'], {"subsession_id": id})
            subsessionsResult += subsession
              
    else:
        #retrieve all matching records from sessions and subsessions
        sessionsResult = import_agenda.sessions.select(['session_id','date', 'time_start', 'time_end', 'title', 'location', 'description'], {column: value})
        subsessionsResult = import_agenda.subsessions.select(['subsession_id','date', 'time_start', 'time_end', 'title', 'location', 'description'], {column: value})
    
    allSubsessions = []
    relatedSubsessions = []

    #iterate through every matched session to include all its subsessions and to retrieve the correspodning speakers
    for result in sessionsResult:
        id = result['session_id']

        #convert time and data values from DATE and TIME types back to input format (HH:MM AM/PM) and (MM/DD/YYYY)
        startTime = result['time_start']
        result['time_start'] = datetime.strptime(startTime, "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
        endTime = result['time_end']
        result['time_end'] = datetime.strptime(endTime, "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
        resultDate = result['date']
        result['date'] = datetime.strptime(resultDate, "%Y-%m-%d").strftime("%m/%d/%Y")

        #retrieve all the speakers for the session, separate them with commas and add them to the session data
        relatedSpeakers = import_agenda.speakers.select(['speaker'], {'session_id': id})
        speakers_list = []
        for item in relatedSpeakers:
            speakers_list.append(item['speaker'])
        speakers_string = ', '.join(speakers_list)
        relatedSpeakers = {'speakers': speakers_string}
        result.update(relatedSpeakers)
        data.append(formatRow(result))
        

        #retrieve all the subsessions for the matched session
        relatedSubsessions = import_agenda.subsessions.select(['subsession_id','date', 'time_start', 'time_end', 'title', 'location', 'description'], {'session_id': id})

       #iterate through every subsession to update the time and date formats and retrieve the corresponding speakers
        for result in relatedSubsessions:
            allSubsessions.append(result)
            id = result['subsession_id']
            #convert time and data values from DATE and TIME types back to input format (HH:MM AM/PM) and (MM/DD/YYYY)
            startTime = result['time_start']
            result['time_start'] = datetime.strptime(startTime, "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
            endTime = result['time_end']
            result['time_end'] = datetime.strptime(endTime, "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
            resultDate = result['date']
            result['date'] = datetime.strptime(resultDate, "%Y-%m-%d").strftime("%m/%d/%Y")

            #retrieve all the speakers for the subsessions, separate them with commas and add them to the subsession data
            relatedSpeakers = import_agenda.speakers.select(['speaker'], {'subsession_id': id})
            speakers_list = []
            for item in relatedSpeakers:
                speakers_list.append(item['speaker'])
            speakers_string = ', '.join(speakers_list)
            relatedSpeakers = {'speakers': speakers_string}
            result.update(relatedSpeakers)
            data.append(formatRow(result))

    #iterate through the matched subsessions to update the time and date formats and retrieve the corresponding speakers
    for result in subsessionsResult:
        #only add the subsession to the final output if it is not already included from the subsessions of the matched sessions
        if (result not in allSubsessions):
            id = result['subsession_id']

            #convert time and data values from DATE and TIME types back to input format (HH:MM AM/PM) and (MM/DD/YYYY)
            startTime = result['time_start']
            result['time_start'] = datetime.strptime(startTime, "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
            endTime = result['time_end']
            result['time_end'] = datetime.strptime(endTime, "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
            resultDate = result['date']
            result['date'] = datetime.strptime(resultDate, "%Y-%m-%d").strftime("%m/%d/%Y")

            #retrieve all the speakers for the session, separate them with commas and add them to the session data
            relatedSpeakers = import_agenda.speakers.select(['speaker'], {'subsession_id': id})
            speakers_list = []
            for item in relatedSpeakers:
                speakers_list.append(item['speaker'])
            speakers_string = ', '.join(speakers_list)
            relatedSpeakers = {'speakers': speakers_string}
            result.update(relatedSpeakers)
            data.append(formatRow(result))

#remove session_id and subsession_id from final output
def formatRow(dict):
    dict.pop('session_id', None)
    dict.pop('subsession_id', None)
    return dict



if __name__ == "__main__":
    data = []
    retrieveRecords(data)