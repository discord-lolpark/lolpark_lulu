import discord
import lolpark_land.land_functions
from lolpark_land.land_database import execute_select_query, execute_post_query


async def register_user(interaction: discord.Interaction):
    """
    /등록 사용 시 적용. 등록되어 있으면 false 반환, 성공 시 true 반환
    """
    user = interaction.user
    user_id = user.id

    # 1. 사용자가 이미 등록되어 있는지 확인
    check_query = "SELECT user_id FROM users WHERE user_id = ?"
    result = execute_select_query(check_query, (user_id,))
    
    # 2. 이미 등록되어 있다면 False 반환
    if result:
        await interaction.followup.send(f"이미 등록된 사용자입니다.", ephemeral=True)
        return False
    
    # 3. 등록되어 있지 않다면 외부 함수로 코인 정보 가져오기
    user_lolpark_coin = lolpark_land.land_functions.get_lolpark_coin(user)
    
    # 4. 프리미엄 역할 확인 및 코인 5배 지급
    has_premium = discord.utils.get(user.roles, name="LOLPARK PREMIUM")
    if has_premium:
        user_lolpark_coin *= 5
        print(f"[INFO] 프리미엄 사용자 {user.display_name}에게 5배 코인 지급: {user_lolpark_coin}")
    
    # 5. 사용자 등록 쿼리 작성 및 실행
    insert_query = "INSERT INTO users (user_id, lolpark_coin) VALUES (?, ?)"
    if not execute_post_query(insert_query, (user_id, user_lolpark_coin)):
        await interaction.followup.send(f"사용자 등록 중 오류가 발생했습니다.", ephemeral=True)
        return False
    
    # 6. LOLPARKLAND 역할 부여
    try:
        guild = interaction.guild
        lolparkland_role = discord.utils.get(guild.roles, name="LOLPARKLAND")
        
        if lolparkland_role:
            await user.add_roles(lolparkland_role)
            print(f"[INFO] {user.display_name}에게 LOLPARKLAND 역할 부여 완료")
        else:
            print(f"[WARNING] LOLPARKLAND 역할을 찾을 수 없습니다.")
            # 역할이 없어도 등록은 성공으로 처리
    except discord.Forbidden:
        print(f"[ERROR] 역할 부여 권한이 없습니다.")
    except discord.HTTPException as e:
        print(f"[ERROR] 역할 부여 중 오류: {e}")
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
    
    return True