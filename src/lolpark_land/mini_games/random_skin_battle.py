##########################################
#####       랜덤 스킨 배틀 !          ######
##########################################

from lolpark_land import execute_select_query
from functions import get_nickname
import discord
import random
import asyncio
from discord import File

async def run_skin_battle(participants: list[discord.Member], ctx: discord.TextChannel):

    get_skin_query = """
    SELECT skin_id, champion_name_kr, champion_name_en, 
        skin_name_kr, skin_name_en, rarity, file_name
    FROM skins
    WHERE 1=1
    """

    skin_list = execute_select_query(get_skin_query)

    # 참여자들의 닉네임 가져오기
    participant_names = []
    for participant in participants:
        nickname = await get_nickname(participant)
        participant_names.append(nickname)
    
    # 참여자 목록 텍스트 생성
    participants_text = "\n".join([f"• {name}" for name in participant_names])
    
    # 임베드 메시지 생성
    embed = discord.Embed(
        title="🎮 랜덤 스킨 배틀을 시작합니다!",
        description=f"**참여자 목록:**\n{participants_text}",
        color=0x00ff00
    )
    embed.set_footer(text="모든 참여자가 '준비' 버튼을 눌러주세요! (3분 제한)")
    
    # 스킨 퀴즈 시작 함수
    async def start_skin_quiz(ready_participants: list[discord.Member]):
        # 랜덤으로 10개 스킨 선택
        current_game_skin_list = random.sample(skin_list, 10)
        
        # 점수 초기화
        scores = {participant: 0 for participant in ready_participants}
        
        for question_num, skin_data in enumerate(current_game_skin_list, 1):
            skin_id, champion_name_kr, champion_name_en, skin_name_kr, skin_name_en, rarity, file_name = skin_data
            
            # 이미지 파일 경로
            image_path = f"/lolpark_assets/splash/{champion_name_en}/{file_name}.jpg"
            
            # 현재 스코어 텍스트 생성
            score_text = "\n".join([f"• {await get_nickname(participant)}: {score}점" 
                                   for participant, score in scores.items()])
            
            # 문제 Embed 생성
            quiz_embed = discord.Embed(
                title=f"🎮 스킨 배틀 - {question_num}/10",
                description=f"**현재 스코어:**\n{score_text}",
                color=0x00ff00
            )
            
            # 이미지 첨부
            try:
                file = File(image_path, filename="skin.jpg")
                quiz_embed.set_image(url="attachment://skin.jpg")
            except:
                quiz_embed.add_field(name="❌ 오류", value="이미지를 불러올 수 없습니다.", inline=False)
            
            # 정답 작성 버튼 뷰
            class AnswerView(discord.ui.View):
                def __init__(self, participants: list[discord.Member], correct_answer: str):
                    super().__init__(timeout=15)  # 15초 제한
                    self.participants = participants
                    self.correct_answer = correct_answer
                    self.submitted_answers = {}  # {user: answer}
                    self.quiz_active = True
                    
                @discord.ui.button(label='정답 작성', style=discord.ButtonStyle.primary, emoji='✏️')
                async def answer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if not self.quiz_active:
                        await interaction.response.send_message("이미 종료된 문제입니다!", ephemeral=True)
                        return
                        
                    if interaction.user not in self.participants:
                        await interaction.response.send_message("참여자가 아닙니다!", ephemeral=True)
                        return
                    
                    if interaction.user in self.submitted_answers:
                        await interaction.response.send_message("이미 답을 제출했습니다!", ephemeral=True)
                        return
                    
                    # Modal 생성
                    class AnswerModal(discord.ui.Modal):
                        def __init__(self, view_ref):
                            super().__init__(title="정답을 입력하세요")
                            self.view_ref = view_ref
                            
                        answer_input = discord.ui.TextInput(
                            label="스킨 이름",
                            placeholder="정확한 스킨 이름을 입력하세요...",
                            required=True,
                            max_length=100
                        )
                        
                        async def on_submit(self, interaction: discord.Interaction):
                            if not self.view_ref.quiz_active:
                                await interaction.response.send_message("시간이 초과되었습니다!", ephemeral=True)
                                return
                                
                            self.view_ref.submitted_answers[interaction.user] = self.answer_input.value
                            await interaction.response.send_message("답안이 제출되었습니다!", ephemeral=True)
                    
                    modal = AnswerModal(self)
                    await interaction.response.send_modal(modal)
                
                async def on_timeout(self):
                    self.quiz_active = False
                    
                    # 정답 확인
                    correct_users = []
                    for user, answer in self.submitted_answers.items():
                        if answer == self.correct_answer:
                            correct_users.append(user)
                            scores[user] += 1
                    
                    # 정답자 텍스트 생성
                    if correct_users:
                        correct_names = [await get_nickname(user) for user in correct_users]
                        correct_text = ", ".join(correct_names)
                        result_text = f"**정답자:** {correct_text}"
                    else:
                        result_text = "**정답자:** 없음"
                    
                    # 업데이트된 스코어 텍스트
                    updated_score_text = "\n".join([f"• {await get_nickname(participant)}: {score}점" 
                                                   for participant, score in scores.items()])
                    
                    # 정답 공개 Embed
                    result_embed = discord.Embed(
                        title=f"🎮 스킨 배틀 - {question_num}/10 (정답 공개)",
                        description=f"**정답:** {champion_name_kr} 스킨 : {skin_name_kr}\n\n{result_text}\n\n**현재 스코어:**\n{updated_score_text}",
                        color=0xff9900
                    )
                    
                    try:
                        file = File(image_path, filename="skin.jpg")
                        result_embed.set_image(url="attachment://skin.jpg")
                        await self.message.edit(embed=result_embed, view=None, attachments=[file])
                    except:
                        await self.message.edit(embed=result_embed, view=None)
                    
                    # 5초 후 다음 문제로 (마지막 문제가 아닌 경우)
                    if question_num < 10:
                        await asyncio.sleep(3)
                        
                        next_embed = discord.Embed(
                            title="⏭️ 다음 문제 준비 중...",
                            description="5초 후 다음 문제로 넘어갑니다!",
                            color=0x0099ff
                        )
                        await self.message.edit(embed=next_embed, attachments=[])
                        await asyncio.sleep(2)
            
            # 메시지 전송
            view = AnswerView(ready_participants, skin_name_kr)
            try:
                message = await ctx.send(embed=quiz_embed, view=view, file=file)
            except:
                message = await ctx.send(embed=quiz_embed, view=view)
            
            view.message = message
            
            # 15초 대기 (타임아웃까지)
            await asyncio.sleep(15)
            
            # 마지막 문제가 아니면 2초 더 대기 (총 5초)
            if question_num < 10:
                await asyncio.sleep(2)
        
        # 최종 결과 발표
        final_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        final_text = ""
        for i, (participant, score) in enumerate(final_scores, 1):
            nickname = await get_nickname(participant)
            if i == 1:
                final_text += f"🥇 **{nickname}**: {score}점\n"
            elif i == 2:
                final_text += f"🥈 **{nickname}**: {score}점\n"
            elif i == 3:
                final_text += f"🥉 **{nickname}**: {score}점\n"
            else:
                final_text += f"{i}등 **{nickname}**: {score}점\n"
        
        final_embed = discord.Embed(
            title="🎉 스킨 배틀 결과 발표!",
            description=final_text,
            color=0xffd700
        )
        
        await ctx.send(embed=final_embed)
    
    # 준비 버튼 뷰 클래스
    class ReadyView(discord.ui.View):
        def __init__(self, participants: list[discord.Member]):
            super().__init__(timeout=180)  # 3분 타임아웃
            self.participants = participants
            self.ready_users = set()  # 준비 완료한 사용자들
            
        @discord.ui.button(label='준비', style=discord.ButtonStyle.green, emoji='✅')
        async def ready_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            # 참여자가 아닌 경우 무시
            if interaction.user not in self.participants:
                await interaction.response.send_message("참여자가 아닙니다!", ephemeral=True)
                return
            
            # 이미 준비한 사용자인 경우
            if interaction.user in self.ready_users:
                await interaction.response.send_message("이미 준비 완료했습니다!", ephemeral=True)
                return
            
            # 준비 완료 처리
            self.ready_users.add(interaction.user)
            ready_nickname = await get_nickname(interaction.user)
            
            # 모든 참여자가 준비 완료했는지 확인
            if len(self.ready_users) == len(self.participants):
                # 모든 참여자 준비 완료
                await interaction.response.edit_message(
                    content="🎉 모든 참여자가 준비 완료! 스킨 배틀을 시작합니다!",
                    embed=None,
                    view=None
                )
                # 스킨 퀴즈 시작
                await start_skin_quiz(list(self.ready_users))
            else:
                # 아직 준비 안 한 사람들 표시
                not_ready = []
                for participant in self.participants:
                    if participant not in self.ready_users:
                        not_ready_nickname = await get_nickname(participant)
                        not_ready.append(not_ready_nickname)
                
                not_ready_text = ", ".join(not_ready)
                await interaction.response.send_message(
                    f"{ready_nickname}님이 준비 완료! 대기 중: {not_ready_text}",
                    ephemeral=False
                )
        
        async def on_timeout(self):
            # 타임아웃 시 처리
            if len(self.ready_users) == 0:
                # 아무도 준비하지 않은 경우
                await self.message.edit(
                    content="⏰ 시간이 초과되었습니다! 아무도 준비하지 않아 스킨 배틀이 취소되었습니다.",
                    embed=None,
                    view=None
                )
                return
            
            # 준비한 사람들만으로 진행
            ready_names = []
            for user in self.ready_users:
                nickname = await get_nickname(user)
                ready_names.append(nickname)
            
            ready_text = ", ".join(ready_names)
            await self.message.edit(
                content=f"⏰ 시간이 초과되었습니다!\n준비 완료한 참여자들만으로 스킨 배틀을 시작합니다!\n\n**최종 참여자:** {ready_text}",
                embed=None,
                view=None
            )
            
            # 스킨 퀴즈 시작
            await start_skin_quiz(list(self.ready_users))
    
    # 메시지 전송
    view = ReadyView(participants)
    message = await ctx.send(embed=embed, view=view)
    view.message = message  # 타임아웃 시 메시지 수정을 위해 필요