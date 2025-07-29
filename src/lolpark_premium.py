
import discord
import aiohttp
import io
import asyncio
from lolparklib.database_functions import (
    get_summoner_stats
)
from lolparklib.discord_config import (
    lolpark_season,
    match_id_by_season,
    premium_image_h,
    premium_image_w
)
from lolparklib.champion_lib import champions_per_line
from lolparklib.discord_functions import get_nickname, get_tier_color, get_user_tier_part
from PIL import Image, ImageDraw, ImageFont

from lolparklib.lol_functions import get_full_champion_kor_name
from lolparklib.record_functions import get_banned_champions_by_position, get_linewise_game_stats, get_most_pick_personal, get_most_picked_champions, get_recent_champion_history 

font_paths = {
    "cookierun": "assets/fonts/CookieRun.ttf",
    "ownglyph": "assets/fonts/Ownglyph.ttf",
    "pyeongchang": "assets/fonts/pyeongchang.ttf",
    "nickname": "assets/fonts/Nickname.ttf"
}


# 승률 계산
def calculate_win_rate(win: int, lose: int) -> float:
    if win + lose == 0:  # 경기가 없는 경우 승률 0% 반환
        return 0.0
    win_rate = (win / (win + lose)) * 100
    return round(win_rate, 2)  # 소수점 셋째 자리에서 반올림


async def send_tier_adjust_profile(channel, user: discord.Member):

    try:
        # 시즌별 프로필 전송
        for season_category, (start_id, end_id) in match_id_by_season.items():
            
            # 대회 내용은 전송 X
            if start_id > 1000000:
                continue

            season_games = get_summoner_stats(user, season=season_category)["total_games"]

            if season_games > 0:
                try:
                    season_profile = await get_lolpark_premium_profile(user, start_id, end_id)
                    with io.BytesIO() as season_buffer:
                        season_profile.save(season_buffer, format='PNG')
                        season_buffer.seek(0)
                        await channel.send(file=discord.File(season_buffer, filename=f"{season_category}_profile.png"))
                except Exception as e:
                    print(f"시즌 {season_category} 프로필 생성 실패: {e}")
                    continue

    except Exception as e:
        print(f"프로필 전송 중 오류 발생: {e}")
        await channel.send("프로필 생성 중 오류가 발생했습니다. 전적이 없을 가능성이 있습니다.")
    


# 요약 전적 가져오기 (/전적 사용시, 일반 서버원)
def get_summarized_record_text(user: discord.member):

    stat_dict = get_summoner_stats(user, season=lolpark_season)

    total_games = stat_dict["total_games"]
    total_win = stat_dict["wins"]
    total_lose = stat_dict["loses"]
    total_winrate = stat_dict["win_rate"]
    
    result_text = f'## 전체 내전 전적 : {total_games}전 {total_win}승 {total_lose}패 ( {total_winrate}% )\n'
    
    return result_text


async def get_premium_record(member: discord.Member):

    result_future = asyncio.Future()

    class LolparkPremiumStatView(discord.ui.View):
        def __init__(self, member, future):
            super().__init__(timeout=180)
            self.message = None
            self.member = member
            self.future = future

        async def on_timeout(self):
            if not self.future.done():
                self.future.set_result(None)
            try:
                await self.message.delete()
            except discord.NotFound:
                pass

    class StatButton(discord.ui.Button):
        def __init__(self, season, member, future):
            button_style = discord.ButtonStyle.green if season == "통산" else discord.ButtonStyle.primary
            super().__init__(label=season, style=button_style)
            self.member = member
            self.season = season
            self.future = future
        
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            profile = await get_lolpark_premium_profile(self.member, self.season)

            if not self.future.done():
                self.future.set_result(profile)
            
        
    stat_view = LolparkPremiumStatView(member, result_future)

    for season_category, (start_id, end_id) in match_id_by_season.items():
        season_games = get_summoner_stats(member, season=season_category)["total_games"]

        if season_games > 0:
            stat_view.add_item(StatButton(season_category,  member, result_future))
    
    return stat_view, result_future


