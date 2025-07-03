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
        nickname = get_nickname(participant)
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
            
            # 문제 Embed와 이미지를 먼저 전송 (한 번만, 깜빡임 방지)
            quiz_embed = discord.Embed(
                title=f"🎮 스킨 배틀 - {question_num}/10",
                description=f"# 챔피언 힌트 : {champion_name_kr}",
                color=0x00ff00
            )
            
            # 이미지 메시지 전송
            try:
                file = File(image_path, filename="skin.jpg")
                quiz_embed.set_image(url="attachment://skin.jpg")
                image_message = await ctx.send(embed=quiz_embed, file=file)
            except:
                image_message = await ctx.send(embed=quiz_embed)
            
            # 정답 작성 버튼 뷰
            class AnswerView(discord.ui.View):
                def __init__(self, participants: list[discord.Member], correct_answer: str):
                    super().__init__(timeout=None)  # View 자체 timeout 완전히 비활성화
                    self.participants = participants
                    self.correct_answer = correct_answer
                    self.submitted_answers = {}  # {user: answer}
                    self.quiz_active = True
                    self.processed = False  # 중복 처리 방지
                    self.processing_lock = asyncio.Lock()  # 중복 처리 방지용 락
                    
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
                            
                            # 모든 참여자가 답안을 제출했는지 확인
                            if len(self.view_ref.submitted_answers) == len(self.view_ref.participants):
                                # 모든 참여자가 제출 완료 -> 즉시 정답 처리
                                await self.view_ref.process_answers()
                    
                    modal = AnswerModal(self)
                    await interaction.response.send_modal(modal)
                
                async def process_answers(self):
                    """정답 처리 함수 - 락으로 중복 실행 방지"""
                    async with self.processing_lock:  # 락으로 중복 처리 방지
                        if self.processed:
                            return
                        self.processed = True
                        self.quiz_active = False
                        
                        # 챔피언 힌트 이미지 메시지 삭제
                        try:
                            await image_message.delete()
                        except:
                            pass  # 이미 삭제되었거나 권한이 없는 경우
                        
                        # 정답 확인 및 점수 업데이트
                        correct_users = []
                        for user, answer in self.submitted_answers.items():
                            if answer == self.correct_answer:
                                correct_users.append(user)
                                scores[user] += 1
                        
                        # 각 플레이어의 답안 상태 생성
                        answer_status_lines = []
                        for participant in self.participants:
                            nickname = get_nickname(participant)
                            
                            if participant in self.submitted_answers:
                                user_answer = self.submitted_answers[participant]
                                if user_answer == self.correct_answer:
                                    # 정답인 경우
                                    answer_status_lines.append(f"⭕ **{nickname}**: `{user_answer}` ✨")
                                else:
                                    # 오답인 경우
                                    answer_status_lines.append(f"❌ **{nickname}**: `{user_answer}`")
                            else:
                                # 답안 제출 안한 경우
                                answer_status_lines.append(f"⏰ **{nickname}**: `미제출`")
                        
                        answer_status_text = "\n".join(answer_status_lines)
                        
                        # 업데이트된 스코어 텍스트
                        updated_score_text = "\n".join([f"• {get_nickname(participant)}: {score}점" 
                                                       for participant, score in scores.items()])
                        
                        # 정답 공개를 정보 메시지에 표시 (이미지 포함)
                        if question_num < 10:
                            # 마지막 문제가 아닌 경우
                            result_embed = discord.Embed(
                                title="🎉 정답 공개!",
                                description=f"**정답:** {self.correct_answer}\n\n**플레이어별 답안:**\n{answer_status_text}\n\n**현재 스코어:**\n{updated_score_text}\n\n⏰ **10초 후 다음 문제로 넘어갑니다.**",
                                color=0xff9900
                            )
                        else:
                            # 마지막 문제인 경우
                            result_embed = discord.Embed(
                                title="🎉 정답 공개!",
                                description=f"**정답:** {self.correct_answer}\n\n**플레이어별 답안:**\n{answer_status_text}\n\n**현재 스코어:**\n{updated_score_text}\n\n⏰ **10초 후 최종 결과를 공개합니다.**",
                                color=0xff9900
                            )
                        
                        try:
                            # 정답 이미지를 새로 첨부
                            file = File(image_path, filename="answer_skin.jpg")
                            result_embed.set_image(url="attachment://answer_skin.jpg")
                            await self.message.edit(embed=result_embed, view=None, attachments=[file])
                        except Exception as e:
                            # 이미지 첨부 실패 시 텍스트만 표시
                            await self.message.edit(embed=result_embed, view=None)
                            print(f"정답 이미지 첨부 중 오류: {e}")
            
            # 현재 스코어 정보 메시지 전송 (업데이트용)
            score_text = "\n".join([f"• {get_nickname(participant)}: {score}점" 
                                   for participant, score in scores.items()])
            
            info_embed = discord.Embed(
                title="📊 현재 상황",
                description=f"**현재 스코어:**\n{score_text}",
                color=0x0099ff
            )
            info_embed.set_footer(text="⏰ 15초 남았습니다...")
            
            # 버튼이 있는 정보 메시지 전송
            view = AnswerView(ready_participants, skin_name_kr)
            info_message = await ctx.send(embed=info_embed, view=view)
            view.message = info_message
            
            # 타이머 실행 (15초 동안 1초마다 업데이트)
            for remaining in range(15, 0, -1):
                # 이미 처리가 완료되었다면 타이머 중단
                if view.processed:
                    break
                    
                # 스코어 업데이트
                current_score_text = "\n".join([f"• {get_nickname(participant)}: {score}점" 
                                               for participant, score in scores.items()])
                
                updated_info_embed = discord.Embed(
                    title="📊 현재 상황",
                    description=f"**현재 스코어:**\n{current_score_text}",
                    color=0x0099ff
                )
                updated_info_embed.set_footer(text=f"⏰ {remaining}초 남았습니다...")
                
                try:
                    await info_message.edit(embed=updated_info_embed, view=view)
                except:
                    pass  # 메시지가 이미 수정되었거나 삭제된 경우
                
                await asyncio.sleep(1)
            
            # 15초 후 정답 처리 (아직 처리되지 않았다면)
            if not view.processed:
                await view.process_answers()
            
            # 결과 확인 시간 (10초)
            await asyncio.sleep(10)
            
            # 정답 공개 메시지 삭제 (마지막 문제가 아닌 경우만)
            if question_num < 10:
                try:
                    await info_message.delete()
                except:
                    pass  # 이미 삭제되었거나 권한이 없는 경우 무시
        
        # 최종 결과 발표
        final_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        final_text = ""
        for i, (participant, score) in enumerate(final_scores, 1):
            nickname = get_nickname(participant)
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
            self.game_started = False  # 게임 시작 상태 추가
            
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
            ready_nickname = get_nickname(interaction.user)
            
            # 모든 참여자가 준비 완료했는지 확인
            if len(self.ready_users) == len(self.participants):
                # 모든 참여자 준비 완료
                self.game_started = True  # 게임 시작 상태 설정
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
                        not_ready_nickname = get_nickname(participant)
                        not_ready.append(not_ready_nickname)
                
                not_ready_text = ", ".join(not_ready)
                await interaction.response.send_message(
                    f"{ready_nickname}님이 준비 완료! 대기 중: {not_ready_text}",
                    ephemeral=False
                )
        
        async def on_timeout(self):
            # 이미 게임이 시작된 경우 타임아웃 처리하지 않음
            if self.game_started:
                return
                
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
            self.game_started = True  # 게임 시작 상태 설정
            ready_names = []
            for user in self.ready_users:
                nickname = get_nickname(user)
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