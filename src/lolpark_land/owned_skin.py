import discord
from lolpark_land.land_functions import execute_select_query
from lolpark_land.representative_skin import get_current_representative_skin

async def show_owned_skins(interaction: discord.Interaction, champion_name: str = None):
    """
    보유 스킨을 조회하는 함수
    champion_name이 있으면 특정 챔피언, 없으면 모든 챔피언 순회
    """
    user_id = str(interaction.user.id)
    
    if champion_name:
        # 특정 챔피언의 보유 스킨 조회
        await show_champion_owned_skins(interaction, user_id, champion_name)
    else:
        # 모든 챔피언 순회
        await show_all_champions_skins(interaction, user_id)

async def show_champion_owned_skins(interaction: discord.Interaction, user_id: str, champion_name: str):
    """
    특정 챔피언의 보유 스킨을 표시하는 함수
    """
    # 챔피언 이름 검증
    from functions import get_full_champion_eng_name
    champion_eng = get_full_champion_eng_name(champion_name)
    
    if champion_eng is None:
        embed = discord.Embed(
            title="❌ 챔피언 이름 오류",
            description="챔피언 이름을 인식 가능하게 입력해주세요.",
            color=0xFF0000
        )
        await interaction.edit_original_response(embed=embed)
        return
    
    # 보유 스킨 조회 (기본 스킨 포함)
    owned_skins = get_champion_owned_skins(user_id, champion_name)
    
    # 현재 대표 스킨 조회
    representative_skin = get_current_representative_skin(user_id, champion_name)
    
    if not owned_skins:
        embed = discord.Embed(
            title=f"📦 {champion_name} 보유 스킨",
            description=f"**{champion_name}**의 스킨을 보유하고 있지 않습니다.\n(기본 스킨은 항상 보유)",
            color=0x808080
        )
        # 기본 스킨만 표시
        if not representative_skin:  # 대표 스킨이 없으면 기본 스킨이 대표
            embed.add_field(
                name="보유 스킨",
                value=f"⭐ **{champion_name}** (대표 스킨)",
                inline=False
            )
        else:
            embed.add_field(
                name="보유 스킨",
                value=f"**{champion_name}**",
                inline=False
            )
    else:
        embed = discord.Embed(
            title=f"📦 {champion_name} 보유 스킨",
            description=f"**{champion_name}**의 보유 스킨 목록입니다.\n총 **{len(owned_skins)}개** 스킨을 보유하고 있습니다.",
            color=0x00BFFF
        )
        
        # 스킨 목록 추가
        skin_list = []
        for skin in owned_skins:
            skin_name = skin['skin_name_kr']
            
            # 대표 스킨 확인
            if representative_skin and skin["skin_id"] == representative_skin["skin_id"]:
                # 설정된 대표 스킨
                skin_list.append(f"⭐ **{skin_name}** (대표 스킨)")
            elif skin["skin_id"].endswith("_0") and not representative_skin:
                # 대표 스킨이 없으면 기본 스킨이 대표
                skin_list.append(f"⭐ **{skin_name}** (대표 스킨)")
            else:
                # 일반 스킨
                skin_list.append(f"**{skin_name}**")
        
        # 스킨이 많으면 여러 필드로 나누기
        if len(skin_list) <= 10:
            embed.add_field(
                name="보유 스킨 목록",
                value="\n".join(skin_list),
                inline=False
            )
        else:
            # 10개씩 나누어서 표시
            for i in range(0, len(skin_list), 10):
                field_skins = skin_list[i:i+10]
                field_name = f"보유 스킨 목록 ({i+1}-{min(i+10, len(skin_list))})"
                embed.add_field(
                    name=field_name,
                    value="\n".join(field_skins),
                    inline=True
                )
    
    await interaction.edit_original_response(embed=embed)

async def show_all_champions_skins(interaction: discord.Interaction, user_id: str):
    """
    모든 챔피언의 보유 스킨을 순회하며 표시하는 함수
    """
    # 스킨을 보유한 챔피언들 조회
    champions_with_skins = get_all_champions_with_skins(user_id)
    
    if not champions_with_skins:
        embed = discord.Embed(
            title="📦 보유 스킨 목록",
            description="보유한 스킨이 없습니다.\n뽑기를 통해 스킨을 획득해보세요!",
            color=0x808080
        )
        await interaction.edit_original_response(embed=embed)
        return
    
    # 첫 번째 챔피언으로 시작
    embed, view = create_champion_skins_embed(interaction.user, champions_with_skins, 0)
    await interaction.edit_original_response(embed=embed, view=view)

