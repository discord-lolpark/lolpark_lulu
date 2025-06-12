import discord
from functions import get_nickname, get_nickname_without_tag

# 티어조정 카테고리 id
tier_adjust_category_id = 1358075007942791339

async def apply_tier_adjust(interaction: discord.Interaction, member: discord.Member=None):

    is_own = False

    # 본인 신청의 경우, 본인으로 변경
    if member is None:
        member = interaction.user
        is_own = True

    # 채널 생성. 채널의 경우 자문단만 볼 수 있음.
    try:
        guild = interaction.guild
        
        # 역할 찾기
        advisor_role = discord.utils.get(guild.roles, name="티어 조정 자문단")
        
        # 역할이 없는 경우 처리
        if advisor_role is None:
            await interaction.channel.send("'자문단' 역할을 찾을 수 없습니다.")
            return
        
        # 권한 설정
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),  # 기본적으로 모두 볼 수 없음
            advisor_role: discord.PermissionOverwrite(view_channel=True),          # 자문단 역할은 볼 수 있음
            guild.me: discord.PermissionOverwrite(view_channel=True),              # 봇은 볼 수 있음
            interaction.user: discord.PermissionOverwrite(view_channel=True),      # 신청자는 볼 수 있음
        }

        # 카테고리 가져오기
        tier_category = discord.utils.get(guild.categories, id=tier_adjust_category_id)

        # 채널 생성 시 권한 설정 적용
        tier_adjust_channel = await tier_category.create_text_channel(
            name=f"{get_nickname_without_tag(member)} 티어조정",
            overwrites=overwrites
        )

    except discord.Forbidden:
        await interaction.channel.send("봇에 채널을 생성하거나 권한을 설정할 권한이 없습니다.", delete_after=1800)
    except discord.HTTPException as e:
        await interaction.channel.send(f"채널 생성 중 오류가 발생했습니다: {e}", delete_after=1800)

    await tier_adjust_channel.send(f"# {get_nickname(member)}님에 대한 티어조정 신청입니다.\n"
                                   f"{'### 본인 신청입니다.' if is_own else f'### {get_nickname(interaction.user)}님의 신청입니다.'}")
    