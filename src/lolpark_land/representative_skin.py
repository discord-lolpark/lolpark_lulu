import discord
import math
from lolpark_land.land_functions import execute_select_query, execute_post_query, get_skin_image_url

async def show_representative_skin_menu(interaction: discord.Interaction):
    """
    대표 스킨 메인 메뉴를 표시하는 함수
    """
    embed = discord.Embed(
        title="👑 대표 스킨 관리",
        description="원하는 기능을 선택해주세요!",
        color=0xFFD700
    )
    
    view = RepresentativeSkinMainView(interaction.user)
    await interaction.response.send_message(embed=embed, view=view)

class RepresentativeSkinMainView(discord.ui.View):
    def __init__(self, user: discord.Member):
        super().__init__(timeout=300.0)
        self.user = user
    
    @discord.ui.button(label='대표 스킨 지정하기', style=discord.ButtonStyle.green, emoji='⚙️')
    async def set_representative_skin(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ChampionInputModal(self.user)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='대표 스킨 확인하기', style=discord.ButtonStyle.blurple, emoji='👁️')
    async def view_representative_skin(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed, view = await get_representative_skin_list(self.user)
        
        if view:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.edit_message(embed=embed, view=None)

class ChampionInputModal(discord.ui.Modal):
    def __init__(self, user: discord.Member):
        super().__init__(title="챔피언 이름 입력")
        self.user = user
        
        self.champion_input = discord.ui.TextInput(
            label="챔피언 이름 (한글)",
            placeholder="예: 진, 야스오, 징크스...",
            required=True,
            max_length=20
        )
        self.add_item(self.champion_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        champion_name = self.champion_input.value.strip()
        
        # 챔피언 이름 검증 (기존 로직 사용)
        from functions import get_full_champion_eng_name
        champion_eng = get_full_champion_eng_name(champion_name)
        
        if champion_eng is None:
            embed = discord.Embed(
                title="❌ 챔피언 이름 오류",
                description="챔피언 이름을 인식 가능하게 입력해주세요.",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        user_id = str(self.user.id)
        
        # 사용자가 해당 챔피언의 스킨을 보유하고 있는지 확인
        owned_skins = get_user_champion_skins(user_id, champion_name)
        
        # 기본 스킨은 항상 있으므로 owned_skins가 비어있을 수 없음
        if not owned_skins:
            embed = discord.Embed(
                title="❌ 챔피언 정보 없음",
                description=f"**{champion_name}** 챔피언의 정보를 찾을 수 없습니다.",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        # 현재 대표 스킨 확인
        current_representative = get_current_representative_skin(user_id, champion_name)
        
        # 스킨 목록 정렬 (현재 대표 스킨이 있으면 맨 앞으로)
        sorted_skins = sort_skins_by_priority(owned_skins, current_representative)
        
        # 첫 번째 스킨으로 미리보기 시작
        embed, view, image_file = create_skin_preview_embed(self.user, champion_name, sorted_skins, 0, current_representative)
        
        if image_file:
            await interaction.response.edit_message(embed=embed, view=view, attachments=[image_file])
        else:
            await interaction.response.edit_message(embed=embed, view=view)

def get_user_champion_skins(user_id: str, champion_name: str):
    """
    사용자가 보유한 특정 챔피언의 모든 스킨을 조회하는 함수
    기본 스킨(0번)은 항상 포함
    """
    # 사용자가 보유한 스킨들 조회
    query = """
    SELECT s.skin_id, s.skin_name_kr, s.skin_name_en, s.file_name
    FROM user_skins us
    JOIN skins s ON us.skin_id = s.skin_id
    WHERE us.user_id = ? AND s.champion_name_kr = ?
    ORDER BY CAST(s.skin_id AS INTEGER)
    """
    results = execute_select_query(query, (user_id, champion_name))
    
    champion_skins = []
    if results:
        for result in results:
            champion_skins.append({
                "skin_id": result[0],
                "skin_name_kr": result[1],
                "skin_name_en": result[2],
                "file_name": result[3]
            })
    
    # 기본 스킨(0번) 추가 - 항상 보유한다고 가정
    # 기본 스킨 정보 조회
    basic_skin_query = """
    SELECT skin_id, skin_name_kr, skin_name_en, file_name
    FROM skins
    WHERE champion_name_kr = ? AND (skin_id LIKE '%_0' OR skin_id LIKE '%0')
    ORDER BY CAST(skin_id AS INTEGER)
    LIMIT 1
    """
    basic_skin_result = execute_select_query(basic_skin_query, (champion_name,))
    
    if basic_skin_result:
        basic_skin = {
            "skin_id": basic_skin_result[0][0],
            "skin_name_kr": basic_skin_result[0][1],
            "skin_name_en": basic_skin_result[0][2],
            "file_name": basic_skin_result[0][3]
        }
        
        # 기본 스킨이 이미 목록에 있는지 확인 (중복 방지)
        basic_skin_exists = any(skin["skin_id"] == basic_skin["skin_id"] for skin in champion_skins)
        
        if not basic_skin_exists:
            # 기본 스킨을 맨 앞에 추가
            champion_skins.insert(0, basic_skin)
    
    return champion_skins

def get_current_representative_skin(user_id: str, champion_name: str):
    """
    사용자의 특정 챔피언 현재 대표 스킨을 조회하는 함수
    """
    query = """
    SELECT s.skin_id, s.skin_name_kr, s.skin_name_en, s.file_name
    FROM user_representative_skins urs
    JOIN skins s ON urs.skin_id = s.skin_id
    WHERE urs.user_id = ? AND urs.champion_name_kr = ?
    """
    result = execute_select_query(query, (user_id, champion_name))
    
    if result:
        skin_info = result[0]
        return {
            "skin_id": skin_info[0],
            "skin_name_kr": skin_info[1],
            "skin_name_en": skin_info[2],
            "file_name": skin_info[3]
        }
    return None

def sort_skins_by_priority(owned_skins: list, current_representative):
    """
    현재 대표 스킨을 맨 앞으로 정렬하는 함수
    """
    if not current_representative:
        return owned_skins
    
    # 현재 대표 스킨을 찾아서 맨 앞으로 이동
    representative_skin = None
    other_skins = []
    
    for skin in owned_skins:
        if skin["skin_id"] == current_representative["skin_id"]:
            representative_skin = skin
        else:
            other_skins.append(skin)
    
    if representative_skin:
        return [representative_skin] + other_skins
    else:
        return owned_skins

def create_skin_preview_embed(user: discord.Member, champion_name: str, skins: list, current_index: int, current_representative):
    """
    스킨 미리보기 embed를 생성하는 함수
    """
    current_skin = skins[current_index]
    is_current_representative = (current_representative and 
                               current_skin["skin_id"] == current_representative["skin_id"])
    
    # 제목 설정
    title_prefix = "⭐ " if is_current_representative else ""
    title = f"{title_prefix}{champion_name} - {current_skin['skin_name_kr']}"
    
    embed = discord.Embed(
        title=title,
        description=f"**{current_skin['skin_name_en']}**",
        color=0xFFD700 if is_current_representative else 0x00BFFF
    )
    
    # 챔피언 영문명 가져오기
    from functions import get_full_champion_eng_name
    champion_eng = get_full_champion_eng_name(champion_name)
    
    # 로컬 스킨 이미지 파일 경로
    image_file = None
    if champion_eng and current_skin['file_name']:
        
        image_path = get_skin_image_url(champion_eng, current_skin['file_name'])
        
        # 파일이 존재하면 Discord File 객체 생성
        import os
        if image_path and os.path.exists(image_path):
            image_file = discord.File(image_path, filename=f"{current_skin['file_name']}.jpg")
            # embed에서 첨부된 파일을 참조
            embed.set_image(url=f"attachment://{current_skin['file_name']}.jpg")
    
    if is_current_representative:
        embed.add_field(
            name="💎 상태",
            value="현재 설정된 대표 스킨입니다",
            inline=False
        )
    
    # 페이지 정보
    embed.set_footer(text=f"스킨 {current_index + 1} / {len(skins)}")
    
    # View 생성
    view = SkinPreviewView(user, champion_name, skins, current_index, current_representative)
    
    return embed, view, image_file

class SkinPreviewView(discord.ui.View):
    def __init__(self, user: discord.Member, champion_name: str, skins: list, current_index: int, current_representative):
        super().__init__(timeout=300.0)
        self.user = user
        self.champion_name = champion_name
        self.skins = skins
        self.current_index = current_index
        self.current_representative = current_representative
        
        # 버튼 업데이트
        self.update_buttons()
    
    def update_buttons(self):
        """
        현재 상태에 따라 버튼 업데이트
        """
        self.clear_items()
        
        current_skin = self.skins[self.current_index]
        is_current_representative = (self.current_representative and 
                                   current_skin["skin_id"] == self.current_representative["skin_id"])
        
        # 이 스킨 지정하기 버튼
        if is_current_representative:
            set_button = discord.ui.Button(
                label="현재 대표 스킨입니다",
                style=discord.ButtonStyle.secondary,
                emoji="⭐",
                disabled=True
            )
        else:
            set_button = discord.ui.Button(
                label="이 스킨 지정하기",
                style=discord.ButtonStyle.green,
                emoji="🎯"
            )
            set_button.callback = self.set_this_skin
        
        self.add_item(set_button)
        
        # 다음 스킨 보기 버튼
        next_button = discord.ui.Button(
            label="다음 스킨 보기",
            style=discord.ButtonStyle.blurple,
            emoji="➡️"
        )
        next_button.callback = self.next_skin
        self.add_item(next_button)
        
        # 기본 스킨으로 설정 버튼
        default_button = discord.ui.Button(
            label="기본 스킨으로 설정",
            style=discord.ButtonStyle.red,
            emoji="🔄"
        )
        default_button.callback = self.set_default_skin
        self.add_item(default_button)
    
    async def set_this_skin(self, interaction: discord.Interaction):
        """
        현재 스킨을 대표 스킨으로 설정
        """
        user_id = str(self.user.id)
        current_skin = self.skins[self.current_index]
        
        # 챔피언 영문명 조회 (실제로는 변환 함수 사용)
        query = "SELECT champion_name_en FROM skins WHERE skin_id = ?"
        result = execute_select_query(query, (current_skin["skin_id"],))
        champion_name_en = result[0][0] if result else ""
        
        # 대표 스킨 설정
        success = set_representative_skin(user_id, self.champion_name, champion_name_en, current_skin["skin_id"])
        
        if success:
            embed = discord.Embed(
                title="✅ 대표 스킨 설정 완료",
                description=f"**{self.champion_name}**의 대표 스킨이\n**{current_skin['skin_name_kr']}**로 설정되었습니다!",
                color=0x00FF00
            )
        else:
            embed = discord.Embed(
                title="❌ 설정 실패",
                description="대표 스킨 설정에 실패했습니다.",
                color=0xFF0000
            )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def next_skin(self, interaction: discord.Interaction):
        """
        다음 스킨으로 이동 (순환)
        """
        self.current_index = (self.current_index + 1) % len(self.skins)
        self.update_buttons()
        
        embed, _, image_file = create_skin_preview_embed(
            self.user, 
            self.champion_name, 
            self.skins, 
            self.current_index, 
            self.current_representative
        )
        
        if image_file:
            await interaction.response.edit_message(embed=embed, view=self, attachments=[image_file])
        else:
            await interaction.response.edit_message(embed=embed, view=self)
    
    async def set_default_skin(self, interaction: discord.Interaction):
        """
        기본 스킨으로 설정 (대표 스킨 제거)
        """
        user_id = str(self.user.id)
        
        # 대표 스킨 제거 (기본 스킨으로 돌아감)
        success = remove_representative_skin(user_id, self.champion_name)
        
        if success:
            embed = discord.Embed(
                title="✅ 기본 스킨으로 설정 완료",
                description=f"**{self.champion_name}**의 대표 스킨이 기본 스킨으로 설정되었습니다.\n(모든 유저가 기본적으로 보유한 스킨입니다)",
                color=0x00FF00
            )
        else:
            embed = discord.Embed(
                title="❌ 설정 실패",
                description="기본 스킨 설정에 실패했습니다.",
                color=0xFF0000
            )
        
        await interaction.response.edit_message(embed=embed, view=None)

def set_representative_skin(user_id: str, champion_name_kr: str, champion_name_en: str, skin_id: str):
    """
    사용자의 챔피언별 대표 스킨을 설정하는 함수
    """
    # 기존 대표 스킨이 있는지 확인
    check_existing_query = "SELECT skin_id FROM user_representative_skins WHERE user_id = ? AND champion_name_kr = ?"
    existing_result = execute_select_query(check_existing_query, (user_id, champion_name_kr))
    
    if existing_result:
        # 기존 대표 스킨 업데이트
        update_query = """
        UPDATE user_representative_skins 
        SET skin_id = ?, champion_name_en = ?, set_at = CURRENT_TIMESTAMP 
        WHERE user_id = ? AND champion_name_kr = ?
        """
        success = execute_post_query(update_query, (skin_id, champion_name_en, user_id, champion_name_kr))
    else:
        # 새로운 대표 스킨 설정
        insert_query = """
        INSERT INTO user_representative_skins (user_id, champion_name_kr, champion_name_en, skin_id) 
        VALUES (?, ?, ?, ?)
        """
        success = execute_post_query(insert_query, (user_id, champion_name_kr, champion_name_en, skin_id))
    
    return success

def remove_representative_skin(user_id: str, champion_name_kr: str):
    """
    사용자의 특정 챔피언 대표 스킨을 제거하는 함수
    """
    query = "DELETE FROM user_representative_skins WHERE user_id = ? AND champion_name_kr = ?"
    success = execute_post_query(query, (user_id, champion_name_kr))
    return success

async def get_representative_skin_list(user: discord.Member):
    """
    사용자의 대표 스킨을 조회하여 페이지네이션으로 표시하는 함수 (기존 코드)
    """
    user_id = str(user.id)
    
    # 사용자의 모든 대표 스킨 조회
    query = """
    SELECT urs.champion_name_kr, s.skin_name_kr, urs.set_at
    FROM user_representative_skins urs
    JOIN skins s ON urs.skin_id = s.skin_id
    WHERE urs.user_id = ?
    ORDER BY urs.champion_name_kr
    """
    
    results = execute_select_query(query, (user_id,))
    
    if not results:
        # 대표 스킨이 없는 경우
        embed = discord.Embed(
            title=f"👑 {user.display_name}님의 대표 스킨",
            description="설정된 대표 스킨이 없습니다.\n`대표 스킨 지정하기`를 통해 대표 스킨을 설정해보세요!",
            color=0x808080
        )
        return embed, None
    
    # 대표 스킨이 있는 경우 페이지네이션 View 생성
    representative_skins = []
    for result in results:
        champion_name = result[0]
        skin_name = result[1]
        set_at = result[2]
        representative_skins.append({
            "champion": champion_name,
            "skin": skin_name,
            "set_at": set_at
        })
    
    # 첫 번째 페이지 embed 생성
    embed = create_representative_skin_embed(user, representative_skins, 0)
    
    # 페이지가 여러 개인 경우에만 View 생성
    if len(representative_skins) > 10:
        view = RepresentativeSkinPageView(user, representative_skins)
        return embed, view
    else:
        return embed, None

def create_representative_skin_embed(user: discord.Member, representative_skins: list, page: int):
    """
    대표 스킨 embed를 생성하는 함수 (기존 코드)
    """
    total_pages = math.ceil(len(representative_skins) / 10)
    start_idx = page * 10
    end_idx = min(start_idx + 10, len(representative_skins))
    page_skins = representative_skins[start_idx:end_idx]
    
    embed = discord.Embed(
        title=f"👑 {user.display_name}님의 대표 스킨",
        description=f"총 **{len(representative_skins)}개** 챔피언의 대표 스킨이 설정되어 있습니다.",
        color=0xFFD700
    )
    
    # 현재 페이지의 스킨들을 필드로 추가
    for skin_info in page_skins:
        champion = skin_info["champion"]
        skin = skin_info["skin"]
        
        embed.add_field(
            name=f"🔸 {champion}",
            value=f"**{skin}**",
            inline=True
        )
    
    # 페이지 정보 추가
    if total_pages > 1:
        embed.set_footer(text=f"페이지 {page + 1} / {total_pages}")
    
    return embed

class RepresentativeSkinPageView(discord.ui.View):
    def __init__(self, user: discord.Member, representative_skins: list):
        super().__init__(timeout=300.0)
        self.user = user
        self.representative_skins = representative_skins
        self.current_page = 0
        self.total_pages = math.ceil(len(representative_skins) / 10)
        
        # 페이지가 1개뿐이면 버튼 추가하지 않음
        if self.total_pages <= 1:
            return
        
        # 첫 페이지에서는 이전 버튼 비활성화
        self.update_buttons()
    
    def update_buttons(self):
        """
        현재 페이지에 따라 버튼 활성화/비활성화 업데이트
        """
        # 기존 버튼들 제거
        self.clear_items()
        
        # 이전 버튼
        prev_button = discord.ui.Button(
            label="이전",
            style=discord.ButtonStyle.gray,
            emoji="◀️",
            disabled=(self.current_page == 0)
        )
        prev_button.callback = self.previous_page
        self.add_item(prev_button)
        
        # 페이지 정보 버튼
        page_button = discord.ui.Button(
            label=f"{self.current_page + 1} / {self.total_pages}",
            style=discord.ButtonStyle.secondary,
            disabled=True
        )
        self.add_item(page_button)
        
        # 다음 버튼
        next_button = discord.ui.Button(
            label="다음",
            style=discord.ButtonStyle.gray,
            emoji="▶️",
            disabled=(self.current_page == self.total_pages - 1)
        )
        next_button.callback = self.next_page
        self.add_item(next_button)
    
    async def previous_page(self, interaction: discord.Interaction):
        """
        이전 페이지로 이동
        """
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            
            embed = create_representative_skin_embed(
                self.user, 
                self.representative_skins, 
                self.current_page
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    async def next_page(self, interaction: discord.Interaction):
        """
        다음 페이지로 이동
        """
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            
            embed = create_representative_skin_embed(
                self.user, 
                self.representative_skins, 
                self.current_page
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    async def on_timeout(self):
        """
        타임아웃 시 버튼 비활성화
        """
        for item in self.children:
            item.disabled = True