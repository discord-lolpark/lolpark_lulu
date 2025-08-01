from asyncio import Future
import sys
import os
import discord
import io
from dotenv import load_dotenv
from discord.ext import commands
from bot import bot
from lolpark_premium import get_premium_record, get_summarized_record_text

# os path 설정
def _setup_imports():
    parent_path = os.path.join(os.path.dirname(__file__), '..', '..')
    if parent_path not in sys.path:
        sys.path.append(parent_path)

_setup_imports()
from lolparklib import *


# 테스트 할때 아래 사용
load_dotenv()
# GitHub Secrets에서 가져오는 값
LULU_TOKEN = os.getenv('LULU_TOKEN')


@bot.event
async def on_ready():
    await bot.tree.sync()


@bot.tree.command(name="전적")
async def find_record(interaction: discord.Interaction, member: discord.Member = None):

    await interaction.response.defer(ephemeral=(interaction.channel_id == record_search_channel_private_id))
    
    if member is None:
        member = interaction.user

    if interaction.channel_id not in [record_search_channel_administrator_id, record_search_channel_public_id, record_search_channel_private_id]:
        await interaction.followup.send(
            content=(
                f'<#{record_search_channel_public_id}> 또는 <#{record_search_channel_private_id}> 에서 전적을 조회해주세요.'
            ),
            ephemeral=True
        )
        return
    
    # 프리미엄 프로필 생성 및 전송하는 함수
    async def send_premium_profile():
        stat_view, future = await get_premium_record(member)
        message = await interaction.followup.send("시즌을 선택하세요:", view=stat_view, ephemeral=True)
        stat_view.message = message
        profile: Future = await future
        await stat_view.message.delete()
        buffer = io.BytesIO()
        profile.save(buffer, format='PNG')
        buffer.seek(0)
        await interaction.followup.send(
            file=discord.File(buffer, filename=f"{member.id}_profile.png"),
            ephemeral=interaction.channel_id == record_search_channel_private_id
        )
        
    # 일반 프로필 생성 및 전송하는 함수
    async def send_standard_profile():
        profile_embed = discord.Embed(
            title=f"[ {lolpark_season} ]",
            description=get_summarized_record_text(member),
            color=discord.Color.blue()
        )
        icon_url = member.avatar.url if member.avatar else member.default_avatar.url
        profile_embed.set_author(name=get_nickname(member), icon_url=icon_url)
        await interaction.followup.send(embed=profile_embed)

    # 관리자 채널: 항상 프리미엄 결과 표시
    if interaction.channel.id == record_search_channel_administrator_id:
        await send_premium_profile()
        return
    
    # 공개 채널
    if interaction.channel.id == record_search_channel_public_id:
        if get_match_played(interaction.user) >= 30:
            await send_premium_profile()
        else:
            await send_standard_profile()
    
    # 비공개 채널
    if interaction.channel.id == record_search_channel_private_id:
        if get_match_played(interaction.user) >= 30:
            await send_premium_profile()
        else:
            await interaction.followup.send(
                content=(
                    "현 시즌 30판 이상 플레이한 유저만 개인용 전적을 조회할 수 있습니다."
                ),
                ephemeral=True
            )


@bot.tree.command(name="티어조정신청")
async def apply(interaction: discord.Interaction, member: discord.Member = None):

    from tier_adjust.main_tier_adjust import apply_tier_adjust

    await interaction.response.defer(ephemeral=True)

    # 신고및문의에서 진행한게 아닌 경우, 무시
    if interaction.channel.id != 1287074399689904190:
        await interaction.followup.send(
        content=(
            f'<#1287074399689904190> 에서 신청해주시길 바랍니다.'
        ),
        ephemeral=True
    ) 

    channel_id = await apply_tier_adjust(interaction=interaction, member=member)
    await interaction.followup.send(
        content=(
            f"티어 조정 신청이 완료되었습니다.\n"
            f"<#{channel_id}> 로 이동하여 메세지 보내기"
        ),
        ephemeral=True
    )


@bot.command()
@commands.is_owner()
async def 기록삭제(ctx, match_id: int):
    try:
        delete_match_data(match_id)
        await ctx.send(f'{match_id}번 내전 기록을 삭제했습니다.')
    except Exception as e:
        await ctx.send(f'기록 삭제 중 오류가 발생했습니다.')


@bot.command()
@commands.is_owner()
async def 승패변경(ctx, match_id: int, game_number: int):

    if swap_game_winner(match_id, game_number):
        await ctx.send(f"내전 #{match_id} {game_number}번 게임 결과가 수정되었습니다.")


@bot.command()
@commands.is_owner()
async def 룰루봇종료(ctx):
    await ctx.send("아.")
    await bot.close()


@bot.command()
@commands.is_owner()
async def 테스트(ctx):
    return


@bot.tree.command()
async def 최근전적(interaction: discord.Interaction):

    await interaction.response.send_message(
        content="준비 중입니다.",
        ephemeral=True
    )
    return

    from last_record import get_personal_game_result_image

    result_image = get_personal_game_result_image(interaction)

    buffer = io.BytesIO()
    result_image.save(buffer, format='PNG')
    buffer.seek(0)

    await interaction.channel.send(file=discord.File(buffer, filename=f"test.png"))


# 명령어 에러 처리
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f"Unhandled error: {error}")


def main() -> None:
    bot.run(token=LULU_TOKEN)


if __name__ == '__main__':
    main()
