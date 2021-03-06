from datetime import timedelta

tea_tzar_id = "2e48529a-c483-4946-8f4e-d5eeb8f4c821" # Kevin's id; fallback when no one is available for tea duty

def get_priority_queue(past_schedule, people):
    '''Returns priority queues of people to be scheduled duties for research talk, tea talk and tea    
    '''
    # rt=research talk, tt=tea talk, t=tea
    rt_queue = []
    tt_queue = []
    tea_queue = []

    rt_eligible_ids = [ victim["id"] for victim in people if victim["rt_excluded"] == False]
    tt_eligible_ids = [ victim["id"] for victim in people if victim["tt_excluded"] == False]
    tea_eligible_ids = [ victim["id"] for victim in people if victim["tea_excluded"] == False]

    # for now, all queues are ordered with least priority -> highest priority

    # loop through past year's talks from most recent to least
    past_schedule = sorted(past_schedule, key=lambda x: x["date"], reverse=True)
    for past_talk in past_schedule:
        # loop through presenters and add eligible people
        for p_id in past_talk["presenter"]:
            if p_id not in rt_queue and p_id in rt_eligible_ids and past_talk["type"] == "Research Talk":
                rt_queue.append(p_id)
            elif p_id not in tt_queue and p_id in tt_eligible_ids and past_talk["type"] == "Tea Talk":
                tt_queue.append(p_id)
            # skip talk types that are neither because no way to know what that is

        # loop through tea people and add eligible people
        for p_id in past_talk["tea"]:
            if p_id not in tea_queue and p_id in tea_eligible_ids:
                tea_queue.append(p_id)
    
    # add anyone who's not found in the past year's talks to the start of the queue
    for p_id in rt_eligible_ids:
        if p_id not in rt_queue:
            rt_queue.append(p_id)
    for p_id in tt_eligible_ids:
        if p_id not in tt_queue:
            tt_queue.append(p_id)
    for p_id in tea_eligible_ids:
        if p_id not in tea_queue:
            tea_queue.append(p_id)
            
    # convert people list to a dictionary of id->victim
    people_dict = { victim["id"]:victim for victim in people}
    
    # reverse order of ids, i.e. highest priority -> lowest priority, and then replace ids with people
    rt_queue_processed = [ people_dict[p_id] for p_id in reversed(rt_queue)]
    tt_queue_processed = [ people_dict[p_id] for p_id in reversed(tt_queue)]
    tea_queue_processed = [ people_dict[p_id] for p_id in reversed(tea_queue)]

    return rt_queue_processed, tt_queue_processed, tea_queue_processed

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

def fill_schedule(to_fill_schedule, past_schedule, rt_queue, tt_queue, tea_queue):
    '''Returns a filled schedule that everybody *should be* happy with
    '''
    # differentiate the things to be filled from things already scheduled
    to_fill_schedule = [ concat_dict(talk, {"to_fill": True}) for talk in to_fill_schedule ]
    past_schedule = [ concat_dict(talk, {"to_fill": False}) for talk in past_schedule ]
    # merge and sort
    merged_schedule = sorted(to_fill_schedule + past_schedule, key=lambda x: x["date"])
    
    # 1. Schedule research talks
    rt_queue = [ concat_dict(victim, {"taken": False}) for victim in rt_queue ]
    for i, talk in enumerate(merged_schedule):
        if talk["to_fill"] and talk["type"] == "Research Talk":
            # schedule
            found_victim = False
            for j, victim in enumerate(rt_queue):
                if not victim["taken"]:
                    if not check_date_contained(talk["date"], victim["away_from"], victim["away_until"]):
                        found_victim = True
                        rt_queue[j]["taken"] = True
                        merged_schedule[i]["presenter"] = [victim["id"]]
                        break
            if not found_victim:
                merged_schedule[i]["type"] = "Just Tea"
    
    # 2. Schedule tea talks
    tt_queue = [ concat_dict(victim, {"taken": False}) for victim in tt_queue ]
    for i, talk in enumerate(merged_schedule):
        if talk["to_fill"] and talk["type"] == "Tea Talk":
            # get a white list of ids of people to protect from duties
            whitelist = get_whitelist(talk["date"], merged_schedule)
            # schedule
            found_victim = False
            for j, victim in enumerate(tt_queue):
                if (not victim["taken"]) and (victim["id"] not in whitelist):
                    if not check_date_contained(talk["date"], victim["away_from"], victim["away_until"]):
                        found_victim = True
                        tt_queue[j]["taken"] = True
                        merged_schedule[i]["presenter"] = [victim["id"]]
                        break
            if not found_victim:
                merged_schedule[i]["type"] = "Just Tea"

    # 3. Schedule tea
    tea_queue = [ concat_dict(victim, {"taken": False}) for victim in tea_queue ]
    for i, talk in enumerate(merged_schedule):
        if talk["to_fill"]:
            # get a white list of ids of people to protect from duties
            whitelist = get_whitelist(talk["date"], merged_schedule)
            # schedule
            found_victim = False
            for j, victim in enumerate(tea_queue):
                if (not victim["taken"]) and (victim["id"] not in whitelist):
                    if not check_date_contained(talk["date"], victim["away_from"], victim["away_until"]):
                        found_victim = True
                        tea_queue[j]["taken"] = True
                        merged_schedule[i]["tea"] = [victim["id"]]
                        break
            if not found_victim:
                merged_schedule[i]["tea"] = [tea_tzar_id]

    # sieve out schedule that was filled
    filled_schedule = [ talk for talk in merged_schedule if talk["to_fill"] ]
    return filled_schedule

def main(to_fill_schedule, past_schedule, people):
    '''Returns a schedule for research and tea talks

    Parameters
    ----------
    to_fill_schedule : list of dictionaries with the following keys
        "date": datetime.datetime object representing date of the talk
        "type": either "Research Talk" or "Tea Talk" representing research talk or tea talk; "Just Tea" for no talk
        "id": string, representing notion id of the talk
    past_schedule : list of dictionaries with the following keys, containing talks from the past year
        "date": datetime.datetime object representing date of the talk
        "type": either "Research Talk" or "Tea Talk" representing research talk or tea talk; "Just Tea" for no talk
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

    Returns
    -------
    filled_schedule: list of dictionaries with the following keys
        "date": datetime.datetime object representing date of the talk
        "type": either "Research Talk" or "Tea Talk" representing research talk or tea talk; "Just Tea" for no talk
        "id": string, representing notion id of the talk
        "presenter": notion id for the person presenting
        "tea": notion id for the person doing tea preparation
    '''

    # get priority queues for each of research talk, tea talk and tea
    rt_queue, tt_queue, tea_queue = get_priority_queue(past_schedule, people)

    # schedule
    filled_schedule = fill_schedule(to_fill_schedule, past_schedule, rt_queue, tt_queue, tea_queue)

    return filled_schedule