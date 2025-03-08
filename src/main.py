import json
import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
import requests
from record import *
from functions import *
from magics import *
from bot import bot

# 테스트 할때 아래 사용
load_dotenv()
# GitHub Secrets에서 가져오는 값
TOKEN = os.getenv('DISCORD_TOKEN')


@bot.event
async def on_ready():
    await bot.tree.sync()  # 슬래시 명령어 동기화


@bot.tree.command(name="전적")
async def find_record(interaction: discord.Interaction, member: discord.Member = None):
    await interaction.response.defer()

    if interaction.channel_id != 1347946316902436864:
        return

    if member is None:
        member = interaction.user

    profile_embed = discord.Embed(
        title=f"[ LOLPARK 2025 SPRING SEASON ]",
        description=get_summarized_record_text(member),
        color=discord.Color.pink()
    )

    icon_url = member.avatar.url if member.avatar else member.default_avatar.url
    profile_embed.set_author(name=get_nickname(member), icon_url=icon_url)

    await interaction.followup.send(embed=profile_embed)


@bot.command()
@commands.is_owner()
async def 상세전적(ctx, member: discord.Member = None):

    if member is None:
        member = ctx.author

    id = member.id
    lane_stats = get_champions_by_lane_with_winrate(id)

    result_str = f"# {get_nickname(member)} 상세 전적\n"

    for line, stats in lane_stats.items():
        line_eng_to_kor = {
            "top": "탑",
            "jungle": "정글",
            "mid": "미드",
            "bot": "원딜",
            "support": "서폿"
        }
        result_str += f"\n## {line_eng_to_kor[line]}\n\n"
        for index, stat in enumerate(stats, start=1):
            if index <= 3:
                result_str += f"### "
            result_str += f"{index}. {get_full_champion_kor_name(stat['champion'])}: {stat['total_games']}전 {stat['wins']}승 {stat['loses']}패 (승률 {stat['win_rate']}%)\n"

    await ctx.send(result_str)


@bot.command()
async def 임시전적(ctx, member: discord.Member = None):

    if member is None:
        member = ctx.author

    id = member.id
    summoner_stats_by_channel = get_summoner_stats_by_channel(id)

    result_str = f"# {get_nickname(member)} 채널별 전적\n\n"

    for channel_id, channel_result in summoner_stats_by_channel.items():
        result_str += f"### {convert_channel_id_to_name(channel_id)}\n\n"
        result_str += f"{channel_result['total_games']}전 {channel_result['wins']}승 {channel_result['loses']}패 ({channel_result['win_rate']}%)\n\n"

    await ctx.send(result_str)


# 명령어 에러 처리
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f"Unhandled error: {error}")


def main() -> None:
    bot.run(token=TOKEN)


if __name__ == '__main__':
    main()
