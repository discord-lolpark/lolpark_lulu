import discord
from discord.ext import commands
from lolpark_land.mini_games import run_skin_battle

# 미니게임 정보 딕셔너리
MINIGAMES = {
    "random_skin_battle": {
        "name": "랜덤 스킨 배틀",
        "description": "시간 안에 스킨 이름을 맞히세요. 더 많이 맞힌 사람이 승자가 됩니다.",
        "emoji": "🆚",
        "min_players": 3
    },
}

class RecruitmentView(discord.ui.View):
    def __init__(self, selected_game, num_of_participants, initial_participants):
        super().__init__(timeout=300)  # 5분 타임아웃
        self.selected_game = selected_game
        self.num_of_participants = num_of_participants
        self.participants = initial_participants.copy()
        
        # 참가/취소 버튼 추가
        self.join_button = discord.ui.Button(
            label="참가하기",
            emoji="✅",
            style=discord.ButtonStyle.success,
            custom_id=f"join_{selected_game}"
        )
        self.join_button.callback = self.join_game
        self.add_item(self.join_button)
        
        # 강제 시작 버튼 (방장만 사용 가능)
        self.force_start_button = discord.ui.Button(
            label="더 모집하지 않고 시작",
            emoji="🚀",
            style=discord.ButtonStyle.secondary,
            custom_id=f"force_start_{selected_game}"
        )
        self.force_start_button.callback = self.force_start_game
        self.add_item(self.force_start_button)
    
    async def join_game(self, interaction):
        user_id = interaction.user.id
        
        if user_id in self.participants:
            # 이미 참가중인 경우 - 취소
            self.participants.remove(user_id)
            action = "취소"
        else:
            # 참가중이 아닌 경우 - 참가
            if len(self.participants) >= self.num_of_participants:
                await interaction.response.send_message("이미 모집이 완료되었습니다!", ephemeral=True)
                return
            
            self.participants.append(user_id)
            action = "참가"
        
        # 임베드 업데이트
        embed = await self.create_recruitment_embed(interaction.guild)
        
        # 모집 완료 확인
        if len(self.participants) == self.num_of_participants:
            await self.start_game(interaction, embed)
        else:
            await interaction.response.edit_message(embed=embed, view=self)
            
            # 참가/취소 알림
            if action == "참가":
                await interaction.followup.send(f"{interaction.user.mention}님이 게임에 참가했습니다!", ephemeral=True)
            else:
                await interaction.followup.send(f"{interaction.user.mention}님이 게임 참가를 취소했습니다!", ephemeral=True)
    
    async def force_start_game(self, interaction):
        # 방장(첫 번째 참가자)만 강제 시작 가능
        if interaction.user.id != self.participants[0]:
            await interaction.response.send_message("방장만 강제 시작할 수 있습니다!", ephemeral=True)
            return
        
        # 게임별 최소 인원 확인
        game_info = MINIGAMES[self.selected_game]
        min_players = game_info.get("min_players", 1)
        
        if len(self.participants) < min_players:
            await interaction.response.send_message(f"최소 {min_players}명은 있어야 게임을 시작할 수 있습니다!", ephemeral=True)
            return
        
        embed = await self.create_recruitment_embed(interaction.guild)
        await self.start_game(interaction, embed)
    
    async def start_game(self, interaction, embed):
        """게임 시작 함수"""
        game_info = MINIGAMES[self.selected_game]
        
        # 게임 시작 임베드 생성
        start_embed = discord.Embed(
            title=f"🎮 {game_info['name']} 게임 시작!",
            description=f"{game_info['description']}\n\n게임이 곧 시작됩니다...",
            color=discord.Color.gold()
        )
        
        # 참가자 목록 추가
        participant_list = []
        for i, user_id in enumerate(self.participants, 1):
            user = interaction.guild.get_member(user_id)
            participant_list.append(f"{i}. {user.mention if user else f'<@{user_id}>'}")
        
        start_embed.add_field(
            name=f"참가자 ({len(self.participants)}명)",
            value="\n".join(participant_list),
            inline=False
        )
        
        start_embed.set_footer(text="게임이 시작됩니다!")
        
        # 모든 버튼 비활성화
        for item in self.children:
            item.disabled = True
        
        # 게임 시작 메시지를 임시로 표시
        await interaction.response.edit_message(embed=start_embed, view=self)
        
        # 실제 게임 로직 실행
        print(f"게임 시작: {self.selected_game}, 참가자: {len(self.participants)}명")
        
        # 예시: 게임별 로직 실행
        if self.selected_game == "random_skin_battle":
            await self.start_random_skin_battle(interaction)
        
        # 게임 시작 후 모집 메시지 삭제
        try:
            await interaction.delete_original_response()
            print("모집 메시지 삭제 완료")
        except Exception as e:
            print(f"모집 메시지 삭제 중 오류: {e}")
    
    async def start_random_skin_battle(self, interaction):
        """랜덤 스킨 배틀 게임 로직"""
        try:
            # 현재 채널의 카테고리 가져오기
            current_channel = interaction.channel
            category = current_channel.category
            
            # 참가자들을 Member 객체로 변환
            participants = []
            for user_id in self.participants:
                member = interaction.guild.get_member(user_id)
                if member:
                    participants.append(member)
            
            # 새 텍스트 채널 생성 (현재 채널과 동일한 권한)
            overwrites = current_channel.overwrites
            game_channel = await interaction.guild.create_text_channel(
                name="스킨-미니게임-채널",
                category=category,
                overwrites=overwrites
            )
            
            # 참가자들 멘션
            participant_mentions = [member.mention for member in participants]
            mention_message = "🎮 **스킨 배틀 게임이 시작됩니다!**\n\n참가자: " + ", ".join(participant_mentions)
            
            await game_channel.send(mention_message)
            
            # 게임 시작 알림을 원래 채널에도 보내기
            await interaction.followup.send(
                f"🆚 랜덤 스킨 배틀이 {game_channel.mention} 채널에서 시작되었습니다!", 
                ephemeral=False
            )
            
            # 실제 게임 실행
            await run_skin_battle(participants, game_channel)
            
        except Exception as e:
            await interaction.followup.send(f"게임 시작 중 오류가 발생했습니다: {str(e)}", ephemeral=True)
            print(f"랜덤 스킨 배틀 시작 오류: {e}")
    
    async def create_recruitment_embed(self, guild):
        """모집 임베드 생성"""
        game_info = MINIGAMES[self.selected_game]
        
        embed = discord.Embed(
            title=f"🎮 {game_info['name']} 모집 중!",
            description=f"{game_info['description']}\n\n**필요 인원:** {self.num_of_participants}명\n**현재 참가자:** {len(self.participants)}명",
            color=discord.Color.green() if len(self.participants) < self.num_of_participants else discord.Color.gold()
        )
        
        # 참가자 목록 생성
        if self.participants:
            participant_list = []
            for i, user_id in enumerate(self.participants, 1):
                user = guild.get_member(user_id)
                participant_list.append(f"{i}. {user.mention if user else f'<@{user_id}>'}")
            
            embed.add_field(
                name="참가자 목록",
                value="\n".join(participant_list),
                inline=False
            )
        
        # 상태 표시
        remaining = self.num_of_participants - len(self.participants)
        if remaining > 0:
            embed.add_field(
                name="상태",
                value=f"모집 중... ({remaining}명 더 필요)",
                inline=False
            )
        else:
            embed.add_field(
                name="상태",
                value="모집 완료! 게임이 시작됩니다.",
                inline=False
            )
        
        embed.set_footer(text="'참가하기' 버튼을 눌러 게임에 참가하거나 취소하세요!")
        
        return embed
    
    async def on_timeout(self):
        # 타임아웃 시 모든 버튼 비활성화
        for item in self.children:
            item.disabled = True

