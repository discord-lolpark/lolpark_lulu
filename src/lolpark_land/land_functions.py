import discord
from record import get_summoner_stats


def get_lolpark_coin(user: discord.Member):

    from config import now_season, division_matchid_dict

    (start_id, end_id) = division_matchid_dict[now_season]

    user_stats = get_summoner_stats(user, start_id, end_id)

    win = user_stats["wins"]
    lose = user_stats["loses"]

    return win * 300 + lose * 100