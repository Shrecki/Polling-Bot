import numpy as np
import pandas as pd
from datetime import timezone
import datetime
import bdd_handler

def find_intersections(intervals, minimum_length):
    """
    This function is tasked with finding intersection between intervals of availabilities between players.
    A player has zero or more availabilities. An availability is nothing but a tuple (a,b), a<b where a is the start
    time of the availability and b is the end time of the availability.
    A player therefore simply has an array of such availabilities.
    This algorithm is tasked with intersecting availabilities of several players to find intervals where all players
    are available.

    It is also possible to constrain the search of intervals to keep only intervals of at least a specific minimum
    length.

    Do note that the algorithm deals with numbers. We talk of availabilities to make the algorithm intent clear, but
    it really only deal with intervals and has no notion of dates or even time for that matter.
    To reflect this better, the code only speaks of intervals, from arguments down to variables.

    :param intervals: list[np.array]
    Every player returns a list of intervals. We here expect to receive concatenation of all these intervals (ie: each
    entry of this list is a list of intervals). We further assume that the list of intervals is in numpy format of shape
     (N,2), N being the list of events for the considered player.
    Cannot be an empty list, or a ValueError is thrown.
    Must contain at least one player with availabilities, or a ValueError is thrown.
    A player's availability MUST be a numpy array of shape (N,2) or a ValueError will be thrown. (N doesn't have to be
    the same for all players).

    :param minimum_length: int
    Minimum length of valid intervals. Must be strictly positive, or a value error will be thrown.

    :return: found_intervals: list
    List of found intervals, if any, or an empty array if no interval was found.
    If a single player is passed, availabilities of the player will be returned.
    """
    n_players = len(intervals)
    if n_players == 0:
        raise ValueError('Invalid number of players: intervals should contain at least one entry.')

    if minimum_length <= 0:
        raise ValueError('Minimum length must be strictly positive!')

    # We create an array of so-called valid players. These players are those that filled their availabilities.
    valid_players = []
    iterators = []
    max_iterators = []
    for player_i in range(0, n_players):
        if intervals[player_i] is not None:
            valid_players.append(intervals[player_i])
            iterators.append(0)
            if len(intervals[player_i].shape) != 2:
                raise ValueError('interval of player should confirm to shape (N,2), where N is the number of intervals '
                                 'of the player, got shape {} instead'.format(intervals[player_i].shape))
            max_iterators.append(intervals[player_i].shape[0]-1)

    iterators = np.asarray(iterators)
    max_iterators = np.asarray(max_iterators)

    if len(valid_players) == 0:
        raise ValueError('No valid intervals! Players did not fill in their calendars!')

    starts = np.empty((len(valid_players)))
    ends = np.empty((len(valid_players)))
    for i, player_i in enumerate(valid_players):
        starts[i] = player_i[iterators[i], 0]
        ends[i] = player_i[iterators[i], 1]

    found_intervals = []

    # The stopping criterion is that we've checked through all intervals of players (apart from internal early stopping
    # conditions of course). This happens once all iterators are done.
    while np.any(max_iterators >= iterators):
        # Start of an interval is the maximum of all starts for all players. (Furthest starting point so to say)
        start_interval = np.max(starts)

        # End of an interval intersecting all availabilities is the minimum of all player's ends (Closest ending point)
        end_interval = np.min(ends)

        print('{} - {} (diff is : {}, minimum length is {})'.format(start_interval, end_interval, end_interval-start_interval, minimum_length))
        print('Starts : {} '.format(starts))
        print('Ends : {} '.format(ends))

        # Add the current interval to good intervals if it is valid. An interval is valid under two conditions:
        # 1) it must be strictly positive
        # 2) it must have an amplitude/length greater or equal to minimum length.
        # Notice that minimum_length is required to be strictly positive, therefore 2) is sufficient for 1).
        if end_interval - start_interval >= minimum_length:
            found_intervals.append([start_interval, end_interval])

        # Now, for the magic part of the algorithm.
        # We will actually increment the interval with the smallest end (/!\ nothing to do with interval amplitude).
        # Assume we have one interval for player 1 which covers all possible times (its end point extends to infinity).
        # Assume now player 2, who has short availabilities, across time.
        # We start with interval 1 of player 2, then we increment interval of player who has smallest end point, ie
        # player 2 (in this case, it will always be the case actually).
        # This is but one of the possible cases as to why it is desirable to start with smallest end point for such
        # interval searches.
        farthest_interval_id = np.argmin(ends)

        # We can only increment this iterator if it didn't reach its end value, so to say.
        # If so, increment it and update the start and end points of its player with its successor interval.
        if iterators[farthest_interval_id] < max_iterators[farthest_interval_id]:
            iterators[farthest_interval_id] += 1
            # Modify starts and ends accordingly
            starts[farthest_interval_id] = valid_players[farthest_interval_id][iterators[farthest_interval_id], 0]
            ends[farthest_interval_id] = valid_players[farthest_interval_id][iterators[farthest_interval_id], 1]

        # We have reached a case, where we have to increment an interval which, really, shouldn't be incremented anymore
        # The interval cannot be changed here. Since we look at interval with furthest end, by hypothesis, it can only
        # either intersect with current intervals of other players, or won't intersect with any other.
        # Because of this property, if an intersection was found, it has been added above. We are guaranteed that
        # there exists no other intersection and we can therefore escape the loop.
        else:
            break
    return found_intervals

