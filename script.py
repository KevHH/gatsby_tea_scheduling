from datetime import timedelta

slot_to_duty = {
    "Research Talk": "presenter",
    "Tea Talk": "presenter",
    "Tea": "tea",
    "MLJC": "presenter",
    "TNJC": "presenter",
    "Coffee Cleaning": "tea"
}

slot_to_talk_types = {
    "Research Talk": ["Research Talk"],
    "Tea Talk": ["Tea Talk"],
    "Tea": ["Research Talk", "Tea Talk", "Just Tea", "Leaving Tea", "External Seminar"],
    "MLJC": ["MLJC"],
    "TNJC": ["TNJC"],
    "Coffee Cleaning": ["Cleaning"]
}

def get_priority_queue(past_schedule, people, eligible_ids, slot_type):
    '''Returns priority queues of people to be scheduled duties for research talk, tea talk and tea    

        slot_type only allowed to take one of these values: "Research Talk", "Tea Talk", "Tea", "MLJC", "TNJC", "Coffee Cleaning"
    '''
    queue = []
    talk_types_to_consider = slot_to_talk_types[slot_type]
    duty_type = slot_to_duty[slot_type]

    # loop through past year's talks from most recent to least; for now, the queue is ordered with least priority -> highest priority
    past_schedule = sorted(past_schedule, key=lambda x: x["date"], reverse=True)
    for past_talk in past_schedule:
        # loop through presenters and add eligible people
        for p_id in past_talk[duty_type]:
            if p_id not in queue and p_id in eligible_ids and past_talk["type"] in talk_types_to_consider:
                queue.append(p_id)
    
    # add anyone who's not found in the past year's talks to the start of the queue
    for p_id in eligible_ids:
        if p_id not in queue:
            queue.append(p_id)
            
    # convert people list to a dictionary of id->victim
    people_dict = { victim["id"]:victim for victim in people}
    
    # reverse order of ids, i.e. highest priority -> lowest priority, and then replace ids with people
    queue_processed = [ people_dict[p_id] for p_id in reversed(queue)]

    return queue_processed

def check_date_contained(talk_date, date_from_list, date_until_list):
    '''Returns a boolean signaling whether the date is contained in any interval in the list
    '''
    for i in range( min( len(date_from_list), len(date_until_list) ) ):
        # if talk date is contained within any date window, return false
        if date_from_list[i] <= talk_date and talk_date <= date_until_list[i]:
            return True
    return False 

def get_whitelist(date, schedule, window_half_width=7):
    '''Get ids of people that should not be scheduled for duties because of existing duties in the given time window
    '''
    # provide a protection window for recent talk presenters
    window = [date - timedelta(days=window_half_width),  
              date + timedelta(days=window_half_width)]
    talks_in_window = filter(lambda x: check_date_contained(x["date"], [window[0]], [window[1]]), schedule)
    whitelist = [person_id for talk in talks_in_window for person_id in talk['presenter']]
    return whitelist

def concat_dict(dict1, dict2):
    return dict(list(dict1.items()) + list(dict2.items()))

def fill_schedule(schedule, queue, slot_type):
    '''Returns a filled schedule that everybody *should be* happy with
        
       slot_type only allowed to take one of these values: "Research Talk", "Tea Talk", "Tea", "MLJC", "TNJC", "Coffee Cleaning"
    '''
    talk_types_to_consider = slot_to_talk_types[slot_type]
    duty_type = slot_to_duty[slot_type]

    # 1. Schedule research talks
    queue = [ concat_dict(victim, {"taken": False}) for victim in queue ]
    for i, talk in enumerate(schedule):
        if talk["to_fill"] and talk["type"] in talk_types_to_consider:
            # get a white list of ids of people to protect from duties
            whitelist = get_whitelist(talk["date"], schedule)
            # schedule
            found_victim = False
            for j, victim in enumerate(queue):
                if (not victim["taken"]) and (victim["id"] not in whitelist):
                    if not check_date_contained(talk["date"], victim["away_from"], victim["away_until"]):
                        found_victim = True
                        queue[j]["taken"] = True
                        schedule[i][duty_type] = [victim["id"]]
                        break
            if not found_victim and (slot_type == "Research Talk" or slot_type == "Tea Talk"):
                schedule[i]["type"] = "Just Tea"

    return schedule

