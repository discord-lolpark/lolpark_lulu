import discord
from discord.ext import commands
from discord import app_commands
from lolparklib import get_summoner_rank, get_solo_rank_simple

class PositionSelect(discord.ui.Select):
    def __init__(self, riot_id: str, summoner_name: str):
        self.riot_id = riot_id
        self.summoner_name = summoner_name
        
        options = [
            discord.SelectOption(label='탑', value='탑'),
            discord.SelectOption(label='정글', value='정글'),
            discord.SelectOption(label='미드', value='미드'),
            discord.SelectOption(label='원딜', value='원딜'),
            discord.SelectOption(label='서폿', value='서폿'),
        ]
        
        super().__init__(
            placeholder="포지션을 선택해주세요 (여러 개 선택 가능)",
            min_values=1,
            max_values=5,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_positions = self.values


        # 15-1 최고 티어
        recent_season_result = get_solo_rank_simple(self.summoner_name)
        recent_season_high_tier = f'{str(recent_season_result["tier"]).upper()} {str(recent_season_result["score"])}' if recent_season_result["tier"] != 'unranked' else 'UNRANKED'
        # 14-3 최고 티어
        prev_season_result = get_summoner_rank(self.summoner_name)
        prev_season_high_tier = f'{str(prev_season_result["tier"]).upper()} {str(prev_season_result["score"])}' if prev_season_result["tier"] != 'unranked' else 'UNRANKED'
        
        from lolparklib import enroll_new_summoner_lane, update_high_tier
        enroll_new_summoner_lane(interaction.user, selected_positions)

        if not update_high_tier(interaction.user):
            await interaction.response.send_message(
                content=f"오류가 발생했습니다. 티켓으로 문의 부탁드립니다.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="소환사 등록 완료",
            description="등록이 성공적으로 완료되었습니다!",
            color=discord.Color.green()
        )
        embed.add_field(name="Riot ID", value=self.riot_id, inline=False)
        embed.add_field(name="소환사명", value=self.summoner_name, inline=False)
        embed.add_field(name="선택된 포지션", value=", ".join(selected_positions), inline=False)
        embed.add_field(name="14-3 최고 티어", value=prev_season_high_tier, inline=False)
        embed.add_field(name="15-1 최고 티어", value=recent_season_high_tier, inline=False)
        
        await interaction.response.edit_message(embed=embed, view=None)

class PositionSelectView(discord.ui.View):
    def __init__(self, riot_id: str, summoner_name: str):
        super().__init__(timeout=600)
        self.add_item(PositionSelect(riot_id, summoner_name))

class SummonerModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title='소환사 등록')

    riot_id = discord.ui.TextInput(
        label='Riot ID를 입력해주세요. (롤 로그인 시 입력하는 ID)',
        placeholder='예: crayonly1123',
        required=True,
        max_length=50
    )
    
    summoner_name = discord.ui.TextInput(
        label='현재 소환사 닉네임을 닉네임#태그 양식으로 입력해주세요.',
        placeholder='예: 마술사의 수습생 #KR1',
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # 먼저 defer로 시간 확보
            await interaction.response.defer(ephemeral=True)
            
            from lolparklib import enroll_new_summoner, get_enrolled_summoner, is_lane_enrolled, update_high_tier
            
            # API 호출을 try-except로 감싸기
            try:
                enroll_new_summoner(interaction.user, self.riot_id.value, self.summoner_name.value)
            except Exception as e:
                await interaction.followup.send(f"소환사 등록 중 오류가 발생했습니다: {str(e)}", ephemeral=True)
                return
                
            enrolled_id = get_enrolled_summoner(interaction.user)
            is_enrolled = is_lane_enrolled(interaction.user)
            
            if is_enrolled:
                try:
                    update_high_tier(interaction.user)
                    # 15-1 최고 티어
                    recent_season_result = get_solo_rank_simple(self.summoner_name.value)
                    recent_season_high_tier = f'{str(recent_season_result["tier"]).upper()} {str(recent_season_result["score"])}' if recent_season_result["tier"] != 'unranked' else 'UNRANKED'
                    # 14-3 최고 티어
                    prev_season_result = get_summoner_rank(self.summoner_name.value)
                    prev_season_high_tier = f'{str(prev_season_result["tier"]).upper()} {str(prev_season_result["score"])}' if prev_season_result["tier"] != 'unranked' else 'UNRANKED'
                    await interaction.followup.send(
                        content=f"소환사 추가 등록이 완료되었습니다.\n\nRiot ID : {self.riot_id.value}\n소환사명 : {self.summoner_name.value}\n14 - 3 최고 티어 : {prev_season_high_tier}\n15 - 1 최고 티어 : {recent_season_high_tier}",
                        ephemeral=True
                    )
                except Exception as e:
                    await interaction.followup.send(f"티어 정보 조회 중 오류: {str(e)}", ephemeral=True)
                return
                
            # 초기 등록인 경우도 동일하게 처리
            embed = discord.Embed(
                title="포지션 선택",
                description="드롭다운에서 플레이할 포지션을 선택해주세요.\n여러 개 선택 가능합니다!",
                color=discord.Color.blue()
            )
            view = PositionSelectView(self.riot_id.value, self.summoner_name.value)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"오류가 발생했습니다: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"오류가 발생했습니다: {str(e)}", ephemeral=True)