import config
import functions
from bot import bot

# 특정 시간에 함수를 실행하는 Task
async def update_lolpark_record_message(date=""):

    import record

    # 업데이트 채널 가져오기
    total_record_channel = bot.get_channel(config.total_record_channel_id)

    # 총 게임 수
    total_game_count = record.get_total_games()

    def get_record_message(is_pick: bool):
        total_record = record.get_total_pick_and_ban(is_pick=is_pick)
        record_message = f"# {config.now_season} 시즌 {'PICK' if is_pick else 'BAN'} TOP 30 (LAST UPDATE : {date})\n\n"

        for idx, champion_dict in enumerate(total_record, start=1):
            
            if idx > 30:
                break # 50개까지만 가져오기 (디스코드 메세지 길이 제한)

            champion_eng = champion_dict["champion"]
            champion_count = champion_dict["total_count"]

            champion_rate = round((champion_count / total_game_count) * 100, 2)

            record_message += f"{idx}위 : {functions.get_full_champion_kor_name(champion_eng)}, {champion_count}회 ({champion_rate}%)\n"

        return record_message

    # 수정할 메세지 데이터 가져오기
    total_ban_content = get_record_message(is_pick=False)
    total_pick_content = get_record_message(is_pick=True)

    # 수정할 메세지 ID 가져오기
    total_ban_message = await total_record_channel.fetch_message(config.total_record_ban_message_id)
    total_pick_message = await total_record_channel.fetch_message(config.total_record_pick_message_id)

    await total_ban_message.edit(content=total_ban_content)
    await total_pick_message.edit(content=total_pick_content)