def main(to_fill_schedule, past_schedule, people, query):
    '''Returns a schedule for research and tea talks

    Parameters
    ----------
    to_fill_schedule : list of dictionaries with the following keys
        "date": datetime.datetime object representing date of the talk
        "type": type of talk / duty
        "id": string, representing notion id of the talk
    past_schedule : list of dictionaries with the following keys, containing talks from the past year
        "date": datetime.datetime object representing date of the talk
        "type": type of talk / dut
        "id": string, representing notion id of the talk
        "presenter": list of strings, representing ids of the presenters
        "tea": list of strings, representing ids of the tea people
    people : list of dictionaries with the following keys, containing people eligible to schedule talks for
        "id": string, representing notion id of the person
        "away_from": list of datetime.datetime objects representing start of away dates (inclusive)
        "away_until": list of datetime.datetime objects representing end of away dates (inclusive) 
                      e.g. ( people["away_from"][0], people["away_until"][0] ) forms an away date pair
        "tea_excluded": boolean indicating whether the person is excluded from tea
        "tt_excluded": boolean indicating whether the person is excluded from tea talk
        "rt_excluded": boolean indicating whether the person is excluded from research talk
    query : string indicating the type of scheduling query. Only one of the following values is allowed:
        "ResearchTeaTalks": scheduling research talks, tea talks and tea
        "MLJC": scheduling MLJC
        "TNJC": scheduling TNJC
        "Coffee Cleaning": scheduling coffee

    Returns
    -------
    filled_schedule: list of dictionaries with the following keys
        "date": datetime.datetime object representing date of the talk
        "type": either "Research Talk" or "Tea Talk" representing research talk or tea talk; "Just Tea" for no talk
        "id": string, representing notion id of the talk
        "presenter": notion id for the person presenting
        "tea": notion id for the person doing tea preparation
    '''

    if query not in ["ResearchTeaTalks", "MLJC", "TNJC", "Coffee Cleaning"]: 
        print('Invalid query sent to scheduling script')
        return 

    # differentiate the things to be filled from things already scheduled
    to_fill_schedule = [ concat_dict(talk, {"to_fill": True}) for talk in to_fill_schedule ]
    past_schedule = [ concat_dict(talk, {"to_fill": False}) for talk in past_schedule ]
    # merge and sort
    schedule = sorted(to_fill_schedule + past_schedule, key=lambda x: x["date"])

    # get priority queues for each of research talk, tea talk and tea
    if query == 'ResearchTeaTalks':
        rt_queue = get_priority_queue(past_schedule, people, 
                                         [ victim["id"] for victim in people if victim["rt_excluded"] == False], 
                                      "Research Talk")
        tt_queue = get_priority_queue(past_schedule, people, 
                                         [ victim["id"] for victim in people if victim["tt_excluded"] == False], 
                                      "Tea Talk")
        tea_queue = get_priority_queue(past_schedule, people, 
                                         [ victim["id"] for victim in people if victim["tea_excluded"] == False], 
                                       "Tea")
        
        schedule = fill_schedule(schedule, rt_queue, "Research Talk")
        schedule = fill_schedule(schedule, tt_queue, "Tea Talk")
        schedule = fill_schedule(schedule, tea_queue, "Tea")
        
        filled_schedule = [ talk for talk in schedule if talk["to_fill"] ]
        return filled_schedule
    
    else: # handles MLJC, TNJC, Coffee Cleaning
        queue = get_priority_queue(past_schedule, people, [ victim["id"] for victim in people], query)
        schedule = fill_schedule(schedule, queue, query)

        filled_schedule = [ talk for talk in schedule if talk["to_fill"] ]
        return filled_schedule

