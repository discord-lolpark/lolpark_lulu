import discord
import asyncio
from typing import Optional


class TierAdjustVoteView(discord.ui.View):
    def __init__(self, member_name, target_channel):
        super().__init__(timeout=86400)  # 24시간
        self.member_name = member_name
        self.target_channel = target_channel
        self.votes = {"상승": {}, "유지": set(), "하락": {}}  # 유지는 set으로 변경
        self.vote_message_id: Optional[int] = None  # 메시지 ID 저장
        self._update_lock = asyncio.Lock()  # 동시성 제어
    
    @discord.ui.button(label="티어 상승", style=discord.ButtonStyle.success, emoji="⬆️")
    async def vote_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 자문단만 투표 가능
        advisor_role = discord.utils.get(interaction.guild.roles, name="티어 조정 자문단")
        if advisor_role not in interaction.user.roles:
            await interaction.response.send_message("자문단만 투표할 수 있습니다.", ephemeral=True)
            return
        modal = TierInputModal("상승", self.member_name)
        modal.vote_view = self
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="티어 유지", style=discord.ButtonStyle.secondary, emoji="➡️")
    async def vote_maintain(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id

        # 자문단만 투표 가능
        advisor_role = discord.utils.get(interaction.guild.roles, name="티어 조정 자문단")
        if advisor_role not in interaction.user.roles:
            await interaction.response.send_message("자문단만 투표할 수 있습니다.", ephemeral=True)
            return
        
        # 기존 투표 제거
        self.remove_existing_vote(user_id)
        
        # 유지 투표 추가
        self.votes["유지"].add(user_id)
        
        # view만 업데이트 (개별 메시지 없음)
        await self.update_vote_display(interaction)
    
    @discord.ui.button(label="티어 하락", style=discord.ButtonStyle.danger, emoji="⬇️")
    async def vote_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 자문단만 투표 가능
        advisor_role = discord.utils.get(interaction.guild.roles, name="티어 조정 자문단")
        if advisor_role not in interaction.user.roles:
            await interaction.response.send_message("자문단만 투표할 수 있습니다.", ephemeral=True)
            return
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
        self.votes["상승"].pop(user_id, None)
        self.votes["유지"].discard(user_id)  # set에서는 discard 사용
        self.votes["하락"].pop(user_id, None)
    
    def _truncate_field_value(self, value: str, max_length: int = 1024) -> str:
        if len(value) <= max_length:
            return value
        
        lines = value.split('\n')
        result = ""
        
        for i, line in enumerate(lines):
            test_result = result + line + '\n'
            if len(test_result) > max_length - 50:
                remaining = len(lines) - i
                result += f"\n... 그리고 {remaining}명 더"
                break
            result = test_result
        
        return result.rstrip()
    
    async def update_vote_display(self, interaction):
        async with self._update_lock:  # 동시성 제어
            embed = self._create_vote_embed()
            
            try:
                await interaction.response.edit_message(embed=embed, view=self)
            except discord.InteractionResponded:
                try:
                    await interaction.edit_original_response(embed=embed, view=self)
                except discord.HTTPException as e:
                    print(f"메시지 업데이트 실패: {e}")
            except discord.HTTPException as e:
                print(f"Discord API 오류: {e}")

    async def update_vote_display_silent(self):
        """모달에서 호출할 때 사용하는 메서드 (interaction 없이)"""
        async with self._update_lock:  # 동시성 제어
            embed = self._create_vote_embed()
            
            try:
                if self.vote_message_id:
                    # 저장된 메시지 ID로 직접 접근
                    message = await self.target_channel.fetch_message(self.vote_message_id)
                    await message.edit(embed=embed, view=self)
                else:
                    # 메시지 ID가 없는 경우 검색 (fallback)
                    await self._find_and_update_message(embed)
            except discord.NotFound:
                print("투표 메시지를 찾을 수 없습니다.")
            except discord.HTTPException as e:
                print(f"메시지 업데이트 실패: {e}")
    
    async def _find_and_update_message(self, embed):
        """메시지를 찾아서 업데이트하는 fallback 메서드"""
        try:
            async for message in self.target_channel.history(limit=50):
                if (message.author.bot and message.embeds and 
                    message.embeds[0].title == "🗳️ 티어 조정 투표 현황" and
                    self.member_name in message.embeds[0].description):
                    self.vote_message_id = message.id  # ID 저장
                    await message.edit(embed=embed, view=self)
                    break
        except discord.HTTPException as e:
            print(f"메시지 검색/업데이트 실패: {e}")
    
    def _create_vote_embed(self) -> discord.Embed:
        """투표 현황 embed 생성"""
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
            up_text = self._truncate_field_value(up_text)
            embed.add_field(name=f"⬆️ 상승 ({len(self.votes['상승'])}표)", value=up_text, inline=False)
        
        # 유지 투표 표시
        if self.votes["유지"]:
            maintain_text = "\n".join([f"• <@{user_id}>" for user_id in self.votes["유지"]])
            maintain_text = self._truncate_field_value(maintain_text)
            embed.add_field(name=f"➡️ 유지 ({len(self.votes['유지'])}표)", value=maintain_text, inline=False)
        
        # 하락 투표 표시
        if self.votes["하락"]:
            down_text = "\n".join([f"• <@{user_id}>: {tier}" for user_id, tier in self.votes["하락"].items()])
            down_text = self._truncate_field_value(down_text)
            embed.add_field(name=f"⬇️ 하락 ({len(self.votes['하락'])}표)", value=down_text, inline=False)
        
        return embed
    
    async def finalize_vote(self, interaction):
        # 투표 결과 집계
        up_count = len(self.votes["상승"])
        maintain_count = len(self.votes["유지"])
        down_count = len(self.votes["하락"])
        total_votes = up_count + maintain_count + down_count
        
        if total_votes == 0:
            embed = discord.Embed(
                title="🏁 티어 조정 투표 완료",
                description=f"**{self.member_name}님**의 티어 조정 투표가 완료되었습니다.\n\n❌ **투표 없음**",
                color=discord.Color.red()
            )
        else:
            embed = self._create_final_result_embed(up_count, maintain_count, down_count, total_votes)
        
        # 타임스탬프 추가
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text="투표 완료 시각")
        
        # 버튼 비활성화
        for item in self.children:
            item.disabled = True
        
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.InteractionResponded:
            await interaction.edit_original_response(embed=embed, view=self)
    
    def _create_final_result_embed(self, up_count, maintain_count, down_count, total_votes):
        """최종 결과 embed 생성"""
        # 최다 득표 결정
        vote_counts = {
            "상승": up_count,
            "유지": maintain_count,
            "하락": down_count
        }
        
        max_votes = max(vote_counts.values())
        winners = [vote_type for vote_type, count in vote_counts.items() if count == max_votes]
        
        # 결과 결정
        if len(winners) > 1:
            result = "동점"
            result_color = discord.Color.orange()
            result_emoji = "🤝"
        else:
            winner = winners[0]
            result_color = {
                "상승": discord.Color.green(),
                "유지": discord.Color.blue(),
                "하락": discord.Color.red()
            }[winner]
            result_emoji = {
                "상승": "⬆️",
                "유지": "➡️", 
                "하락": "⬇️"
            }[winner]
            
            if winner == "유지":
                result = "티어 유지"
            else:
                # 상승/하락의 경우 가장 많이 언급된 티어 찾기
                tier_votes = self.votes[winner]
                if tier_votes:
                    # 티어별 득표수 계산
                    tier_count = {}
                    for tier in tier_votes.values():
                        tier_count[tier] = tier_count.get(tier, 0) + 1
                    
                    # 최다 득표 티어
                    most_voted_tier = max(tier_count.items(), key=lambda x: x[1])
                    result = f"{most_voted_tier[0]}로 {winner}"
                else:
                    result = f"티어 {winner}"
        
        embed = discord.Embed(
            title="🏁 티어 조정 투표 완료",
            description=f"**{self.member_name}님**의 티어 조정 투표가 완료되었습니다.\n\n"
                    f"{result_emoji} **최종 결과: {result}**",
            color=result_color
        )
        
        # 투표 현황 표시
        embed.add_field(
            name="📊 투표 현황",
            value=f"총 {total_votes}표\n"
                f"⬆️ 상승: {up_count}표\n"
                f"➡️ 유지: {maintain_count}표\n"
                f"⬇️ 하락: {down_count}표",
            inline=True
        )
        
        # 각 투표 타입별 상세 정보 추가
        self._add_vote_details_to_embed(embed, up_count, maintain_count, down_count)
        
        # 동점인 경우 안내
        if len(winners) > 1:
            tied_votes = [f"{vote_type}({vote_counts[vote_type]}표)" for vote_type in winners]
            embed.add_field(
                name="⚠️ 동점 안내",
                value=f"다음 항목들이 동점입니다: {', '.join(tied_votes)}\n추가 논의가 필요합니다.",
                inline=False
            )
        
        return embed
    
    def _add_vote_details_to_embed(self, embed, up_count, maintain_count, down_count):
        """투표 상세 정보를 embed에 추가"""
        # 상승 투표 상세
        if self.votes["상승"]:
            up_details = []
            tier_count = {}
            for user_id, tier in self.votes["상승"].items():
                up_details.append(f"• <@{user_id}>: {tier}")
                tier_count[tier] = tier_count.get(tier, 0) + 1
            
            tier_summary = ", ".join([f"{tier}({count}표)" for tier, count in tier_count.items()])
            detail_text = f"**티어별 득표:** {tier_summary}\n" + "\n".join(up_details)
            detail_text = self._truncate_field_value(detail_text)
            
            embed.add_field(
                name=f"⬆️ 상승 투표 ({up_count}표)",
                value=detail_text,
                inline=False
            )
        
        # 유지 투표 상세
        if self.votes["유지"]:
            maintain_details = "\n".join([f"• <@{user_id}>" for user_id in self.votes["유지"]])
            maintain_details = self._truncate_field_value(maintain_details)
            embed.add_field(
                name=f"➡️ 유지 투표 ({maintain_count}표)",
                value=maintain_details,
                inline=False
            )
        
        # 하락 투표 상세
        if self.votes["하락"]:
            down_details = []
            tier_count = {}
            for user_id, tier in self.votes["하락"].items():
                down_details.append(f"• <@{user_id}>: {tier}")
                tier_count[tier] = tier_count.get(tier, 0) + 1
            
            tier_summary = ", ".join([f"{tier}({count}표)" for tier, count in tier_count.items()])
            detail_text = f"**티어별 득표:** {tier_summary}\n" + "\n".join(down_details)
            detail_text = self._truncate_field_value(detail_text)
            
            embed.add_field(
                name=f"⬇️ 하락 투표 ({down_count}표)",
                value=detail_text,
                inline=False
            )


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
        
        if not target_tier:
            await interaction.response.send_message("티어를 입력해주세요.", ephemeral=True)
            return
        
        # 기존 투표 제거
        self.vote_view.remove_existing_vote(user_id)
        
        # 새 투표 추가
        self.vote_view.votes[self.vote_type][user_id] = target_tier
        
        # 모달 응답 (간단한 확인만)
        await interaction.response.send_message("투표 완료!", ephemeral=True)
        
        # view 업데이트 (별도 메서드 사용)
        await self.vote_view.update_vote_display_silent()