class ParticipantSelect(discord.ui.Select):
    def __init__(self, selected_game):
        self.selected_game = selected_game
        game_info = MINIGAMES[selected_game]
        
        # 게임별 최소 인원 설정 (기본값: 1명)
        min_players = game_info.get("min_players", 1)
        
        # 최소 인원부터 10명까지 선택 옵션 생성
        options = []
        for i in range(min_players, 11):
            options.append(discord.SelectOption(
                label=f"{i}명",
                value=str(i),
                description=f"{i}명이서 게임을 진행합니다"
            ))
        
        super().__init__(
            placeholder=f"참여할 인원을 선택하세요 ({min_players}~10명)",
            options=options,
            custom_id=f"participant_select_{selected_game}"
        )
    
    async def callback(self, interaction):
        num_of_participants = int(self.values[0])
        
        # 모집 함수 실행
        await start_recruitment(interaction, self.selected_game, num_of_participants)

class ParticipantSelectView(discord.ui.View):
    def __init__(self, selected_game):
        super().__init__(timeout=300)
        self.add_item(ParticipantSelect(selected_game))
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class MinigameView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=1800)  # 30분 타임아웃
        
        # 각 미니게임에 대한 버튼 생성
        for game_id, game_info in MINIGAMES.items():
            button = discord.ui.Button(
                label=game_info["name"],
                emoji=game_info["emoji"],
                custom_id=f"minigame_{game_id}",
                style=discord.ButtonStyle.primary
            )
            button.callback = self.create_game_callback(game_id)
            self.add_item(button)
    
    def create_game_callback(self, game_id):
        async def game_callback(interaction):
            game_info = MINIGAMES[game_id]
            
            # 인원 선택 임베드 생성
            embed = discord.Embed(
                title=f"{game_info['emoji']} {game_info['name']}",
                description=f"{game_info['description']}\n\n참여할 인원을 선택해주세요!",
                color=discord.Color.orange()
            )
            
            # 인원 선택 뷰로 전환
            view = ParticipantSelectView(game_id)
            
            # 원래 메시지를 새로운 메시지로 교체
            await interaction.response.edit_message(
                embed=embed,
                view=view
            )
            
        return game_callback
    
    async def on_timeout(self):
        # 타임아웃 시 모든 버튼 비활성화
        for item in self.children:
            item.disabled = True

