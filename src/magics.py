import discord
from record import *
from functions import convert_channel_id_to_name, get_full_champion_kor_name


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


# 모스트 밴 TOP 50 text
def get_most_banned_text():
    
    banned_champions = get_most_banned_champions()
    total_games = get_total_games()

    most_banned_text = f"## 가장 많이 밴 된 챔피언 TOP 50 \n\n"

    for rank, champ in enumerate(banned_champions, start=1):
        most_banned_text += (f"{rank}위. {get_full_champion_kor_name(champ['champion'])} : {champ['ban_count']}회, ( {round(champ['ban_count'] / total_games * 100, 2)}% )\n")
        if rank >= 50:
            break

    return most_banned_text


# 유저 라인별 밴 당한 리스트 출력:
def get_banned_by_lane_text(user: discord.Member):

    from functions import get_champions_per_line, get_nickname

    id = user.id

    banned_by_lane_result = get_banned_champions_by_position(id)

    banned_by_lane_text = f"## {get_nickname(user)}님의 라인별 밴 당한 챔피언 목록\n\n"

    for row in banned_by_lane_result:
        position_eng, champion, ban_count, _ = row

        position = "탑" if position_eng == "top" \
            else "정글" if position_eng == "jungle" \
            else "미드" if position_eng == "mid" \
            else "원딜" if position_eng == "bot" \
            else "서폿"
        
        champion_per_line = get_champions_per_line(position_eng)

        if champion == "Total Games":
            banned_by_lane_text += (f"\n### {position} 게임 수: {ban_count}\n\n")
            banned_by_lane_text += f"{position} 선택 시 밴당한 {position} 챔피언 목록\n\n"
        else:
            if champion in champion_per_line:
                banned_by_lane_text += (f" {get_full_champion_kor_name(champion)} - {ban_count}회\n")

    return banned_by_lane_text