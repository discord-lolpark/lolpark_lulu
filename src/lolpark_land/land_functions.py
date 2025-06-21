import discord
from record import get_summoner_stats
from lolpark_land.land_database import execute_select_query, execute_post_query
import random
from config import now_season, division_matchid_dict


def get_lolpark_coin(user: discord.Member):

    """
    초기 등록 시 롤파크 코인 얻는 함수
    """


    from config import now_season, division_matchid_dict

    (start_id, end_id) = division_matchid_dict[now_season]

    user_stats = get_summoner_stats(user, start_id, end_id)

    win = user_stats["wins"]
    lose = user_stats["loses"]

    return win * 300 + lose * 100


def draw_random_skin(user_id, box_type=None, line_type=None, is_most_pick=False, except_common=False):
    """
    모든 스킨 중에서 무작위로 하나를 뽑는 함수
    box_type이 지정되면 해당 스킨 라인에서만 뽑음
    line_type이 지정되면 해당 라인의 챔피언 스킨만 뽑음
    is_most_pick이 True면 모스트 픽 챔피언들만 뽑음
    """
    import random
    from lolpark_land.land_database import execute_select_query, execute_post_query
    
    # 레어리티별 가중치 설정 (높을수록 뽑힐 확률이 높음)
    RARITY_WEIGHTS = {
        'Common': 50,      # 가장 높은 확률
        'Rare': 40,         # 중간 확률
        'Epic': 12.5,         # 낮은 확률
        'Legendary': 8,     # 매우 낮은 확률
        'Mythic': 3,        # 극히 낮은 확률
        'Ultimate': 1,      # 최저 확률
        'Exalted': 0.5      # 최극히 낮은 확률
    }
    
    # 0. 기본 쿼리 작성
    query = """
    SELECT skin_id, champion_name_kr, champion_name_en, 
           skin_name_kr, skin_name_en, rarity, file_name
    FROM skins
    WHERE 1=1
    """
    params = []

    # 1. except_common 조건 추가 (대소문자 수정)
    if except_common:
        query += " AND rarity != ?"
        params.append('Common')  # 'common' -> 'Common'
    
    # 2. box_type 조건 추가 (테마 검색)
    if box_type:
        query += " AND (skin_name_kr LIKE ? OR skin_name_en LIKE ?)"
        params.append(f"%{box_type}%")
        params.append(f"%{box_type}%")
    
    # 3. line_type 조건 추가
    if line_type:
        try:
            from functions import get_champions_per_line, lol_champion_korean_dict
            print(f"라인 타입: {line_type}")
            champions = get_champions_per_line(line_type)
            champions_kr_list = [lol_champion_korean_dict[champion_en][0] for champion_en in champions]
            placeholders = ",".join(["?" for _ in champions_kr_list])
            query += f" AND champion_name_kr IN ({placeholders})"  # 한글 이름으로만 검색
            params.extend(champions_kr_list)
            print(f"[DEBUG] 라인 챔피언들 (한글): {champions_kr_list}")
        except ImportError as e:
            print(f"get_champions_per_line 함수 import 실패: {e}")
            return None
    
    # 4. is_most_pick 조건 추가
    if is_most_pick:
        try:
            from record import get_most_picked_champions
            from config import division_matchid_dict, now_season  # 실제 모듈명으로 변경 필요
            
            (start_id, end_id) = division_matchid_dict[now_season]
            most_pick_champions_info = get_most_picked_champions(user_id, start_id, end_id)
            most_pick_champions = []
            
            for index, info in enumerate(most_pick_champions_info):
                if index >= 5:
                    break
                most_pick_champions.append(info[0])
                
            if most_pick_champions:
                placeholders = ",".join(["?" for _ in most_pick_champions])
                query += f" AND (champion_name_kr IN ({placeholders}) OR champion_name_en IN ({placeholders}))"
                params.extend(most_pick_champions)
                params.extend(most_pick_champions)  # 한국어, 영어 둘 다
        except ImportError as e:
            print(f"모스트 픽 관련 함수 import 실패: {e}")
            return None
    
    print(f"[DEBUG] 최종 쿼리: {query}")
    print(f"[DEBUG] 파라미터: {params}")
    
    # 5. 쿼리 실행
    all_skins = execute_select_query(query, tuple(params) if params else None)
    
    # 6. 뽑을 수 있는 스킨이 없는 경우
    if not all_skins:
        print(f"[WARNING] 조건에 맞는 스킨이 없습니다.")
        return None
    
    print(f"[DEBUG] 조건에 맞는 스킨 수: {len(all_skins)}")
    
    # 7. 가중치를 적용한 무작위 스킨 선택
    weighted_skins = []
    
    for skin in all_skins:
        rarity = skin[5]  # rarity는 6번째 컬럼 (인덱스 5)
        weight = RARITY_WEIGHTS.get(rarity, 1)  # 기본 가중치 1
        
        # 가중치만큼 리스트에 추가 (소수점 처리를 위해 반복 횟수 조정)
        repeat_count = max(1, int(weight * 10))  # 소수점 가중치 처리
        for _ in range(repeat_count):
            weighted_skins.append(skin)
    
    # 가중치가 적용된 리스트에서 무작위 선택
    selected_skin = random.choice(weighted_skins)
    
    print(f"[DEBUG] 선택된 스킨: {selected_skin[3]} ({selected_skin[5]})")
    
    # 8. 선택된 스킨을 사용자에게 지급 (중복 허용)
    insert_query = "INSERT INTO user_skins (user_id, skin_id) VALUES (?, ?)"
    success = execute_post_query(insert_query, (user_id, selected_skin[0]))
    
    if success:
        # print(f"[SUCCESS] 스킨 지급 완료: {selected_skin[3]} ({selected_skin[1]})")
        # 스킨 정보를 딕셔너리로 반환
        return {
            "skin_id": selected_skin[0],
            "champion_name_kr": selected_skin[1],
            "champion_name_en": selected_skin[2],
            "skin_name_kr": selected_skin[3],
            "skin_name_en": selected_skin[4],
            "rarity": selected_skin[5],
            "file_name": selected_skin[6]
        }
    else:
        print(f"[ERROR] 스킨 지급 실패")
        return None
    

def get_skin_image_url(champion_name: str, file_name: str) -> str:
    """
    fileName을 기반으로 로컬 스킨 이미지 파일 경로를 생성
    """
    if not file_name or not champion_name:
        return None
    
    champion_name = champion_name.capitalize()
    file_name = file_name.capitalize()
    
    # 로컬 assets 폴더의 스킨 이미지 경로 (챔피언별 폴더)
    import os
    champion_path = f"lolpark_assets/splash/{champion_name}/{file_name}.jpg"
    image_path = f"C:/Users/Desktop/lolpark_githubs/{champion_path}" if os.path.exists(f"C:/Users/Desktop/lolpark_githubs/{champion_path}") else f"/{champion_path}"
    return image_path