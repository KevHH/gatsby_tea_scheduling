from datetime import datetime

def get_talk_dates(start_date, end_date):
    """Returns available talk dates. Currently set to return Mondays, Tuesdays, and Thursdays between given dates

    Parameters
    ----------
    start_date : datetime.datetime object
        The start date for scheduling
    end_date : datetime.datetime object
        The end date for scheduling
        
    Returns
    -------
    talk_dates : list of datetime.datetime object
    """
    print("")

def scheduling(start_date, end_date, people):
    """Returns a schedule for research and tea talks

    Parameters
    ----------
    start_date : datetime.datetime object
        The start date for scheduling
    end_date : datetime.datetime object
        The end date for scheduling
    people : list of dictionaries with the following keys
        'id': string, representing notion id of the person
        'away_dates': list of 2-tuples of datetime.datetime objects representing start and end of away dates (inclusive)  

    Returns
    -------
    schedule: list of dictionaries with the following keys
        'date': datetime.datetime object representing date of the talk
        'type': either 'R' or 'T' representing research talk or tea talk
        'presenter': notion id for the person presenting
        'tea': notion id for the person doing tea preparation
    """
    print("")