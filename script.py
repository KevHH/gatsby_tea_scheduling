from datetime import datetime

def scheduling(empty_schedule, people):
    """Returns a schedule for research and tea talks

    Parameters
    ----------
    empty_schedule : list of dictionaries with the following keys
        'date': datetime.datetime object representing date of the talk
        'type': either 'R' or 'T' representing research talk or tea talk
        'id': string, representing notion id of the talk
    people : list of dictionaries with the following keys
        'id': string, representing notion id of the person
        'away_dates': list of 2-tuples of datetime.datetime objects representing start and end of away dates (inclusive)  

    Returns
    -------
    filled_schedule: list of dictionaries with the following keys
        'date': datetime.datetime object representing date of the talk
        'type': either 'R' or 'T' representing research talk or tea talk
        'id': string, representing notion id of the talk
        'presenter': notion id for the person presenting
        'tea': notion id for the person doing tea preparation
    """
    
    filled_schedule = []
    for talk in empty_schedule:
        filled_schedule.append({'date':talk['date'],
                                'type':talk['type'],
                                'id':talk['id'],
                                'presenter':people[0]['id'],
                                'tea':people[0]['id']  
                                })
    return filled_schedule