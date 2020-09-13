def query_bdd_for_player_mock(url_query):
    """
    This method is a mock for now.

    :param url_query: string
    Url query with which to query the database
    :return: string
    The json string of the player, if query was successful, empty string otherwise.
    """
    json = ''
    if '188626510901542912' in url_query:
        json = [{'start': 0, 'end': 100000, 'repeatable': 1, 'id': 'some-id',},
                { 'start': 200000, 'end': 500000, 'repeatable': 1, 'id': 'some-id'},
                { 'start': 700000, 'end': 1100000, 'repeatable': 1, 'id': 'some-id'}]
    elif '265523588918935552' in url_query:
        json = [{ 'start': 3, 'end': 90000,'repeatable': 1, 'id': 'some-id'},
                { 'start': 150000,'end': 310000,'repeatable': 1,'id': 'some-id'}]
    elif '298673420181438465' in url_query:
        json = [{ 'start': 2, 'end': 80000, 'repeatable': 1,'id': 'some-id'},
                { 'start': 170000, 'end': 700000, 'repeatable': 1, 'id': 'some-id'}]
    return json