def get_champion_owned_skins(user_id: str, champion_name: str):
    """
    특정 챔피언의 보유 스킨을 조회하는 함수 (기본 스킨 포함)
    """
    # 사용자가 보유한 스킨들 조회
    query = """
    SELECT s.skin_id, s.skin_name_kr, s.skin_name_en, s.file_name
    FROM user_skins us
    JOIN skins s ON us.skin_id = s.skin_id
    WHERE us.user_id = ? AND s.champion_name_kr = ?
    ORDER BY CAST(REPLACE(s.skin_id, '_', '') AS INTEGER)
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
    
    # 기본 스킨 추가 (항상 보유)
    from functions import get_full_champion_eng_name
    champion_eng = get_full_champion_eng_name(champion_name)
    
    if champion_eng:
        basic_skin = {
            "skin_id": f"{champion_eng}_0",
            "skin_name_kr": f"{champion_name}",
            "skin_name_en": f"{champion_eng}",
            "file_name": f"{champion_eng}_0"
        }
        
        # 기본 스킨을 맨 앞에 추가
        champion_skins.insert(0, basic_skin)
    
    return champion_skins

def get_all_champions_with_skins(user_id: str):
    """
    스킨을 보유한 모든 챔피언들을 조회하는 함수
    """
    query = """
    SELECT DISTINCT s.champion_name_kr, s.champion_name_en
    FROM user_skins us
    JOIN skins s ON us.skin_id = s.skin_id
    WHERE us.user_id = ?
    ORDER BY s.champion_name_kr
    """
    results = execute_select_query(query, (user_id,))
    
    champions = []
    if results:
        for result in results:
            champion_kr = result[0]
            champion_en = result[1]
            
            # 해당 챔피언의 보유 스킨 수 조회
            owned_skins = get_champion_owned_skins(user_id, champion_kr)
            
            champions.append({
                "champion_name_kr": champion_kr,
                "champion_name_en": champion_en,
                "owned_skins": owned_skins,
                "skin_count": len(owned_skins)
            })
    
    return champions

def create_champion_skins_embed(user: discord.Member, champions_data: list, current_index: int):
    """
    챔피언별 보유 스킨 embed를 생성하는 함수
    """
    current_champion = champions_data[current_index]
    champion_name = current_champion["champion_name_kr"]
    owned_skins = current_champion["owned_skins"]
    
    embed = discord.Embed(
        title=f"📦 {champion_name} 보유 스킨",
        description=f"**{champion_name}**의 보유 스킨 목록입니다.\n총 **{len(owned_skins)}개** 스킨을 보유하고 있습니다.",
        color=0x00BFFF
    )
    
    # 현재 대표 스킨 조회
    user_id = str(user.id)
    representative_skin = get_current_representative_skin(user_id, champion_name)
    
    # 스킨 목록 추가
    skin_list = []
    for skin in owned_skins:
        skin_name = skin['skin_name_kr']
        
        # 대표 스킨 확인
        if representative_skin and skin["skin_id"] == representative_skin["skin_id"]:
            # 설정된 대표 스킨
            skin_list.append(f"⭐ **{skin_name}** (대표 스킨)")
        elif skin["skin_id"].endswith("_0") and not representative_skin:
            # 대표 스킨이 없으면 기본 스킨이 대표
            skin_list.append(f"⭐ **{skin_name}** (대표 스킨)")
        else:
            # 일반 스킨
            skin_list.append(f"**{skin_name}**")
    
    # 스킨이 많으면 여러 필드로 나누기
    if len(skin_list) <= 15:
        embed.add_field(
            name="보유 스킨 목록",
            value="\n".join(skin_list),
            inline=False
        )
    else:
        # 15개씩 나누어서 표시
        for i in range(0, len(skin_list), 15):
            field_skins = skin_list[i:i+15]
            field_name = f"보유 스킨 목록 ({i+1}-{min(i+15, len(skin_list))})"
            embed.add_field(
                name=field_name,
                value="\n".join(field_skins),
                inline=True
            )
    
    # 페이지 정보
    embed.set_footer(text=f"챔피언 {current_index + 1} / {len(champions_data)}")
    
    # View 생성
    view = ChampionSkinsNavigationView(user, champions_data, current_index)
    
    return embed, view

class ChampionSkinsNavigationView(discord.ui.View):
    def __init__(self, user: discord.Member, champions_data: list, current_index: int):
        super().__init__(timeout=300.0)
        self.user = user
        self.champions_data = champions_data
        self.current_index = current_index
        
        # 버튼 업데이트
        self.update_buttons()
    
    def update_buttons(self):
        """
        현재 페이지에 따라 버튼 활성화/비활성화 업데이트
        """
        self.clear_items()
        
        # 이전 챔피언 버튼
        prev_button = discord.ui.Button(
            label="이전 챔피언",
            style=discord.ButtonStyle.gray,
            emoji="◀️",
            disabled=(self.current_index == 0)
        )
        prev_button.callback = self.previous_champion
        self.add_item(prev_button)
        
        # 챔피언 정보 버튼 (비활성화된 버튼으로 현재 챔피언 표시)
        champion_name = self.champions_data[self.current_index]["champion_name_kr"]
        info_button = discord.ui.Button(
            label=f"{champion_name} ({self.current_index + 1}/{len(self.champions_data)})",
            style=discord.ButtonStyle.secondary,
            disabled=True
        )
        self.add_item(info_button)
        
        # 다음 챔피언 버튼
        next_button = discord.ui.Button(
            label="다음 챔피언",
            style=discord.ButtonStyle.gray,
            emoji="▶️",
            disabled=(self.current_index == len(self.champions_data) - 1)
        )
        next_button.callback = self.next_champion
        self.add_item(next_button)
        
        # 챔피언 검색 버튼
        search_button = discord.ui.Button(
            label="챔피언 검색",
            style=discord.ButtonStyle.green,
            emoji="🔍"
        )
        search_button.callback = self.search_champion
        self.add_item(search_button)
    
    async def previous_champion(self, interaction: discord.Interaction):
        """
        이전 챔피언으로 이동
        """
        if self.current_index > 0:
            self.current_index -= 1
            self.update_buttons()
            
            embed, _ = create_champion_skins_embed(
                self.user,
                self.champions_data,
                self.current_index
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    async def next_champion(self, interaction: discord.Interaction):
        """
        다음 챔피언으로 이동
        """
        if self.current_index < len(self.champions_data) - 1:
            self.current_index += 1
            self.update_buttons()
            
            embed, _ = create_champion_skins_embed(
                self.user,
                self.champions_data,
                self.current_index
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    async def search_champion(self, interaction: discord.Interaction):
        """
        챔피언 검색 Modal 표시
        """
        modal = ChampionSearchModal(self)
        await interaction.response.send_modal(modal)
    
    async def jump_to_champion(self, champion_name: str, interaction: discord.Interaction):
        """
        특정 챔피언으로 바로 이동
        """
        # 챔피언 이름으로 인덱스 찾기
        for i, champion_data in enumerate(self.champions_data):
            if champion_data["champion_name_kr"] == champion_name:
                self.current_index = i
                self.update_buttons()
                
                embed, _ = create_champion_skins_embed(
                    self.user,
                    self.champions_data,
                    self.current_index
                )
                
                await interaction.response.edit_message(embed=embed, view=self)
                return True
        
        return False
    
    async def on_timeout(self):
        """
        타임아웃 시 버튼 비활성화
        """
        for item in self.children:
            item.disabled = True

class ChampionSearchModal(discord.ui.Modal):
    def __init__(self, navigation_view):
        super().__init__(title="챔피언 검색")
        self.navigation_view = navigation_view
        
        self.champion_input = discord.ui.TextInput(
            label="챔피언 이름 (한글)",
            placeholder="예: 진, 야스오, 징크스...",
            required=True,
            max_length=20
        )
        self.add_item(self.champion_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        search_name = self.champion_input.value.strip()
        
        # 챔피언 이름 검증
        from functions import get_full_champion_eng_name
        champion_eng = get_full_champion_eng_name(search_name)
        
        if champion_eng is None:
            embed = discord.Embed(
                title="❌ 챔피언 이름 오류",
                description="챔피언 이름을 인식 가능하게 입력해주세요.",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        # 해당 챔피언이 스킨을 보유하고 있는지 확인
        success = await self.navigation_view.jump_to_champion(search_name, interaction)
        
        if not success:
            embed = discord.Embed(
                title="❌ 챔피언 없음",
                description=f"**{search_name}**의 스킨을 보유하고 있지 않습니다.\n(기본 스킨만 보유한 챔피언은 목록에 표시되지 않습니다)",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=self.navigation_view)