def create_minigame_manager(interaction):
    """미니게임 매니저 뷰와 임베드를 생성하는 함수"""
    
    # 임베드 생성
    embed = discord.Embed(
        title="🎮 미니게임 센터",
        description="원하는 미니게임을 선택해주세요!",
        color=discord.Color.blue()
    )
    
    # 각 미니게임 정보를 필드로 추가
    for game_id, game_info in MINIGAMES.items():
        embed.add_field(
            name=f"{game_info['emoji']} {game_info['name']}",
            value=game_info['description'],
            inline=False
        )
    
    embed.set_footer(text="버튼을 클릭하여 게임을 시작하세요!")
    
    # 뷰 생성
    view = MinigameView()
    
    return embed, view

async def start_recruitment(interaction, selected_game, num_of_participants):
    """모집 함수 - 지정된 인원으로 게임 참가자를 모집합니다"""
    
    game_info = MINIGAMES[selected_game]
    min_players = game_info.get("min_players", 1)
    
    # 최소 인원이 1명이고 선택한 인원이 1명인 경우 바로 게임 시작
    if min_players == 1 and num_of_participants == 1:
        await start_single_player_game(interaction, selected_game)
        return
    
    # 그 외의 경우 모집 시작
    initial_participants = [interaction.user.id]
    
    # 모집 뷰 생성
    recruitment_view = RecruitmentView(selected_game, num_of_participants, initial_participants)
    
    # 모집 임베드 생성
    embed = await recruitment_view.create_recruitment_embed(interaction.guild)
    
    await interaction.response.send_message(
        embed=embed,
        view=recruitment_view
    )
    
    print(f"모집 시작: {selected_game}, 인원: {num_of_participants}명")

async def start_single_player_game(interaction, selected_game):
    """1인 게임 즉시 시작"""
    game_info = MINIGAMES[selected_game]
    
    # 게임 시작 임베드 생성
    embed = discord.Embed(
        title=f"🎮 {game_info['name']} 게임 시작!",
        description=f"{game_info['description']}\n\n혼자서 게임을 시작합니다!",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="참가자 (1명)",
        value=f"1. {interaction.user.mention}",
        inline=False
    )
    
    embed.set_footer(text="게임이 시작되었습니다!")
    
    await interaction.response.send_message(embed=embed)
    
    # TODO: 여기서 실제 1인 게임 로직 실행
    print(f"1인 게임 시작: {selected_game}")
    
    # 예시: 게임별 1인 로직 실행 (랜덤 스킨 배틀은 1인 불가능)
    if selected_game == "random_skin_battle":
        await interaction.followup.send("❌ 랜덤 스킨 배틀은 1인 플레이가 불가능합니다!", ephemeral=True)
    else:
        await interaction.followup.send(f"🎮 {game_info['name']} 게임이 시작되었습니다!", ephemeral=False)