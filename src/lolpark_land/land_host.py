import discord
import lolpark_land.land_functions

async def register_user(interaction: discord.Interaction):

    """
    /등록 사용 시 적용. 등록되어 있으면 false 반환, 성공 시 true 반환
    """
    
    from lolpark_land.land_database import execute_select_query, execute_post_query

    await interaction.response.defer()

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
    user_lolpark_coin = land_functions.get_lolpark_coin(user)
    
    # 4. 사용자 등록 쿼리 작성 및 실행
    insert_query = "INSERT INTO users (user_id, lolpark_coin) VALUES (?, ?)"
    if not execute_post_query(insert_query, (user_id, user_lolpark_coin)):
        await interaction.followup.send(f"사용자 등록 중 오류가 발생했습니다.", ephemeral=True)
        return False
    
    return True