async def get_lolpark_premium_profile(member: discord.Member, season: str):

    profile = Image.new('RGB', (premium_image_w, premium_image_h), 'skyblue')
    padding = 50

    start_id, end_id = match_id_by_season.get(season, (0, 9999999999))

    # 시즌 표시
    season_textbox = get_season_textbox(start_id, end_id)

    # 디스코드 프로필 이미지
    profile_image = await get_profile_image(member)

    # 롤 닉네임#태그
    nickname_textbox = get_nickname_textbox(member)

    # 현재 티어 로고
    tier_image = get_tier_image(member)

    # 통산 전적 textbox
    full_record_textbox = get_full_record_textbox(member, season)

    # 최근 전적 image
    recent_result_image = get_lastly_played_game_result(member, start_id, end_id)

    # 모스트 픽
    most_pick_image = get_most_pick_images(member, start_id, end_id)

    # 저격밴
    most_banned_image = get_most_banned_images(member, start_id, end_id)

    # 라인별 승률
    winrate_by_lane_image = get_most_selected_lane(member, start_id, end_id)

    # 각 이미지들 paste
    profile.paste(season_textbox, (padding, 0))
    profile.paste(profile_image, (padding, padding))
    profile.paste(nickname_textbox, (padding + padding // 2 + profile_image.width, padding))
    profile.paste(tier_image, (padding * 2 + profile_image.width + nickname_textbox.width, padding))

    profile.paste(full_record_textbox, (padding, padding * 2 + 100))

    profile.paste(recent_result_image, (padding, padding * 2 + 200))

    # 모스트 픽 top 5
    profile.paste(most_pick_image, (padding, 400))
    # 저격밴 top 5
    profile.paste(most_banned_image, (padding + 500, 400))
    # 라인별 승률
    profile.paste(winrate_by_lane_image, (padding + 500 + 380, 400))

    return profile


def get_season_textbox(start_id, end_id):

    title = "통산"

    for season_title, (s_i, e_i) in match_id_by_season.items():
        if s_i == start_id and e_i == end_id:
            title = season_title

    title += " 전적"

    textbox = get_textbox(300, 50, title, font_path=font_paths["cookierun"], font_color="black")

    return textbox

async def get_profile_image(member:discord.Member):

    profile_image_url = member.display_avatar.url
    
    # 프로필 이미지 다운로드 (메모리에서 직접 불러오기)
    async with aiohttp.ClientSession() as session:
        async with session.get(profile_image_url) as resp:
            if resp.status != 200:
                avatar_data = None
                return
            avatar_data = await resp.read()

    # 프로필 이미지를 PIL Image로 변환 (메모리에서 처리)
    profile_image_size = (100, 100)
    profile_image = Image.open(io.BytesIO(avatar_data)).convert("RGBA").resize((100, 100), Image.Resampling.LANCZOS)

    # ✅ "L" 모드 (그레이스케일) 마스크 생성
    mask = Image.new("L", profile_image_size, 0)  # 검은색 (완전 투명)
    draw = ImageDraw.Draw(mask)

    # ✅ 둥근 모서리를 위한 마스크 적용 (radius=30)
    draw.rounded_rectangle((0, 0, profile_image_size[0], profile_image_size[1]), radius=30, fill=255)

    # ✅ 배경이 skyblue인 이미지 생성
    background = Image.new("RGBA", profile_image_size, "skyblue")

    # ✅ 프로필 이미지를 둥근 마스크를 적용한 형태로 배경에 붙이기
    rounded_profile_image = Image.new("RGBA", profile_image_size, "skyblue")
    rounded_profile_image.paste(profile_image, (0, 0), mask)
    background.paste(rounded_profile_image, (0, 0), rounded_profile_image)

    return rounded_profile_image


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


def get_nickname_textbox(member: discord.Member):

    return get_textbox(x=800, y=100, text=get_nickname(member), font_path=font_paths["nickname"], padding=20, font_color=get_tier_color(member))


def get_tier_image(member):

    tier_initial, tier_score = get_user_tier_part(member)

    tier_image = Image.new('RGB', (350, 100), 'skyblue')

    tier = "challenger" if tier_initial == "C" else \
        "grandmaster" if tier_initial == "GM" else \
        "master" if tier_initial == "M" else \
        "diamond" if tier_initial == "D" else \
        "emerald" if tier_initial == "E" else \
        "platinum" if tier_initial == "P" else \
        "gold" if tier_initial == "G" else \
        "silver" if tier_initial == "S" else \
        "bronze" if tier_initial == "B" else \
        "iron" if tier_initial == "I" else \
        "unranked"
    
    def get_tier_logo(tier):

        # ✅ 원본 이미지 불러오기 (RGBA 모드 유지)
        tier_logo_image = Image.open(f"assets/tier_image/icon/{tier}.png").convert("RGBA").resize((100, 100), Image.Resampling.LANCZOS)

        # ✅ 새로운 배경 생성 (예: skyblue)
        background = Image.new("RGBA", tier_logo_image.size, "skyblue")

        # ✅ 투명한 부분을 skyblue로 채운 이미지 생성
        background.paste(tier_logo_image, (0, 0), tier_logo_image)

        return background
    
    def get_tier_score_textbox(tier, tier_score):
        
        tier_score_textbox_image = Image.new('RGB', (200, 80), 'skyblue')
        draw = ImageDraw.Draw(tier_score_textbox_image)
        font_path = "assets/fonts/CookieRun.ttf"
        font_size = 60
        font_color = "gray"
        font = ImageFont.truetype(font_path, font_size)

        if tier in ['challenger', 'grandmaster', 'master']:
            draw.text((0, 10), f"{tier_score}LP", fill=font_color, font=font)
        elif tier in ['unranked']:
            draw.text((0, 10), f"UNRANKED", fill=font_color, font=font)
        else:
            tier_level_text = ["I", "II", "III", "IV"]
            draw.text((0, 20), f"{tier_level_text[tier_score - 1]}", fill=font_color, font=font)
        
        return tier_score_textbox_image

    tier_logo = get_tier_logo(tier)
    tier_score_textbox = get_tier_score_textbox(tier, tier_score)

    tier_image.paste(tier_logo, (0,0))
    tier_image.paste(tier_score_textbox, (125, 0))

    return tier_image


def get_full_record_textbox(member, season):

    stat_dict = get_summoner_stats(member, season)
    
    x = 1500
    y = 200

    record_textbox_image = Image.new('RGB', (x, y), 'skyblue')
    draw = ImageDraw.Draw(record_textbox_image)

    total_games = stat_dict["total_games"]
    total_win = stat_dict["wins"]
    total_lose = stat_dict["loses"]
    total_winrate = stat_dict["win_rate"]

    full_record_text = f'전체 내전 전적 : {total_games}전 {total_win}승 {total_lose}패 ( {total_winrate}% )'
    full_record_font = ImageFont.truetype("assets/fonts/CookieRun.ttf", 70)

    draw.text((0, 0), full_record_text, fill='black', font=full_record_font)
    
    return record_textbox_image


# 챔피언 프로필 이미지 가져오기
def get_champion_profile_image(champion):
    
    champion_profile_img = Image.new('RGB', (100, 150), 'skyblue')

    champion_kor = get_full_champion_kor_name(champion)

    champion_img = Image.open(f"assets/champion_square/{champion}.png").resize((100, 100), Image.Resampling.LANCZOS)

    champion_name_textbox = get_textbox(x=100, y=40, text=champion_kor, font_path=font_paths["ownglyph"], max_font_size=50, min_font_size=5, padding=5, font_color='black')

    champion_profile_img.paste(champion_img, (0, 0))
    champion_profile_img.paste(champion_name_textbox, (0, 100))

    return champion_profile_img


# 모스트 픽 top 5 나열
def get_most_pick_images(member, start_id, end_id):

    most_x = 700
    most_y = 1000

    most_pick_image = Image.new('RGB', (most_x, most_y), 'skyblue')

    most_pick_list = get_most_pick_personal(member.id, start_id, end_id)

    title_text = get_textbox(700, 100, text='MOST PICK', font_path=font_paths["pyeongchang"], max_font_size=50, padding=10, font_color='black')

    most_pick_image.paste(title_text, (0, 0))
    
    for index, champion_result in enumerate(most_pick_list):

        if index == 5:
            break

        champion, games, win, lose, win_rate = champion_result
        if champion is None:
            continue
        champion_profile_image = get_champion_profile_image(champion)

        result_text_color = 'red' if win_rate >= 60.0 else 'blue' if win_rate <= 40.0 else 'gray'
        result_textbox = get_textbox(x=550, y=100, text=f'{games}전 {win}승 {lose}패 ({win_rate}%)', font_path=font_paths["cookierun"], font_color=result_text_color)

        most_pick_image.paste(result_textbox, (150, 170 * index + 150))

        most_pick_image.paste(champion_profile_image, (0, 170 * index + 150))

    return most_pick_image.resize((420, 600), Image.Resampling.LANCZOS)


# 모스트 픽 top 5 나열
def get_most_banned_images(member, start_id, end_id):

    most_x = 500
    most_y = 1000

    most_banned_image = Image.new('RGB', (most_x, most_y), 'skyblue')

    banned_by_lane_result = get_banned_champions_by_position(member.id, start_id, end_id)

    banned_dict = {}

    for row in banned_by_lane_result:
        position_eng, champion, ban_count, _ = row

        if ban_count == 0:
            continue
        
        champion_per_line = champions_per_line[position_eng]

        if champion == "Total Games":
            continue
        else:
            if champion in champion_per_line:
                if champion in banned_dict:
                    banned_dict[champion] += ban_count
                else:
                    banned_dict[champion] = ban_count
    
    def get_top_5_banned(ban_dict):
        count = min(len(ban_dict), 5)
        # value를 기준으로 내림차순 정렬한 후 상위 5개만 선택
        sorted_items = sorted(ban_dict.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_items[:count])
    
    banned_list = get_top_5_banned(banned_dict)

    title_text = get_textbox(500, 100, text='MOST BANNED', font_path=font_paths["pyeongchang"], max_font_size=50, padding=10, font_color='black')

    most_banned_image.paste(title_text, (0, 0))
    
    for index, (champion, ban_count) in enumerate(banned_list.items()):

        champion_profile_image = get_champion_profile_image(champion)

        most_banned_image.paste(champion_profile_image, (0, 170 * index + 150))
        
        ban_count_textbox = get_textbox(x=350, y=100, text=f'{ban_count}회', font_path=font_paths["cookierun"], max_font_size=50, font_color='black')

        most_banned_image.paste(ban_count_textbox, (150, 170 * index + 150))

    return most_banned_image.resize((300, 600), Image.Resampling.LANCZOS)


def get_lane_logo(line, primary=False):

    # ✅ 원본 이미지 불러오기 (RGBA 모드 유지)
    line_logo_image = Image.open(f'assets/line_icons/{line}_{"primary" if primary else "normal"}.png').convert("RGBA").resize((100, 100), Image.Resampling.LANCZOS)

    # ✅ 새로운 배경 생성 (예: skyblue)
    background = Image.new("RGBA", (100, 100), "skyblue")

    # ✅ 투명한 부분을 skyblue로 채운 이미지 생성
    background.paste(line_logo_image, (0, 0), line_logo_image)

    return background


# 라인별 승률 나열
def get_most_selected_lane(member, start_id, end_id):

    lane_x = 700
    lane_y = 1000

    lane_record_image = Image.new('RGB', (lane_x, lane_y), 'skyblue')

    title_text = get_textbox(700, 100, text='라인별 승률', font_path=font_paths["pyeongchang"], max_font_size=50, padding=10, font_color='black')

    lane_record_image.paste(title_text, (0, 0))

    line_record = get_linewise_game_stats(member.id, start_id, end_id) # (라인 이름(영어), 총 게임 수, 승, 패, 승률)

    def get_record_by_lane(line, games, win, lose, win_rate, primary=False):

        record_image = Image.new('RGB', (700, 140), 'skyblue')
        line_image = get_lane_logo(line, primary=primary)

        line_kor = {
            "top": "탑",
            "jungle": "정글",
            "mid": "미드",
            "bot": "원딜",
            "support": "서포터"
        }

        line_name_textbox = get_textbox(x=100, y=40, text=line_kor.get(line, "없음"), font_path=font_paths["ownglyph"], max_font_size=40, min_font_size=40, padding=5, font_color='black')
        record_text = f"{games}전 {win}승 {lose}패 ({win_rate}%)"

        record_text_color = 'red' if win_rate >= 60.0 else 'blue' if win_rate <= 40.0 else 'gray'
        record_textbox = get_textbox(550, 100, record_text, font_paths["cookierun"], font_color=record_text_color)

        record_image.paste(line_image, (0, 0))
        record_image.paste(line_name_textbox, (0, 100))
        record_image.paste(record_textbox, (150, 0))

        return record_image
        

    for index, record in enumerate(line_record):
        line, games, win, lose, win_rate = record

        primary = True if index == 0 else False

        lane_image = get_record_by_lane(line, games, win, lose, win_rate, primary)
        lane_record_image.paste(lane_image, (0, 170 * index + 150))

    return lane_record_image.resize((420, 600), Image.Resampling.LANCZOS)


# 최근 전적 나열 (최근 10개 게임?)
def get_lastly_played_game_result(member, start_id, end_id):

    recent_result_image = Image.new('RGB', (premium_image_w, 200), 'skyblue')

    recent_x = 60
    recent_y = 80

    if end_id > 100000000:
        end_id = 1000000

    recent_result = get_recent_champion_history(member.id, start_id, end_id)

    def get_result_per_champion(match_id: int, game_index: int, champion_eng: str, line: str, is_win: bool):

        result_per_champion_image = Image.new('RGB', (recent_x, recent_y), 'skyblue')

        draw = ImageDraw.Draw(result_per_champion_image)

        game_info_textbox = get_textbox(recent_x, recent_y // 4, f"#{match_id}({game_index})", font_paths['cookierun'], font_color='gray')

        champion_image = Image.open(f"assets/champion_square/{champion_eng}.png").resize((recent_x, recent_y * 3 // 4), Image.Resampling.LANCZOS)

        result_per_champion_image.paste(game_info_textbox, (0, 0))
        result_per_champion_image.paste(champion_image, (0, recent_y // 4))

        result_text = f"{'W' if is_win else 'L'}"
        result_font = ImageFont.truetype(font_paths['cookierun'], 25)

        bbox = draw.textbbox((0, 0), result_text, font=result_font)
        
        # 텍스트 실제 너비와 높이 계산
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        result_x = (recent_x - text_width) / 2
        result_y = (recent_y - text_height)
        draw.text((result_x, result_y - recent_y // 10), result_text, fill=f"{'gold' if is_win else 'silver'}", font=result_font)

        return result_per_champion_image

    recent_textbox = get_textbox(recent_x * 4, recent_y, f"최근 전적 : ", font_paths["cookierun"], font_color='black')

    recent_result_image.paste(recent_textbox, (0, 0))

    count = 0

    for index, (match_id, game_index, champion_eng, line, result) in enumerate(recent_result):

        if count >= 20:
            break

        is_win = True if result == "승리" else False

        if champion_eng is None or champion_eng == "" or champion_eng == "None":
            continue

        recent_result_image.paste(get_result_per_champion(match_id, game_index, champion_eng, line, is_win), (recent_x * 4 + recent_x * count, 0))

        count += 1

    return recent_result_image
