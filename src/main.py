import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from record import *
from functions import *
from magics import *
from bot import bot
from lolpark_premium import lolpark_premium

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

    lolpark_premium_role = discord.utils.get(member.roles, name='LOLPARK PREMIUM')

    if lolpark_premium_role:
        profile = await lolpark_premium(member)

        buffer = io.BytesIO()
        profile.save(buffer, format='PNG')
        buffer.seek(0)

        await interaction.followup.send(file=discord.File(buffer, filename=f"{member.id}_profile.png"))

        class PremiumView(discord.ui.View):
            def __init__(self, member):  # async 제거
                super().__init__(timeout=180)
                self.message = None
                self.member = member  # 멤버 저장
                self.add_item(MostPickButton())
                self.add_item(MostBannedButton())

            async def on_timeout(self):
                try:
                    await self.message.delete()
                except discord.NotFound:
                    pass
                except Exception as e:
                    print(f"오류 발생 : {e}")

        class MostPickButton(discord.ui.Button):
            def __init__(self):
                super().__init__(label="가장 많이 픽한 챔피언", style=discord.ButtonStyle.primary)
            
            async def callback(self, interaction):  # 콜백 메서드 추가
                # 여기서 버튼이 클릭되었을 때 실행될 코드
                view = self.view
                await interaction.response.send_message(get_picked_by_lane_text(view.member), ephemeral=True)

        class MostBannedButton(discord.ui.Button):
            def __init__(self):
                super().__init__(label="가장 많이 밴한 챔피언", style=discord.ButtonStyle.danger)
            
            async def callback(self, interaction):  # 콜백 메서드 추가
                # 여기서 버튼이 클릭되었을 때 실행될 코드
                view = self.view
                await interaction.response.send_message(get_banned_by_lane_text(view.member), ephemeral=True)

        # 사용 예시
        premium_view = PremiumView(member)
        premium_view.message = await interaction.followup.send(
            content="## 롤파크 프리미엄 추가 기능", 
            view=premium_view,  # 새 인스턴스 생성 대신 기존 인스턴스 사용
            ephemeral=True
        )
    else:
        profile_embed = discord.Embed(
            title=f"[ LOLPARK 2025 SPRING SEASON ]",
            description=get_summarized_record_text(member),
            color=discord.Color.pink()
        )

        icon_url = member.avatar.url if member.avatar else member.default_avatar.url
        profile_embed.set_author(name=get_nickname(member), icon_url=icon_url)

        await interaction.followup.send(embed=profile_embed)


@bot.command()
@commands.has_role("LOLPARK PREMIUM")
async def 상세전적(ctx):    

    member = ctx.author

    profile = await lolpark_premium(member)

    buffer = io.BytesIO()
    profile.save(buffer, format='PNG')
    buffer.seek(0)

    await ctx.send(file=discord.File(buffer, filename=f"{member.id}_profile.png"))


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


@bot.command()
@commands.has_role("LOLPARK PREMIUM")
async def 모스트밴(ctx):

    id = ctx.author.id

    await ctx.send(get_most_banned_text())


@bot.command()
@commands.has_role("LOLPARK PREMIUM")
async def 라인별밴(ctx, member: discord.Member = None):
    return
    member = ctx.author

    await ctx.send(get_banned_by_lane_text(member))


@bot.command()
@commands.has_role("LOLPARK PREMIUM")
async def 라인별픽(ctx, member: discord.Member = None):
    return
    member = ctx.author

    await ctx.send(get_picked_by_lane_text(member))



@bot.command()
@commands.has_role("관리자")
async def 내전정보(ctx, match_id: int):

    match_summoner_ids = get_summoners_by_match(match_id)

    lolpark = bot.get_guild(1287065134652457020)

    match_text = f'## 내전 #{match_id}에 참여한 소환사 목록입니다.\n\n'

    match_text += f'### 1팀\n\n'
    for id in match_summoner_ids['team_1']:
        match_text += f'{get_nickname(lolpark.get_member(id))}\n'
    
    match_text += f'\n### 2팀\n\n'
    for id in match_summoner_ids['team_2']:
        match_text += f'{get_nickname(lolpark.get_member(id))}\n'

    await ctx.send(match_text)




@bot.command()
@commands.is_owner()
async def 죽어라마술사(ctx):
    await ctx.send("아.")
    await bot.close()


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
