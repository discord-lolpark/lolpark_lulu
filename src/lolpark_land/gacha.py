import discord
from discord.ext import commands
from lolpark_land.land_functions import draw_random_skin

# ===== 상자 정보 설정 =====
BOX_INFO = {
    "normal": {
        "title": "📦 일반 상자",
        "description": "**모든 스킨**에서 무작위로 뽑을 수 있는 기본 상자입니다.\n모든 등급의 스킨이 동일한 확률로 나옵니다.",
        "price": 100,
        "color": 0x808080
    },
    "premium": {
        "title": "💎 고급 상자",
        "description": "**레어 등급 이상** 스킨만 나오는 프리미엄 상자입니다.\n높은 등급의 스킨을 획득할 확률이 높습니다!",
        "price": 300,
        "color": 0x00ff00
    },
    "line": {
        "title": "🎯 라인별 상자",
        "description": "**특정 라인의 챔피언** 스킨만 나오는 상자입니다.\n원하는 라인을 선택해주세요!",
        "price": 1000,
        "color": 0x5865f2
    },
    "theme": {
        "title": "✨ 테마 상자",
        "description": "**특정 테마의 스킨**만 나오는 상자입니다.\n별 수호자, 프로젝트, K/DA 등 다양한 테마를 선택할 수 있습니다.",
        "price": 3000,
        "color": 0xed4245
    },
    "most_pick": {
        "title": "🔥 모스트 픽 상자",
        "description": "**본인 모스트 픽 5개 챔피언**의 스킨만 나오는 롤파크 프리미엄 전용 상자입니다!",
        "price": 2000,
        "color": 0xffa500
    }
}

# 라인별 상자 정보
LINE_INFO = {
    "top": {"title": "탑 라인 상자", "description": "탑 라인 챔피언들의 스킨만 나오는 상자입니다.", "color": 0x8B4513},
    "jungle": {"title": "정글 상자", "description": "정글 챔피언들의 스킨만 나오는 상자입니다.", "color": 0x228B22},
    "mid": {"title": "미드 라인 상자", "description": "미드 라인 챔피언들의 스킨만 나오는 상자입니다.", "color": 0x4169E1},
    "bot": {"title": "원딜 상자", "description": "원딜 챔피언들의 스킨만 나오는 상자입니다.", "color": 0xDC143C},
    "support": {"title": "서포터 상자", "description": "서포터 챔피언들의 스킨만 나오는 상자입니다.", "color": 0x708090}
}

# 메인 메뉴 정보
MAIN_MENU = {
    "title": "🎁 롤파크 스킨 뽑기",
    "description": "원하는 상자를 선택해주세요!",
    "color": 0x00ff00
}

class GachaButtonView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60.0)
        self.user_id = user_id
        
    def add_premium_button(self):
        """프리미엄 유저를 위한 모스트 픽 상자 버튼 추가"""
        self.add_item(MostPickButton())

    @discord.ui.button(label='일반 상자', style=discord.ButtonStyle.gray, emoji='📦')
    async def normal_box(self, interaction: discord.Interaction, button: discord.ui.Button):
        box_info = BOX_INFO["normal"]
        embed = discord.Embed(
            title=box_info["title"],
            description=box_info["description"],
            color=box_info["color"]
        )
        view = ConfirmGachaView(self.user_id, box_type="normal", price=box_info["price"])
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='고급 상자', style=discord.ButtonStyle.green, emoji='💎')
    async def premium_box(self, interaction: discord.Interaction, button: discord.ui.Button):
        box_info = BOX_INFO["premium"]
        embed = discord.Embed(
            title=box_info["title"],
            description=box_info["description"],
            color=box_info["color"]
        )
        view = ConfirmGachaView(self.user_id, box_type="premium", price=box_info["price"])
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='라인별 상자', style=discord.ButtonStyle.blurple, emoji='🎯')
    async def line_box(self, interaction: discord.Interaction, button: discord.ui.Button):
        box_info = BOX_INFO["line"]
        embed = discord.Embed(
            title=box_info["title"],
            description=box_info["description"],
            color=box_info["color"]
        )
        view = LineButtonView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='테마 상자', style=discord.ButtonStyle.red, emoji='✨')
    async def theme_box(self, interaction: discord.Interaction, button: discord.ui.Button):
        box_info = BOX_INFO["theme"]
        embed = discord.Embed(
            title=box_info["title"],
            description=box_info["description"],
            color=box_info["color"]
        )
        view = ThemeSelectView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='뽑기 취소', style=discord.ButtonStyle.red, emoji='❌')
    async def cancel_gacha(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ 뽑기 취소",
            description="뽑기를 취소했습니다.",
            color=0xff0000
        )
        await interaction.response.edit_message(embed=embed, view=None)

class MostPickButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='모스트 픽 상자', style=discord.ButtonStyle.secondary, emoji='🔥')
    
    async def callback(self, interaction: discord.Interaction):
        box_info = BOX_INFO["most_pick"]
        embed = discord.Embed(
            title=box_info["title"],
            description=box_info["description"],
            color=box_info["color"]
        )
        view = ConfirmGachaView(self.view.user_id, box_type="most_pick", price=box_info["price"], is_most_pick=True)
        await interaction.response.edit_message(embed=embed, view=view)

class ConfirmGachaView(discord.ui.View):
    def __init__(self, user_id, box_type, price, line_type=None, theme=None, is_most_pick=False):
        super().__init__(timeout=60.0)
        self.user_id = user_id
        self.box_type = box_type
        self.price = price
        self.line_type = line_type
        self.theme = theme
        self.is_most_pick = is_most_pick
        
        # 뽑기 버튼을 동적으로 생성 (초록색)
        draw_button = discord.ui.Button(
            label=f'뽑기 ({self.price:,}LC)',
            style=discord.ButtonStyle.green,
            emoji='🎰'
        )
        draw_button.callback = self.confirm_gacha
        self.add_item(draw_button)
        
        # 돌아가기 버튼 (빨간색)
        back_button = discord.ui.Button(
            label='돌아가기',
            style=discord.ButtonStyle.red,
            emoji='🔙'
        )
        back_button.callback = self.back_to_main
        self.add_item(back_button)
    
    async def confirm_gacha(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # 실제 뽑기 실행
        await self.handle_gacha(interaction)
    
    async def back_to_main(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=MAIN_MENU["title"],
            description=MAIN_MENU["description"],
            color=MAIN_MENU["color"]
        )
        # 원래 메인 메뉴로 돌아가기 (프리미엄 확인 포함)
        view = GachaButtonView(self.user_id)
        
        # 프리미엄 유저 확인 - interaction.user 사용
        has_premium = discord.utils.get(interaction.user.roles, name="LOLPARK PREMIUM")
        if has_premium:
            view.add_premium_button()
            
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def handle_gacha(self, interaction):
        """실제 뽑기 실행"""
        # 뽑기 실행
        if self.box_type == "normal":
            result = draw_random_skin(self.user_id)
        elif self.box_type == "premium":
            result = draw_random_skin(self.user_id)
        elif self.line_type:
            result = draw_random_skin(self.user_id, line_type=self.line_type)
        elif self.theme:
            result = draw_random_skin(self.user_id, box_type=self.theme)
        elif self.is_most_pick:
            result = draw_random_skin(self.user_id, is_most_pick=True)
        else:
            result = draw_random_skin(self.user_id)
        
        # 결과 표시
        if result:
            embed = discord.Embed(
                title="🎉 스킨 획득!",
                description=f"**{result['skin_name_kr']}**\n({result['champion_name_kr']})",
                color=0xffd700
            )
            embed.add_field(name="등급", value=result.get('rarity', 'RARE'), inline=True)
            embed.add_field(name="챔피언", value=f"{result['champion_name_kr']} ({result['champion_name_en']})", inline=True)
            embed.add_field(name="소모된 LC", value=f"{self.price:,} LC", inline=True)
        else:
            embed = discord.Embed(
                title="❌ 오류 발생",
                description="뽑기에 실패했습니다. 다시 시도해주세요.",
                color=0xff0000
            )
        
        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)

