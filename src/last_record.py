from PIL import Image, ImageDraw, ImageFont
import sqlite3

import discord
from config import matches_db
from functions import get_nickname

def get_personal_game_dict(match_id: int, game_index: int):
    """
    match_id와 game_index를 파라미터로 받아서 게임 정보를 반환하는 함수
    
    Args:
        match_id (int): 경기 ID
        game_index (int): 게임 인덱스
    
    Returns:
        dict: 게임 정보가 담긴 딕셔너리
    """
    conn = sqlite3.connect(matches_db)
    cursor = conn.cursor()
    
    try:
        # GAMES 테이블에서 기본 정보 조회
        cursor.execute('''
            SELECT blue_team, red_team, winner_team, loser_team
            FROM GAMES 
            WHERE match_id = ? AND game_index = ?
        ''', (match_id, game_index))
        
        game_data = cursor.fetchone()
        if not game_data:
            return None
        
        blue_team_name, red_team_name, winner_team, loser_team = game_data
        
        # PICKS 테이블에서 팀별 픽 정보 조회
        cursor.execute('''
            SELECT team_name, summoner_id, line, champion
            FROM PICKS 
            WHERE match_id = ? AND game_index = ?
            ORDER BY team_name, line
        ''', (match_id, game_index))
        
        picks_data = cursor.fetchall()
        
        # 팀별로 데이터 분리
        team_1_picks = {}
        team_2_picks = {}
        
        for team_name, summoner_id, line, champion in picks_data:
            if team_name == "team_1":
                team_1_picks[line] = (summoner_id, champion)
            elif team_name == "team_2":
                team_2_picks[line] = (summoner_id, champion)
        
        # blue/red 팀 매핑 결정
        # blue_team이 "team_1"이면 blue="team_1", red="team_2"
        # blue_team이 "team_2"이면 blue="team_2", red="team_1"
        if blue_team_name == "team_1":
            blue = "team_1"
            red = "team_2"
        else:
            blue = "team_2"
            red = "team_1"
        
        # 결과 딕셔너리 구성
        result = {
            "match_id": match_id,
            "game_index": game_index,
            "blue": blue,
            "red": red,
            "team_1": {
                "top": team_1_picks.get("top", (None, None)),
                "jungle": team_1_picks.get("jungle", (None, None)),
                "mid": team_1_picks.get("mid", (None, None)),
                "bot": team_1_picks.get("bot", (None, None)),
                "support": team_1_picks.get("support", (None, None)),
            },
            "team_2": {
                "top": team_2_picks.get("top", (None, None)),
                "jungle": team_2_picks.get("jungle", (None, None)),
                "mid": team_2_picks.get("mid", (None, None)),
                "bot": team_2_picks.get("bot", (None, None)),
                "support": team_2_picks.get("support", (None, None)),
            },
            "win_team": winner_team
        }
        
        return result
        
    except Exception as e:
        print(f"Error occurred: {e}")
        return None
        
    finally:
        conn.close()

def get_personal_game_result_image(interaction: discord.Interaction, match_id: int, game_index: int):

    game_dict = get_personal_game_dict(match_id=match_id, game_index=game_index)

    team_1 = game_dict["team_1"]
    team_2 = game_dict["team_2"]

    blue_team = team_1 if game_dict["blue"] == "team_1" else team_2
    red_team = team_2 if blue_team == team_1 else team_1

    w = 540
    h = 200

    result_image = Image.new('RGB', (w, h), 'skyblue')

    member_image_x = w // 5 * 2
    member_image_y = h // 5
    game_info_x = w // 5 

    guild = interaction.guild
    user = interaction.user

    def create_team_lineup(team_data):
        """팀 데이터로부터 라인업 리스트 생성"""
        positions = ['top', 'jungle', 'mid', 'bot', 'support']
        lineup = []
        
        for position in positions:
            if position in team_data:
                summoner_id, champion = team_data[position]
                if summoner_id is not None and champion is not None:
                    member = guild.get_member(summoner_id)
                    nickname = get_nickname(member)
                    lineup.append((nickname, champion))
                else:
                    lineup.append((None, None))
            else:
                lineup.append((None, None))
        
        return lineup

    def paste_team_images(lineup, x_position):
        """팀 라인업의 이미지들을 결과 이미지에 붙여넣기"""
        for index, (nickname, champion) in enumerate(lineup):
            member_image = get_member_image(
                nickname=nickname, 
                champion_eng=champion,
                w=member_image_x,
                h=member_image_y,
                is_principal=(nickname == get_nickname(user))
            )
            result_image.paste(member_image, (x_position, member_image_y * index))

    for team_data, x_pos in [(blue_team, 0), (red_team, w - member_image_x)]:
        lineup = create_team_lineup(team_data)
        paste_team_images(lineup, x_pos)

    return result_image


# 텍스트박스 그리기
def get_textbox(x: int, y: int, text: str, font_path: str, max_font_size=200, min_font_size=10, padding=10, font_color='white', background_color='skyblue'):

    textbox_image = Image.new('RGB', (x, y), background_color)
    draw = ImageDraw.Draw(textbox_image)
    font_size = max_font_size

    while font_size >= min_font_size:
        font = ImageFont.truetype(font_path, font_size)
        # 텍스트 크기 측정 (bbox는 (left, top, right, bottom) 반환)
        bbox = draw.textbbox((0, 0), text, font=font)
        
        # 텍스트 실제 너비와 높이 계산
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 텍스트가 박스 안에 들어가면 폰트 크기 확정
        if text_width <= x - padding * 2 and text_height <= y - padding * 2:
            break
        font_size -= 2  # 폰트 크기를 줄이면서 확인

    # 텍스트 위치 중앙 정렬 (bbox 오프셋 고려)
    text_x = (x - text_width) // 2 - bbox[0]  # left 오프셋 보정
    text_y = (y - text_height) // 2 - bbox[1]  # top 오프셋 보정

    # 배경은 이미지 생성 시 이미 채워졌으므로 다시 그릴 필요 없음
    # draw.rectangle([0, 0, x, y], fill=background_color)  # x*2, y*2가 아닌 x, y로 수정

    # 텍스트 추가 (오프셋 보정된 위치에)
    draw.text((text_x, text_y), text, fill=font_color, font=font)

    return textbox_image


def get_member_image(nickname: str, champion_eng: str, w: int, h: int, is_principal=False):

    member_image = Image.new('RGB', (w, h), 'skyblue')

    font_path = 'assets/fonts/CookieRun.ttf'
    font_color = 'purple' if is_principal else 'black'

    champion_image = Image.open(f'assets/champions/square/{champion_eng}.png').resize((h, h), Image.Resampling.LANCZOS)
    nickname_textbox = get_textbox(w-h, h, nickname, font_path, font_color=font_color)

    member_image.paste(nickname_textbox, (0, 0))
    member_image.paste(champion_image, (w - h, 0))

    return member_image
