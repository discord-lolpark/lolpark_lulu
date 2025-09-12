
import discord
import aiohttp
import io
import asyncio
from lolparklib.database_functions import (
    get_summoner_stats
)
from lolparklib.discord_config import (
    lolpark_season,
    season_name_list,
    cup_name_list
)
from PIL import Image, ImageDraw, ImageFont
from lolparklib.discord_functions import get_nickname, get_user_tier_part
from lolparklib.image_functions import *
from lolparklib.record_functions import get_recent_champion_history

asset_dir = "assets"
w = 1920
h = 1080
profile_image_size = (160, 160)
champion_image_size = 88


async def get_lolpark_premium_profile(member: discord.Member, season_name: str):

    profile_image = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(profile_image)

    # 배경 이미지
    background_image = Image.open(f"{asset_dir}/lolpark_images/record_background.png").convert("RGBA")
    profile_image.paste(background_image, (0, 0))

    # 시즌 텍스트
    draw.text(
        xy=(370, 50),
        text=f"[ {season_name} ]",
        font=ImageFont.truetype(f"{asset_dir}/fonts/NotoSansKR.ttf", 25),
        fill="#252121"
    )

    #### 멤버 프로필 ####

    # 멤버 프로필 이미지
    member_profile_image = make_rounded(await get_profile_image(member), radius=20)
    member_profile_image = member_profile_image.resize(profile_image_size, Image.LANCZOS)
    profile_image.paste(member_profile_image, (180, 160), member_profile_image)

    # 멤버 티어 정보
    tier_initial, tier_score = get_user_tier_part(member)

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

    member_tier_image = Image.open(f"{asset_dir}/tier_image/icon/{tier}.png").convert("RGBA").resize((160, 160), Image.LANCZOS)
    profile_image.paste(member_tier_image, (380, 130), member_tier_image)
    tier_text = "[" + tier_initial.upper() + str(tier_score) + "]"
    tier_textbox = get_textbox_image(tier_text, 160, 60, font_color="#FFFFFF", font_path=f"{asset_dir}/fonts/nanumgothic.ttf")
    profile_image.paste(tier_textbox, (380, 260), tier_textbox)

    # 멤버 닉네임
    nickname = get_nickname(member, only_nickname=True)
    nickname_textbox = get_nickname_textbox_image(nickname, 380, 120, font_color="#FFFFFF", font_path=f"{asset_dir}/fonts/nanumgothic.ttf")
    profile_image.paste(nickname_textbox, (170, 300), nickname_textbox)

    left_start_x = 160

    # 전체 내전 전적
    stat_dict = get_summoner_stats(member, season_name=season_name)
    total_games = stat_dict["total_games"]
    total_win = stat_dict["wins"]
    total_lose = stat_dict["loses"]
    total_winrate = stat_dict["win_rate"]
    total_record_text = f'{total_games}전 {total_win}승 {total_lose}패 ( {total_winrate}% )'
    total_record_textbox = get_textbox_image(total_record_text, 550, 55, font_color="#FFFFFF", font_path=f"{asset_dir}/fonts/nanumgothic.ttf")
    profile_image.paste(total_record_textbox, (140, 515), total_record_textbox)

    # 최근 전적
    recent_result = get_recent_champion_history(member.id, season_name, limit=15)
    
    recent_win_count = 0
    recent_lose_count = 0

    for index, game_info in enumerate(recent_result):
        
        row_count = 5

        match_id = game_info[0]
        game_index = game_info[1]
        champion_name_eng = game_info[2]
        is_win = True if game_info[4] == "승리" else False


        game_info_textbox_height = 40

        champion_image = Image.open(f"{asset_dir}/champion_square/{champion_name_eng}.png").convert("RGBA").resize((champion_image_size, champion_image_size), Image.LANCZOS)

        game_info_textbox = get_textbox_image(f"#{match_id}({game_index})", champion_image_size, game_info_textbox_height, font_color="#FFFFFF", font_path=f"{asset_dir}/fonts/NotoHans.ttf")

        profile_image.paste(champion_image, (left_start_x + (index % row_count) * champion_image_size, 645 + (index // row_count) * (champion_image_size + game_info_textbox_height) + game_info_textbox_height), champion_image)
        profile_image.paste(game_info_textbox, (left_start_x + (index % row_count) * champion_image_size, 645 + (index // row_count) * (champion_image_size + game_info_textbox_height)), game_info_textbox)
        if is_win:
            draw.text(
                xy =(left_start_x + (index % row_count) * champion_image_size + 29, 645 + (index // row_count + 1) * (champion_image_size + game_info_textbox_height) - 30),
                text="W",
                font=ImageFont.truetype(f"{asset_dir}/fonts/nanumgothic.ttf", 30),
                fill="#FFE927"
            )
        else:
            draw.text(
                xy =(left_start_x + (index % row_count) * champion_image_size + 34, 645 + (index // row_count + 1) * (champion_image_size + game_info_textbox_height) - 30),
                text="L",
                font=ImageFont.truetype(f"{asset_dir}/fonts/nanumgothic.ttf", 30),
                fill="#F1EDC7"
            )


        recent_win_count += 1 if is_win else 0
        recent_lose_count += 0 if is_win else 1
    
    recent_record_text = f'{recent_win_count + recent_lose_count}전 {recent_win_count}승 {recent_lose_count}패 ( {calculate_win_rate(recent_win_count, recent_lose_count)}% )'
    recent_record_textbox = get_textbox_image(recent_record_text, 350, 55, font_color="#DBD1D1", font_path=f"{asset_dir}/fonts/nanumgothic.ttf")
    profile_image.paste(recent_record_textbox, (340, 590), recent_record_textbox)

    return profile_image


# 승률 계산
def calculate_win_rate(win: int, lose: int) -> float:
    if win + lose == 0:  # 경기가 없는 경우 승률 0% 반환
        return 0.0
    win_rate = (win / (win + lose)) * 100
    return round(win_rate, 2)  # 소수점 셋째 자리에서 반올림


async def send_tier_adjust_profile(channel, user: discord.Member):

    try:
        # 시즌별 프로필 전송
        for season_name in season_name_list:

            season_games = get_summoner_stats(user, season_name=season_name)["total_games"]

            if season_games > 0:
                try:
                    season_profile = await get_lolpark_premium_profile(user, season_name)
                    with io.BytesIO() as season_buffer:
                        season_profile.save(season_buffer, format='PNG')
                        season_buffer.seek(0)
                        await channel.send(file=discord.File(season_buffer, filename=f"{season_name}_profile.png"))
                except Exception as e:
                    print(f"{season_name} 프로필 생성 실패: {e}")
                    continue

    except Exception as e:
        print(f"프로필 전송 중 오류 발생: {e}")
        await channel.send("프로필 생성 중 오류가 발생했습니다. 전적이 없을 가능성이 있습니다.")
    


# 요약 전적 가져오기 (/전적 사용시, 일반 서버원)
def get_summarized_record_text(user: discord.member, season: str=lolpark_season):

    stat_dict = get_summoner_stats(user, season_name=season)

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
            self.other_buttons_count = 0  # row 2 이상에 배치될 버튼 개수 추적

        def get_button_row(self, season):
            if season == lolpark_season:
                return 1  # 현재 시즌
            elif season == "통산":
                return 0  # 통산
            else:
                # 나머지 버튼들을 row 2, 3, 4에 5개씩 분산
                row = 2 + (self.other_buttons_count // 5)
                self.other_buttons_count += 1
                return row

        async def on_timeout(self):
            if not self.future.done():
                self.future.set_result(None)
            try:
                await self.message.delete()
            except discord.NotFound:
                pass

    class StatButton(discord.ui.Button):
        def __init__(self, season, member, future, view):
            button_style = discord.ButtonStyle.green if season == lolpark_season else discord.ButtonStyle.red if season == "통산" else discord.ButtonStyle.primary
            row = view.get_button_row(season)
            super().__init__(label=f"{season} (현재 시즌)" if season == lolpark_season else season, style=button_style, row=row)
            self.member = member
            self.season = season
            self.future = future
        
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            profile = await get_lolpark_premium_profile(self.member, self.season)

            if not self.future.done():
                self.future.set_result(profile)
            
        
    stat_view = LolparkPremiumStatView(member, result_future)

    current_season_games = get_summoner_stats(member, lolpark_season)["total_games"]

    if current_season_games > 0:
        stat_view.add_item(StatButton(lolpark_season, member, result_future, stat_view))

    for season_name in season_name_list:
        if season_name == lolpark_season:
            continue

        season_games = get_summoner_stats(member, season_name)["total_games"]

        if season_games > 0:
            stat_view.add_item(StatButton(season_name, member, result_future, stat_view))

    for cup_name in cup_name_list:
        cup_games = get_summoner_stats(member, cup_name)["total_games"]

        if cup_games > 0:
            stat_view.add_item(StatButton(cup_name, member, result_future, stat_view))
    
    return stat_view, result_future




def get_textbox_image(text, x, y, font_color="#ECE4E4", font_path=f"{asset_dir}/fonts/Nickname.ttf"):

    x_padding = 10
    y_padding = 7
    # 투명한 배경으로 생성
    nickname_textbox_image = Image.new('RGBA', (x, y), (0, 0, 0, 0))  # 완전 투명
    draw = ImageDraw.Draw(nickname_textbox_image)
    
    max_font_size = 100
    min_font_size = 10
    font_size = max_font_size

    while font_size >= min_font_size:
        font = ImageFont.truetype(font_path, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        if text_width <= x - x_padding * 2 and text_height <= y - y_padding * 2:
            break
        font_size -= 2

    # 실제 텍스트 렌더링 영역 기준으로 중앙 정렬
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # X축 중앙 정렬
    text_x = (x - text_width) // 2
    
    # Y축 진짜 중앙 정렬 (베이스라인 보정)
    text_y = (y - text_height) // 2 - bbox[1]  # bbox[1]이 음수라서 빼면 위로 올라감
    
    # 텍스트에 따른 추가 보정
    if any('\uac00' <= char <= '\ud7af' for char in text):  # 한글 포함
        text_y += 2  # 한글은 살짝 아래로
    else:  # 영어만
        text_y += 0  # 영어는 보정 없음

    # 배경은 투명하게 (이 줄 제거)
    # draw.rectangle([0, 0, x, y], fill=winlose_background_color)

    # 텍스트만 추가
    draw.text((text_x, text_y), text, fill=font_color, font=font)

    return nickname_textbox_image