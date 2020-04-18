
def pro_heat_level(info):
    '''Based on the information about this pro heat, return the level.
       The level is the number of points awarded to the winner, if there
       is only a final round. Bonus points are awarded for prelim rounds.'''
    if type(info) == int:
        return info
    if "Rising Star" in info or "RS" in info:
        return 10  #"Rising Star"
    elif "Novice" in info or "Basics" in info or "Pre-Champ" in info:
        return 5   #"Novice"
    else:
        return 20  #"Open"


def extra_points(info, check_for_open=True):
    '''Based on the information about this  heat, return the number
       of extra points based on specific key words'''
    value = 0
    if check_for_open and "Open" in info:
        value += 5
    if "Scholarship" in info or "Scolarship" in info:
        value += 5
    return value


def non_pro_heat_level(info, multi_dance=True):
    '''Based on the information about this heat, return the level.
       The level is the number of points awarded to the winner, if there
       is only a final round. Bonus points are awarded for prelim rounds.'''
    if "Newcomer" in info or "Novice" in info:
        return 5 + extra_points(info)
    elif "Bronze" in info:
        return 10 + extra_points(info)
    elif "Silver" in info:
        return 15 + extra_points(info)
    elif "Gold" in info:
        return 20 + extra_points(info)
    elif "Closed" in info or "Challenge" in info:
        return 15 + extra_points(info)
    elif "Open" in info or "World" in info:
        return 20 + extra_points(info, check_for_open=False)
    elif "Pre-Champ" in info or "PreChamp" in info or "Pre Champ" in info:
        return 15
    elif "Champ" in info or "Grand Slam" in info or "Competition" in info:
        return 20
    elif "Scholar" in info:
        return 25
    else:
        if multi_dance:
            #TODO: Query user? 
            print("Unknown level for heat", info)
        return 15


def calc_points(level, placement, num_competitors = 6, rounds = "F", accum = 0):
    '''Point values are awarded based on the level of the event (Open, Rising Star, Novice)
       and the number of rounds (Final only, Semi-Final, and Quarter-Final).
       Extra points are awarded for events that had prelim rounds.'''
    place = placement - 1
    max_pts = level
    if num_competitors >= 5:
        percent_table = [100, 80, 65, 50, 40, 35, 30, 25, 25]
        if rounds == "S":
            max_pts = level + 10
            if placement == -2: # semis
                percent = min(25, max(1, accum))
            else:
                percent = percent_table[place]
        elif rounds == "Q":
            max_pts = level + 20
            if placement == -2: # semis
                percent = min(25, max(15, accum))
            elif placement == -1: # quarters
                percent = min(10, max(1, accum))
            else:
                percent = percent_table[place]
        elif rounds == "R1":
            max_pts = level + 30
            if placement == -2: # semis
                percent = min(25, max(20, accum))
            elif placement == -1: # quarters
                percent = min(15, max(10, accum))
            elif placement == -10: # round 1
                percent = min(5, max(1, accum))
            else:
                percent = percent_table[place]
        elif rounds == "R21":
            max_pts = level + 40
            if placement == -2: # semis
                percent = min(30, max(25, accum))
            elif placement == -1: # quarters
                percent = min(20, max(15, accum))
            elif placement == -5: # round 2
                percent = min(12, max(7, accum))
            elif placement == -10: # round 1
                percent = min(5, max(1, accum))
            else:
                percent = percent_table[place]
        elif rounds == "R321":
            max_pts = level + 50
            if placement == -2: # semis
                percent = min(30, max(25, accum))
            elif placement == -1: # quarters
                percent = min(23, max(19, accum))
            elif placement == -3: # third round
                percent = min(17, max(13, accum))
            elif placement == -5: # round 2
                percent = min(11, max(7, accum))
            elif placement == -10: # round 1
                percent = min(5, max(1, accum))
            else:
                percent = percent_table[place]
        else:
            if num_competitors >= 10:
                max_pts = level + 10
            if place >= len(percent_table):
                percent = percent_table[-1]
            else:
                percent = percent_table[place]
        return max_pts * percent / 100
    elif num_competitors == 4:
        percent_table = [100, 70, 50, 35];
        return max_pts * percent_table[place] / 100
    elif num_competitors == 3:
        percent_table = [90, 60, 35];
        return max_pts * percent_table[place] / 100
    elif num_competitors == 2:
        percent_table = [75, 35];
        return max_pts * percent_table[place] / 100
    else:  # only one entry
        return max_pts * 0.6


'''Main program for testing'''
if __name__ == '__main__':
    rounds = "F"
    for level in ["Open", "Rising Star", "Novice"]:
        for rounds in ["F", "S", "Q"]:
            for competitors in range(1, 9):
                for placement in range (1, competitors + 1):
                    print(level, rounds, competitors, placement, calc_points(level, placement, competitors, rounds=rounds))
            if rounds != "F":
                print(level, rounds, competitors, "Semis", calc_points(level, -2, competitors, accum = 5, rounds=rounds))
                print(level, rounds, competitors, "Semis", calc_points(level, -2, competitors, accum = 15, rounds=rounds))
                print(level, rounds, competitors, "Semis", calc_points(level, -2, competitors, accum = 35, rounds=rounds))
            if rounds == "Q":
                print(level, rounds, competitors, "quarters", calc_points(level, -1, competitors, accum = 4, rounds=rounds))
                print(level, rounds, competitors, "quarters", calc_points(level, -1, competitors, accum = 14, rounds=rounds))