class LineButtonView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60.0)
        self.user_id = user_id
    
    @discord.ui.button(label='탑 뽑기', style=discord.ButtonStyle.blurple)
    async def top_gacha(self, interaction: discord.Interaction, button: discord.ui.Button):
        line_info = LINE_INFO["top"]
        embed = discord.Embed(
            title=line_info["title"],
            description=line_info["description"],
            color=line_info["color"]
        )
        view = ConfirmGachaView(self.user_id, box_type="line", price=BOX_INFO["line"]["price"], line_type="top")
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='정글 뽑기', style=discord.ButtonStyle.blurple)
    async def jungle_gacha(self, interaction: discord.Interaction, button: discord.ui.Button):
        line_info = LINE_INFO["jungle"]
        embed = discord.Embed(
            title=line_info["title"],
            description=line_info["description"],
            color=line_info["color"]
        )
        view = ConfirmGachaView(self.user_id, box_type="line", price=BOX_INFO["line"]["price"], line_type="jungle")
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='미드 뽑기', style=discord.ButtonStyle.blurple)
    async def mid_gacha(self, interaction: discord.Interaction, button: discord.ui.Button):
        line_info = LINE_INFO["mid"]
        embed = discord.Embed(
            title=line_info["title"],
            description=line_info["description"],
            color=line_info["color"]
        )
        view = ConfirmGachaView(self.user_id, box_type="line", price=BOX_INFO["line"]["price"], line_type="mid")
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='원딜 뽑기', style=discord.ButtonStyle.blurple)
    async def bot_gacha(self, interaction: discord.Interaction, button: discord.ui.Button):
        line_info = LINE_INFO["bot"]
        embed = discord.Embed(
            title=line_info["title"],
            description=line_info["description"],
            color=line_info["color"]
        )
        view = ConfirmGachaView(self.user_id, box_type="line", price=BOX_INFO["line"]["price"], line_type="bot")
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='서포터 뽑기', style=discord.ButtonStyle.blurple)
    async def support_gacha(self, interaction: discord.Interaction, button: discord.ui.Button):
        line_info = LINE_INFO["support"]
        embed = discord.Embed(
            title=line_info["title"],
            description=line_info["description"],
            color=line_info["color"]
        )
        view = ConfirmGachaView(self.user_id, box_type="line", price=BOX_INFO["line"]["price"], line_type="support")
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='돌아가기', style=discord.ButtonStyle.red, emoji='🔙')
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title=MAIN_MENU["title"],
            description=MAIN_MENU["description"],
            color=MAIN_MENU["color"]
        )
        view = GachaButtonView(self.user_id)
        
        # 프리미엄 유저 확인
        has_premium = discord.utils.get(interaction.user.roles, name="LOLPARK PREMIUM")
        if has_premium:
            view.add_premium_button()
            
        await interaction.response.edit_message(embed=embed, view=view)

