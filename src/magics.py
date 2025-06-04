import discord
from record import *
from functions import convert_channel_id_to_name, get_full_champion_kor_name


# 승률 계산
def calculate_win_rate(win: int, lose: int) -> float:
    if win + lose == 0:  # 경기가 없는 경우 승률 0% 반환
        return 0.0
    win_rate = (win / (win + lose)) * 100
    return round(win_rate, 2)  # 소수점 셋째 자리에서 반올림


# 요약 전적 가져오기 (/전적 사용시, 일반 서버원)
def get_summarized_record_text(user: discord.member, for_qualification=False):

    stat_dict = get_summoner_stats(user, 0, 999999999)

    total_games = stat_dict["total_games"]
    total_win = stat_dict["wins"]
    total_lose = stat_dict["loses"]
    total_winrate = stat_dict["win_rate"]
    
    result_text = f'## 전체 내전 전적 : {total_games}전 {total_win}승 {total_lose}패 ( {total_winrate}% )\n'
    
    return result_text



# 유저 라인별 밴 당한 리스트 출력:
def get_banned_by_lane_text(user: discord.Member):

    from functions import get_champions_per_line, get_nickname

    id = user.id

    banned_by_lane_result = get_banned_champions_by_position(id)

    banned_by_lane_text = f"## {get_nickname(user)}님의 라인별 밴 당한 챔피언 목록\n\n"

    for row in banned_by_lane_result:
        position_eng, champion, ban_count, _ = row

        if ban_count == 0:
            continue

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


# 모스트 픽 TOP 50 text
def get_most_picked_text():
    
    picked_champions = get_most_picked_champions()
    total_games = get_total_games()

    most_picked_text = f"## 가장 많이 픽 된 챔피언 TOP 50 \n\n"

    for rank, champ in enumerate(picked_champions, start=1):
        most_picked_text += (f"{rank}위. {get_full_champion_kor_name(champ['champion'])} : {champ['pick_count']}회, ( {round(champ['pick_count'] / total_games * 100, 2)}% )\n")
        if rank >= 50:
            break

    return most_picked_text


# 픽한 리스트 출력:
def get_picked_by_lane_text(user: discord.Member):

    from functions import get_champions_per_line, get_nickname

    id = user.id

    picked_by_lane_result = get_picked_champions_by_position(id)

    picked_by_lane_text = f"## {get_nickname(user)}님의 라인별 픽한 챔피언 목록\n\n"

    for row in picked_by_lane_result:
        position_eng, champion, pick_count, _ = row

        if pick_count == 0:
            continue

        position = "탑" if position_eng == "top" \
            else "정글" if position_eng == "jungle" \
            else "미드" if position_eng == "mid" \
            else "원딜" if position_eng == "bot" \
            else "서폿"

        if champion == "Total Games":
            picked_by_lane_text += (f"\n### {position} 게임 수: {pick_count}\n\n")
            picked_by_lane_text += f"{position}에서 픽한 챔피언 목록\n\n"
        else:
            picked_by_lane_text += (f" {get_full_champion_kor_name(champion)} - {pick_count}회\n")

    return picked_by_lane_text


def delete_match_data(match_id):
    conn = sqlite3.connect(matches_db)
    cursor = conn.cursor()

    # 테이블에서 match_id에 해당하는 데이터 삭제
    cursor.execute("DELETE FROM PICKS WHERE match_id = ?", (match_id,))
    cursor.execute("DELETE FROM BANS WHERE match_id = ?", (match_id,))
    cursor.execute("DELETE FROM GAMES WHERE match_id = ?", (match_id,))
    cursor.execute("DELETE FROM MATCHES WHERE match_id = ?", (match_id,))

    conn.commit()
    conn.close()


def swap_game_winner(match_id, game_number):
    """
    특정 게임의 승자와 패자 팀을 서로 바꾸고, MATCHES 테이블의 승리 기록도 업데이트합니다.
    
    Parameters:
    match_id (int): 매치 ID
    game_number (int): 게임 번호 (game_index)
    
    Returns:
    bool: 성공적으로 업데이트되었는지 여부
    """
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(matches_db)
        cursor = conn.cursor()
        
        # 트랜잭션 시작
        conn.execute("BEGIN TRANSACTION")
        
        # 1. 현재 게임의 승자와 패자 정보 가져오기
        cursor.execute('''
            SELECT winner_team, loser_team
            FROM GAMES
            WHERE match_id = ? AND game_index = ?
        ''', (match_id, game_number))
        
        game_info = cursor.fetchone()
        if not game_info:
            print(f"게임 정보를 찾을 수 없습니다: match_id={match_id}, game_index={game_number}")
            conn.rollback()
            conn.close()
            return False
        
        current_winner, current_loser = game_info
        
        # 만약 승자나 패자 정보가 없으면 실패
        if not current_winner or not current_loser:
            print(f"승자 또는 패자 정보가 없습니다. 완료된 게임이 아닙니다.")
            conn.rollback()
            conn.close()
            return False
        
        # 2. GAMES 테이블에서 승자와 패자 뒤바꾸기
        cursor.execute('''
            UPDATE GAMES
            SET winner_team = ?, loser_team = ?
            WHERE match_id = ? AND game_index = ?
        ''', (current_loser, current_winner, match_id, game_number))
        
        # 3. MATCHES 테이블에서 승리 카운트 업데이트
        # 이전 승자의 승리 수 감소
        cursor.execute(f'''
            UPDATE MATCHES
            SET {current_winner}_win = {current_winner}_win - 1
            WHERE match_id = ?
        ''', (match_id,))
        
        # 새 승자(이전 패자)의 승리 수 증가
        cursor.execute(f'''
            UPDATE MATCHES
            SET {current_loser}_win = {current_loser}_win + 1
            WHERE match_id = ?
        ''', (match_id,))
        
        # 트랜잭션 커밋
        conn.commit()
        
        print(f"게임 승자가 성공적으로 변경되었습니다: match_id={match_id}, game_index={game_number}")
        print(f"이전 승자: {current_winner}, 새 승자: {current_loser}")
        
        # 연결 종료
        cursor.close()
        conn.close()
        
        return True
        
    except sqlite3.Error as e:
        print(f"데이터베이스 오류: {e}")
        # 연결이 열려있는 경우 롤백하고 닫기
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        # 연결이 열려있는 경우 롤백하고 닫기
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False