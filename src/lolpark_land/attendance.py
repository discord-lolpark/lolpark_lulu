import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import sqlite3
import asyncio
from functions import get_nickname

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

class AttendanceSystem:
    def __init__(self):
        self.db_path = "/database/lolpark_land.db"
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
    
    async def process_attendance(self, user_id):
        """출석체크 전체 프로세스 처리 (트랜잭션으로 묶음)"""
        async with self._lock:  # 동시성 제어
            try:
                # 사용자 존재 확인
                if not self.user_exists(user_id):
                    return False, "사용자 정보를 찾을 수 없습니다."
                
                # 오늘 이미 출석했는지 확인
                if self.has_attended_today(user_id):
                    return False, "오늘은 이미 출석체크를 완료하셨습니다!"
                
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
                            SET lolpark_coin = lolpark_coin + 1000 
                            WHERE user_id = ?
                        ''', (str(user_id),))
                        
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
                        
                        return True, f"출석체크 완료! 1000 LC가 지급되었습니다.\n현재 보유 LC: {current_lc:,}"
                        
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
        
        # 응답 지연 방지
        await interaction.response.defer()
        
        try:
            success, message = await attendance_system.process_attendance(user_id)
            
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

async def setup_attendance(bot):
    """봇에 출석체크 Cog를 추가하는 함수"""
    await bot.add_cog(AttendanceCog(bot))