def get_player_json(player_id, start_time, end_time):
    """
    This method uses the provided player_id to query the BDD and get the player's JSON (as a string)

    :param player_id: int
    Discord id of the player
    :param start_time: int
    Unix timestamp of start time (moment where we start to look for availabilities of the considered player)
    :param end_time: int
    Unix timestamp of end time (moment where we stop looking for availabilities of the considered player)
    :return: player_json: string
    String representing the player's JSON in the BDD.
    """
    url_query = "https://api.dispos.pocot.fr/events/"+str(player_id)+"?from="+str(start_time) +"&to="+str(end_time)
    json = bdd_handler.query_bdd_for_player(url_query)
    print(url_query)
    return json


def convert_player_json(player_id, start_time, start_time_strict, end_time):
    """
    Method which, provided a player id, queries the BDD for its JSON, reads its, and converts it to the appropriate
    array. Note that if the player hasn't filled his/her availabilities (meaning an empty JSON was retrieved), this
    method returns a None instead of an array.
    :param player_id: the id of the player (Discord id)
    :param start_time: start time. This argument is helpful to provide the day from which to start to look for requests,
    potentially including intervals that started before the request was issued.
    :param start_time_strict: strict starting time of the request. This one will be helpful to filter out intervals
    starting before start_time_strict. All start_time inferior to start_time_strict will be included and then truncated
    to start_time_strict .
    :param end_time: end time of tolerated intervals. Do note that only start time of intervals are filtered through
    this end_time. This is because an interval might very well be valid by starting before end_time, but ending after it.
    We don't exclude it in this case but truncate its end_time to end_time.
    :return: player_array, array containing intervals truncated to fall between start_time_strict and end_time, by retaining
    all intervals that have a start_time between start_time and end_time. Intervals are returned sorted by start_time in
    increasing order.
    """
    player_json = get_player_json(player_id, start_time, end_time)
    player_array = None

    # Expression is equivalent to if player_json != []
    if player_json:
        player_df = pd.DataFrame(player_json)
        try:
            player_array_tmp = player_df[['start', 'end']]
        except KeyError:
            raise KeyError('Player entries invalid: expected to find at start and end keys, but got {} instead'.format(player_df.keys()))

        # We filter out all entries where the start time is out of bound. We do not filter on the end time, because it
        # is possible that an interval reaches out of these bounds. In such case, we will simply have to truncate it,
        # instead of excluding it.
        # Likewise for the case of an entry with a start somehow before start_time.
        player_array_tmp = player_array_tmp[(player_array_tmp['end'] > start_time_strict) & (player_array_tmp['start'] < end_time)]

        # Truncate now the end time of valid entries.
        player_array = player_array_tmp.copy()
        player_array.loc[player_array_tmp.end > end_time, 'end'] = end_time
        player_array.loc[player_array_tmp.start < start_time_strict, 'start'] = start_time_strict
        player_array = player_array.sort_values('start').to_numpy()
    return player_array


def convert_time_string_to_unix_timestamp(time_string):
    """Format assumed to be HH:MM"""
    print('time_string : {}'.format(time_string))
    hours_minutes = time_string.split(':')
    hours_minutes[0] = int(hours_minutes[0])
    hours_minutes[1] = int(hours_minutes[1])
    if len(hours_minutes) != 2:
        raise ValueError('Input format of time string must conform to HH:MM !')
    if hours_minutes[0] < 0:
        raise ValueError('Hours should be positive or zero ! ')
    if hours_minutes[1] < 0:
        raise ValueError('Minutes should be positive or zero !')
    print('New minimum length : {}'.format(hours_minutes[0]*3600 + hours_minutes[1]*60))
    return hours_minutes[0]*3600 + hours_minutes[1]*60


def convert_weeks_to_unix_timestamp(n_weeks: int):
    if n_weeks <= 0:
        raise ValueError('Should look at at least one week, but number of weeks was negative or null.')
    return n_weeks * 7 * 24 * 3600


def convert_date_to_unix_timestamp(dt: datetime.datetime):
    return dt.replace(tzinfo=timezone.utc).timestamp()


def get_from_and_to_optimistic(curr_date: datetime.datetime, n_weeks: int):
    # We want to start from the whole day
    curr_date_morning = datetime.datetime(curr_date.year, curr_date.month, curr_date.day, 0,0,0,0, timezone.utc)
    from_ = int(convert_date_to_unix_timestamp(curr_date_morning)*1000)

    # For the end date, we want to consider the entirety of the end day, so we'll set the end date to 23h59 and 59s.
    end_date = datetime.datetime(curr_date.year, curr_date.month, curr_date.day, 23,59,59,0, timezone.utc)
    to_ = int((convert_date_to_unix_timestamp(end_date) + convert_weeks_to_unix_timestamp(n_weeks))*1000)
    return from_, to_


def get_from_strict(curr_date: datetime.datetime):
    from_ = int(convert_date_to_unix_timestamp(curr_date)*1000)
    return from_


def convert_timestamp_to_date(timestamp: int, is_milliseconds=True, french_time=False):
    coeff = 1.0
    if is_milliseconds:
        coeff = 1000.0
    time_zone = datetime.timezone.utc
    if french_time:
        time_zone = datetime.timezone(datetime.timedelta(hours=2))
    return datetime.datetime.fromtimestamp(int(timestamp/coeff), tz=time_zone)


def convert_number_to_day_string(day_number: int):
    if day_number < 0 or day_number > 6:
        raise ValueError('Expected day_number to be strictly between 0 and 6 (both included), but got {} instead.'.format(day_number))
    days = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}

    return days[day_number]


def convert_number_to_month_string(month_number: int):
    if month_number < 1 or month_number > 12:
        raise ValueError('Expected month_number to be strictly between 1 and 12 (both included), but got {} instead.'.
                         format(month_number))
    months = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August',
              9: 'September', 10: 'October', 11: 'November', 12: 'December'}

    return months[month_number]
