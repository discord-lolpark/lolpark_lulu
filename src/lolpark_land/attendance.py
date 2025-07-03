import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta, time
import sqlite3
import asyncio
from functions import get_nickname, lol_champion_korean_dict
from lolpark_land.land_config import ATTENDANCE_CHANNEL_ID, land_database_path
import random
import os

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

class AttendanceSystem:
    def __init__(self):
        self.db_path = land_database_path
        self._lock = asyncio.Lock()  # 동시성 제어를 위한 락
        self.init_attendance_table()
    
    def init_attendance_table(self):
        """출석체크 테이블 초기화 (없으면 생성)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 출석체크 테이블 생성
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attendance (
                        user_id TEXT PRIMARY KEY,
                        last_attendance_date TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 인덱스 생성 (성능 향상)
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_attendance_date 
                    ON attendance(last_attendance_date)
                ''')
                
        except sqlite3.Error as e:
            print(f"출석체크 테이블 초기화 오류: {e}")
            raise
    
    def get_korean_date_string(self):
        """한국 시간 기준으로 오늘 날짜 반환 (YYYY-MM-DD 형식)"""
        korean_time = datetime.now(KST)
        return korean_time.strftime("%Y-%m-%d")
    
    def get_korean_date_formatted(self):
        """한국 시간 기준으로 오늘 날짜 반환 (MM월 DD일 형식)"""
        korean_time = datetime.now(KST)
        return korean_time.strftime("%m월 %d일")
    
    def get_last_attendance_date(self, user_id):
        """사용자의 마지막 출석체크 날짜 반환"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT last_attendance_date FROM attendance WHERE user_id = ?", 
                    (str(user_id),)
                )
                result = cursor.fetchone()
                return result[0] if result else None
                
        except sqlite3.Error as e:
            print(f"마지막 출석일 조회 오류: {e}")
            return None
    
    def has_attended_today(self, user_id):
        """오늘 이미 출석체크했는지 확인"""
        last_attendance = self.get_last_attendance_date(user_id)
        today = self.get_korean_date_string()
        return last_attendance == today
    
    def user_exists(self, user_id):
        """사용자가 users 테이블에 존재하는지 확인"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (str(user_id),))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"사용자 존재 확인 오류: {e}")
            return False
    
    def has_premium_role(self, member):
        """사용자가 LOLPARK PREMIUM 역할을 가지고 있는지 확인"""
        try:
            if member is None:
                return False
            
            for role in member.roles:
                if role.name == "LOLPARK PREMIUM":
                    return True
            return False
        except Exception as e:
            print(f"프리미엄 역할 확인 오류: {e}")
            return False
    
    async def process_attendance(self, user_id, member=None):
        """출석체크 전체 프로세스 처리 (트랜잭션으로 묶음)"""
        async with self._lock:  # 동시성 제어
            try:
                # 사용자 존재 확인
                if not self.user_exists(user_id):
                    return False, "아직 롤파크랜드에 가입되지 않았습니다.\n<#1385406629146525798>에서 /랜드등록을 통해 먼저 가입해주세요"
                
                # 오늘 이미 출석했는지 확인
                if self.has_attended_today(user_id):
                    return False, "오늘은 이미 출석체크를 완료하셨습니다!"
                
                # 프리미엄 역할 확인
                is_premium = self.has_premium_role(member)
                reward_amount = 5000 if is_premium else 1000
                
                today = self.get_korean_date_string()
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # 트랜잭션 시작
                    conn.execute("BEGIN TRANSACTION")
                    
                    try:
                        # 1. 출석 기록 업데이트
                        cursor.execute('''
                            INSERT OR REPLACE INTO attendance 
                            (user_id, last_attendance_date, updated_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        ''', (str(user_id), today))
                        
                        # 2. LC 보상 지급
                        cursor.execute('''
                            UPDATE users 
                            SET lolpark_coin = lolpark_coin + ? 
                            WHERE user_id = ?
                        ''', (reward_amount, str(user_id)))
                        
                        # 업데이트된 행이 있는지 확인
                        if cursor.rowcount == 0:
                            raise sqlite3.Error("사용자 정보 업데이트 실패")
                        
                        # 3. 현재 LC 조회
                        cursor.execute(
                            "SELECT lolpark_coin FROM users WHERE user_id = ?", 
                            (str(user_id),)
                        )
                        result = cursor.fetchone()
                        current_lc = result[0] if result else 0
                        
                        # 트랜잭션 커밋
                        conn.commit()
                        
                        # 메시지 생성
                        if is_premium:
                            message = f"출석체크 완료! {reward_amount:,} LC (롤파크 프리미엄 보너스 5배) 획득!\n현재 보유 LC: {current_lc:,}"
                        else:
                            message = f"출석체크 완료! {reward_amount:,} LC가 지급되었습니다.\n현재 보유 LC: {current_lc:,}"
                        
                        return True, message
                        
                    except sqlite3.Error as e:
                        # 트랜잭션 롤백
                        conn.rollback()
                        print(f"출석체크 트랜잭션 오류: {e}")
                        return False, "출석체크 처리 중 오류가 발생했습니다."
                        
            except sqlite3.Error as e:
                print(f"출석체크 처리 오류: {e}")
                return False, "데이터베이스 오류가 발생했습니다."
            except Exception as e:
                print(f"예상치 못한 오류: {e}")
                return False, "시스템 오류가 발생했습니다."

# AttendanceSystem 인스턴스 생성
attendance_system = AttendanceSystem()

class AttendanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @discord.app_commands.command(name="출석", description="하루 한 번 출석체크를 할 수 있습니다.")
    async def attendance_check(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_name = get_nickname(interaction.user)
        member = interaction.user if hasattr(interaction.user, 'roles') else None
        
        # 응답 지연 방지
        await interaction.response.defer()
        
        try:
            success, message = await attendance_system.process_attendance(user_id, member)
            
            if success:
                embed = discord.Embed(
                    title="✅ 출석체크 완료",
                    description=f"{user_name}님, {message}",
                    color=0x00ff00
                )
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ 출석체크 실패",
                    description=f"{user_name}님, {message}",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            print(f"출석체크 명령어 처리 중 오류: {e}")
            await interaction.followup.send(
                "출석체크 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                ephemeral=True
            )
    

    @tasks.loop(time=time(hour=15, minute=0))
    async def daily_attendance_notification(self):
        """매일 오전 0시에 출석체크 알림 메시지 전송"""

        if ATTENDANCE_CHANNEL_ID is None:
            print("출석체크 채널이 설정되지 않았습니다.")
            return
        
        try:
            channel = self.bot.get_channel(ATTENDANCE_CHANNEL_ID)
            if channel is None:
                print(f"채널을 찾을 수 없습니다. ID: {ATTENDANCE_CHANNEL_ID}")
                return
            
            # 오늘 날짜 가져오기
            today_date = attendance_system.get_korean_date_formatted()
            
            # LOLPARKLAND 역할 찾기
            lolparkland_role = None
            for guild in self.bot.guilds:
                for role in guild.roles:
                    if role.name == "LOLPARKLAND":
                        lolparkland_role = role
                        break
                if lolparkland_role:
                    break
            
            # 임베드 메시지 생성
            embed = discord.Embed(
                title="🌅 새로운 하루가 시작되었습니다!",
                description=f"**{today_date}**입니다!\n\n출석체크를 하여 **무료 LOLPARK COIN**을 지급받으세요!",
                color=0xffd700  # 금색
            )
            
            embed.add_field(
                name="💰 보상",
                value="일반 유저: **1,000 LC**\n프리미엄 유저: **5,000 LC** (5배 보너스!)",
                inline=False
            )
            
            embed.add_field(
                name="📝 출석체크 방법",
                value="현재 채널에서 `/출석` 명령어를 입력하세요!",
                inline=False
            )
            
            embed.set_footer(text="매일 오전 0시에 갱신됩니다 • LOLPARK LAND")

            try:
                random_champion = random.choice(list(lol_champion_korean_dict.keys()))
                file_path = f"/lolpark_assets/splash/{random_champion}/{random_champion}_0.jpg"
                
                # 파일 존재 확인
                if os.path.exists(file_path):
                    file = discord.File(file_path, filename="champion.jpg")
                    embed.set_thumbnail(url="attachment://champion.jpg")
                else:
                    print(f"파일이 존재하지 않음: {file_path}")
                    file = None
                    # 대신 고양이 썸네일 사용
                    embed.set_thumbnail(url="https://cdn2.thecatapi.com/images/0XYvRd7oD.jpg")
                
                # 역할 멘션과 함께 메시지 전송
                mention_text = lolparkland_role.mention if lolparkland_role else "@LOLPARKLAND"
                
                if file:
                    await channel.send(file=file, content=mention_text, embed=embed)
                else:
                    await channel.send(content=mention_text, embed=embed)
                    
            except Exception as e:
                print(f"썸네일 설정 오류: {e}")
                # 오류 시 기본 썸네일로 대체
                embed.set_thumbnail(url="https://cdn2.thecatapi.com/images/0XYvRd7oD.jpg")
                mention_text = lolparkland_role.mention if lolparkland_role else "@LOLPARKLAND"
                await channel.send(content=mention_text, embed=embed)
            
        except Exception as e:
            print(f"출석체크 알림 전송 오류: {e}")
    
    @daily_attendance_notification.before_loop
    async def before_daily_notification(self):
        """봇이 준비될 때까지 대기"""
        await self.bot.wait_until_ready()
    
    async def cog_load(self):
        """Cog가 로드될 때 작업 시작"""
        self.daily_attendance_notification.start()
        print("출석체크 알림 시스템이 시작되었습니다.")
    
    async def cog_unload(self):
        """Cog가 언로드될 때 작업 중지"""
        self.daily_attendance_notification.cancel()
        print("출석체크 알림 시스템이 중지되었습니다.")

async def setup_attendance(bot):
    """봇에 출석체크 Cog를 추가하는 함수"""
    await bot.add_cog(AttendanceCog(bot))