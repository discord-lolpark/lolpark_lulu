################################################
################ 채널 ID 모음 ###################
################################################

# 전적 검색 채널
record_search_channel_administrator_id = 1361969506905358356
record_search_channel_public_id = 1347946316902436864
record_search_channel_private_id = 1362776969481027945

# 전체 통계 채널
total_record_channel_id = 1362780811618943006

# 대회 참가를 위한 횟수 확인용 채널
qualify_channel_id = 1364431449733857362


################################################
################ 잡동사니 모음 ###################
################################################

# 현재 시즌
now_season = "LOLPARK 2025 SPRING"

# 전체 통계 채널의 메세지 ID
total_record_ban_message_id = 1362788613359669468
total_record_pick_message_id = 1362788614911557854

# DB path
import os
matches_db = "C:/Users/Desktop/matches.db" if os.path.exists("C:/Users/Desktop/matches.db") else f"/database/matches.db"


# font_path들 모음
font_paths = {
    'cookierun': 'assets/fonts/CookieRun.ttf',
    'notosans': 'assets/fonts/NotoSansKR.ttf',
    'ownglyph': 'assets/fonts/Ownglyph.ttf',
    'pyeongchang': 'assets/fonts/pyeongchang.ttf',
    'gangwon': 'assets/fonts/gangwon.ttf',
    'jamsil': 'assets/fonts/Jamsil.ttf'
}


# 현재 시즌
now_season = "2025 SUMMER"

# 대회 코드별 이름
tournament_name_dict = {
    802: "2nd_low_tier",
    704: "4th_lolpark_cup"
}

# match_id별 시즌 분기
division_matchid_dict = {
    "2025 SPRING": (0, 1500),
    "2025 SUMMER": (1501, 3000),
    "제 2회 저티어 대회": (8020001, 8049999),
    "제 4회 이벤트 대회": (7040001, 7049999)
}