class RepresentativeSkinChoiceView(discord.ui.View):
    def __init__(self, user_id, champion_name_kr, champion_name_en, skin_id, skin_name):
        super().__init__(timeout=120.0)  # 2분 타임아웃
        self.user_id = user_id
        self.champion_name_kr = champion_name_kr
        self.champion_name_en = champion_name_en
        self.skin_id = skin_id
        self.skin_name = skin_name
    
    @discord.ui.button(label='대표 스킨으로 설정', style=discord.ButtonStyle.green, emoji='👑')
    async def set_representative(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 뽑은 사람만 버튼 사용 가능
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ 본인만 설정할 수 있습니다.", ephemeral=True)
            return
        
        from lolpark_land.land_database import set_representative_skin
        
        # 대표 스킨 설정
        success = set_representative_skin(self.user_id, self.champion_name_kr, self.champion_name_en, self.skin_id)
        
        if success:
            embed = discord.Embed(
                title="✅ 대표 스킨 설정 완료",
                description=f"**{self.skin_name}**이(가) **{self.champion_name_kr}**의 대표 스킨으로 설정되었습니다!",
                color=0x00FF00
            )
        else:
            embed = discord.Embed(
                title="❌ 설정 실패",
                description="대표 스킨 설정에 실패했습니다. 다시 시도해주세요.",
                color=0xFF0000
            )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label='나중에 설정', style=discord.ButtonStyle.gray, emoji='⏰')
    async def skip_setting(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 뽑은 사람만 버튼 사용 가능
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ 본인만 선택할 수 있습니다.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⏰ 대표 스킨 설정 건너뜀",
            description=f"**{self.skin_name}**의 대표 스킨 설정을 건너뛰었습니다.\n나중에 `/대표스킨` 명령어로 설정할 수 있습니다.",
            color=0x808080
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def on_timeout(self):
        """
        타임아웃 시 메시지 수정
        """
        embed = discord.Embed(
            title="⏰ 시간 초과",
            description="대표 스킨 설정 시간이 초과되었습니다.\n`/대표스킨` 명령어로 나중에 설정할 수 있습니다.",
            color=0x808080
        )
        # 메시지 수정 시도 (이미 수정되었을 수도 있음)
        try:
            await self.message.edit(embed=embed, view=None)
        except:
            pass

class RepresentativeSkinChoiceView(discord.ui.View):
    def __init__(self, user_id, champion_name_kr, champion_name_en, skin_id, skin_name):
        super().__init__(timeout=120.0)  # 2분 타임아웃
        self.user_id = user_id
        self.champion_name_kr = champion_name_kr
        self.champion_name_en = champion_name_en
        self.skin_id = skin_id
        self.skin_name = skin_name
    
    @discord.ui.button(label='대표 스킨으로 설정', style=discord.ButtonStyle.green, emoji='👑')
    async def set_representative(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 뽑은 사람만 버튼 사용 가능
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ 본인만 설정할 수 있습니다.", ephemeral=True)
            return
        
        from lolpark_land.land_database import set_representative_skin
        
        # 대표 스킨 설정
        success = set_representative_skin(self.user_id, self.champion_name_kr, self.champion_name_en, self.skin_id)
        
        if success:
            embed = discord.Embed(
                title="✅ 대표 스킨 설정 완료",
                description=f"**{self.skin_name}**이(가) **{self.champion_name_kr}**의 대표 스킨으로 설정되었습니다!",
                color=0x00FF00
            )
        else:
            embed = discord.Embed(
                title="❌ 설정 실패",
                description="대표 스킨 설정에 실패했습니다. 다시 시도해주세요.",
                color=0xFF0000
            )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label='나중에 설정', style=discord.ButtonStyle.gray, emoji='⏰')
    async def skip_setting(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 뽑은 사람만 버튼 사용 가능
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ 본인만 선택할 수 있습니다.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⏰ 대표 스킨 설정 건너뜀",
            description=f"**{self.skin_name}**의 대표 스킨 설정을 건너뛰었습니다.\n나중에 `/대표스킨` 명령어로 설정할 수 있습니다.",
            color=0x808080
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def on_timeout(self):
        """
        타임아웃 시 메시지 수정
        """
        embed = discord.Embed(
            title="⏰ 시간 초과",
            description="대표 스킨 설정 시간이 초과되었습니다.\n`/대표스킨` 명령어로 나중에 설정할 수 있습니다.",
            color=0x808080
        )
        # 메시지 수정 시도 (이미 수정되었을 수도 있음)
        try:
            await self.message.edit(embed=embed, view=None)
        except:
            pass

class ThemeSelectView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60.0)
        self.user_id = user_id
    
    @discord.ui.select(
        placeholder="테마를 선택하세요...",
        options=[
            discord.SelectOption(label="별 수호자", value="별 수호자", emoji="⭐"),
            discord.SelectOption(label="프로젝트", value="프로젝트", emoji="🤖"),
            discord.SelectOption(label="K/DA", value="K/DA", emoji="💃"),
            discord.SelectOption(label="아케이드", value="아케이드", emoji="🕹️"),
            discord.SelectOption(label="블러드 문", value="블러드 문", emoji="🌙")
        ]
    )
    async def theme_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        selected_theme = select.values[0]
        
        embed = discord.Embed(
            title=f"✨ {selected_theme} 테마 상자",
            description=f"**{selected_theme} 테마**의 스킨만 나오는 상자입니다.",
            color=0xed4245
        )
        
        view = ConfirmGachaView(self.user_id, box_type="theme", price=BOX_INFO["theme"]["price"], theme=selected_theme)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='돌아가기', style=discord.ButtonStyle.red, emoji='🔙')
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title=MAIN_MENU["title"],
            description=MAIN_MENU["description"],
            color=MAIN_MENU["color"]
        )
        view = GachaButtonView(self.user_id)
        
        # 프리미엄 유저 확인
        has_premium = discord.utils.get(interaction.user.roles, name="LOLPARK PREMIUM")
        if has_premium:
            view.add_premium_button()
            
        await interaction.response.edit_message(embed=embed, view=view)