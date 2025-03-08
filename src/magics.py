import discord
from record import *
from functions import convert_channel_id_to_name


# 승률 계산
def calculate_win_rate(win: int, lose: int) -> float:
    if win + lose == 0:  # 경기가 없는 경우 승률 0% 반환
        return 0.0
    win_rate = (win / (win + lose)) * 100
    return round(win_rate, 2)  # 소수점 셋째 자리에서 반올림


# 요약 전적 가져오기 (/전적 사용시)
def get_summarized_record_text(user: discord.member):

    summoner_stats_by_channel = get_summoner_stats_by_channel(user)

    # 채널별 전적 저장
    record_by_channel = {
        "A": [0, 0],
        "B": [0, 0],
        "C": [0, 0],
        "D": [0, 0],
        "E": [0, 0],
        "F": [0, 0],
        "FEARLESS": [0, 0],
        "TIER_LIMIT": [0, 0],
        "ARAM": [0, 0],
        "TWENTY": [0, 0],
        "TOTAL": [0, 0]
    }

    for channel_id, channel_result in summoner_stats_by_channel.items():
        channel_name = convert_channel_id_to_name(channel_id)

        win = channel_result["wins"]
        lose = channel_result["loses"]

        record_by_channel[channel_name] = [win, lose]

        if channel_name != "ARAM":
            record_by_channel["TOTAL"][0] += win
            record_by_channel["TOTAL"][1] += lose

    def get_channel_record_message(record_by_channel, channel_name):

        channel_name_kor = {
            "FEARLESS": "피어리스",
            "TIER_LIMIT": "티어 제한",
            "ARAM": "칼바람",
            "TWENTY": "20인",
        }

        win = record_by_channel[channel_name][0]
        lose = record_by_channel[channel_name][1]

        games = win + lose
        win_rate = calculate_win_rate(win, lose)

        if win + lose > 0:
            return f'{channel_name_kor[channel_name]} 내전 전적 : {games}전 {win}승 {lose}패 ( {win_rate}% )\n'
        else:
            return f''

    total_win = record_by_channel["TOTAL"][0]
    total_lose = record_by_channel["TOTAL"][1]

    total_games = total_win + total_lose
    total_winrate = calculate_win_rate(total_win, total_lose)

    result_text = f'## 전체 내전 전적 : {total_games}전 {total_win}승 {total_lose}패 ( {total_winrate}% )\n'

    result_text += get_channel_record_message(record_by_channel, channel_name="FEARLESS")
    result_text += get_channel_record_message(record_by_channel, channel_name="TIER_LIMIT")
    result_text += get_channel_record_message(record_by_channel, channel_name="ARAM")
    result_text += get_channel_record_message(record_by_channel, channel_name="TWENTY")
    
    return result_text