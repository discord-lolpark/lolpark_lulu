import discord


class TierAdjustVoteView(discord.ui.View):
    def __init__(self, member_name, target_channel):
        super().__init__(timeout=86400)  # 24시간
        self.member_name = member_name
        self.target_channel = target_channel
        self.votes = {"상승": {}, "유지": [], "하락": {}}  # 상승/하락은 {user: tier} 형태
    
    @discord.ui.button(label="티어 상승", style=discord.ButtonStyle.success, emoji="⬆️")
    async def vote_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TierInputModal("상승", self.member_name)
        modal.vote_view = self
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="티어 유지", style=discord.ButtonStyle.secondary, emoji="➡️")
    async def vote_maintain(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        
        # 기존 투표 제거
        self.remove_existing_vote(user_id)
        
        # 유지 투표 추가
        self.votes["유지"].append(user_id)
        
        await interaction.response.send_message(f"**{self.member_name}님**의 티어 **유지**에 투표했습니다.", ephemeral=True)
        await self.update_vote_display(interaction)
    
    @discord.ui.button(label="티어 하락", style=discord.ButtonStyle.danger, emoji="⬇️")
    async def vote_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TierInputModal("하락", self.member_name)
        modal.vote_view = self
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="투표 종료", style=discord.ButtonStyle.primary, emoji="🏁")
    async def end_vote(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 자문단만 투표 종료 가능
        advisor_role = discord.utils.get(interaction.guild.roles, name="티어 조정 자문단")
        if advisor_role not in interaction.user.roles:
            await interaction.response.send_message("자문단만 투표를 종료할 수 있습니다.", ephemeral=True)
            return
        
        await self.finalize_vote(interaction)
    
    def remove_existing_vote(self, user_id):
        # 기존 투표 제거
        if user_id in self.votes["상승"]:
            del self.votes["상승"][user_id]
        if user_id in self.votes["유지"]:
            self.votes["유지"].remove(user_id)
        if user_id in self.votes["하락"]:
            del self.votes["하락"][user_id]
    
    async def update_vote_display(self, interaction):
        total_votes = len(self.votes["상승"]) + len(self.votes["유지"]) + len(self.votes["하락"])
        
        embed = discord.Embed(
            title="🗳️ 티어 조정 투표 현황",
            description=f"**{self.member_name}님**의 티어 조정 투표\n\n"
                       f"총 투표 수: {total_votes}표",
            color=discord.Color.blue()
        )
        
        # 상승 투표 표시
        if self.votes["상승"]:
            up_text = "\n".join([f"• <@{user_id}>: {tier}" for user_id, tier in self.votes["상승"].items()])
            embed.add_field(name=f"⬆️ 상승 ({len(self.votes['상승'])}표)", value=up_text, inline=False)
        
        # 유지 투표 표시
        if self.votes["유지"]:
            maintain_text = "\n".join([f"• <@{user_id}>" for user_id in self.votes["유지"]])
            embed.add_field(name=f"➡️ 유지 ({len(self.votes['유지'])}표)", value=maintain_text, inline=False)
        
        # 하락 투표 표시
        if self.votes["하락"]:
            down_text = "\n".join([f"• <@{user_id}>: {tier}" for user_id, tier in self.votes["하락"].items()])
            embed.add_field(name=f"⬇️ 하락 ({len(self.votes['하락'])}표)", value=down_text, inline=False)
        
        try:
            await interaction.edit_original_response(embed=embed, view=self)
        except:
            pass
    
    async def finalize_vote(self, interaction):
        # 투표 결과 집계 및 최종 결과 표시
        embed = discord.Embed(
            title="🏁 티어 조정 투표 완료",
            description=f"**{self.member_name}님**의 티어 조정 투표가 완료되었습니다.",
            color=discord.Color.green()
        )
        
        # 결과 요약 로직 추가
        # ...
        
        # 버튼 비활성화
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)


class TierInputModal(discord.ui.Modal):
    def __init__(self, vote_type, member_name):
        super().__init__(title=f"티어 {vote_type} - {member_name}")
        self.vote_type = vote_type
        self.member_name = member_name
        self.vote_view = None
    
    tier_input = discord.ui.TextInput(
        label="목표 티어를 입력하세요",
        placeholder="예: 골드, 플래티넘, 다이아몬드 등",
        required=True,
        max_length=50
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        target_tier = self.tier_input.value.strip()
        
        # 기존 투표 제거
        self.vote_view.remove_existing_vote(user_id)
        
        # 새 투표 추가
        self.vote_view.votes[self.vote_type][user_id] = target_tier
        
        await interaction.response.send_message(
            f"**{self.member_name}님**의 티어를 **{target_tier}**로 **{self.vote_type}**에 투표했습니다.", 
            ephemeral=True
        )
        
        await self.vote_view.update_vote_display(interaction)