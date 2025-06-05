import config
import functions
import discord
from bot import bot

async def update_lolpark_record_message(date=""):

    import record

    # 업데이트 채널 가져오기
    total_record_channel = bot.get_channel(config.total_record_channel_id)

    start_id, end_id = config.division_matchid_dict[config.now_season]

    # 총 게임 수
    total_game_count = record.get_total_games(start_id, end_id)

    def get_record_message(is_pick: bool):
        total_record = record.get_total_pick_and_ban(is_pick=is_pick, start_id=start_id, end_id=end_id)
        record_message = f"# {config.now_season} 시즌 {'PICK' if is_pick else 'BAN'} TOP 30 (LAST UPDATE : {date})\n\n"

        for idx, champion_dict in enumerate(total_record, start=1):
            
            if idx > 30:
                break # 30개까지만 가져오기 (디스코드 메세지 길이 제한)

            champion_eng = champion_dict["champion"]
            champion_count = champion_dict["total_count"]

            if champion_eng == "none" or champion_eng == "None":
                idx -= 1
                continue

            champion_rate = round((champion_count / total_game_count) * 100, 2)

            record_message += f"{idx}위 : {functions.get_full_champion_kor_name(champion_eng)}, {champion_count}회 ({champion_rate}%)\n"

        return record_message

    # 메시지 내용 생성
    total_ban_content = get_record_message(is_pick=False)
    total_pick_content = get_record_message(is_pick=True)

    # BAN 메시지 처리
    try:
        if hasattr(config, 'total_record_ban_message_id') and config.total_record_ban_message_id:
            # 기존 메시지가 있으면 수정 시도
            total_ban_message = await total_record_channel.fetch_message(config.total_record_ban_message_id)
            await total_ban_message.edit(content=total_ban_content)
            print(f"BAN 메시지 수정 완료: {config.total_record_ban_message_id}")
        else:
            # 메시지 ID가 없으면 새로 생성
            raise ValueError("메시지 ID 없음")
    except (discord.NotFound, ValueError, AttributeError):
        # 메시지를 찾을 수 없거나 ID가 없으면 새로 생성
        new_ban_message = await total_record_channel.send(total_ban_content)
        config.total_record_ban_message_id = new_ban_message.id
        print(f"새 BAN 메시지 생성: {new_ban_message.id}")

    # PICK 메시지 처리
    try:
        if hasattr(config, 'total_record_pick_message_id') and config.total_record_pick_message_id:
            # 기존 메시지가 있으면 수정 시도
            total_pick_message = await total_record_channel.fetch_message(config.total_record_pick_message_id)
            await total_pick_message.edit(content=total_pick_content)
            print(f"PICK 메시지 수정 완료: {config.total_record_pick_message_id}")
        else:
            # 메시지 ID가 없으면 새로 생성
            raise ValueError("메시지 ID 없음")
    except (discord.NotFound, ValueError, AttributeError):
        # 메시지를 찾을 수 없거나 ID가 없으면 새로 생성
        new_pick_message = await total_record_channel.send(total_pick_content)
        config.total_record_pick_message_id = new_pick_message.id
        print(f"새 PICK 메시지 생성: {new_pick_message.id}")