# 챔피언 영 - 한
import io

import discord


lol_champion_korean_dict = {
    'aatrox': ['아트록스', '아트'],
    'ahri': ['아리'],
    'akali': ['아칼리'],
    'akshan': ['아크샨'],
    'alistar': ['알리스타', '알리'],
    'ambessa': ['암베사'],
    'amumu': ['아무무', '무무'],
    'anivia': ['애니비아'],
    'annie': ['애니'],
    'aphelios': ['아펠리오스', '아펠'],
    'ashe': ['애쉬'],
    'aurelionsol': ['아우렐리온 솔', '아우렐리온솔', '아우솔'],
    'aurora': ['오로라'],
    'azir': ['아지르'],
    'bard': ['바드'],
    'belveth': ['벨베스'],
    'blitzcrank': ['블리츠크랭크', '블리츠', '블츠', '블랭'],
    'brand': ['브랜드'],
    'braum': ['브라움'],
    'briar': ['브라이어'],
    'caitlyn': ['케이틀린', '케틀'],
    'camille': ['카밀'],
    'cassiopeia': ['카시오페아', '카시'],
    'chogath': ['초가스'],
    'corki': ['코르키', '콜키'],
    'darius': ['다리우스', '다리'],
    'diana': ['다이애나'],
    'draven': ['드레이븐', '드븐'],
    'drmundo': ['문도 박사', '문도박사', '문도', '문박'],
    'ekko': ['에코'],
    'elise': ['엘리스'],
    'evelynn': ['이블린'],
    'ezreal': ['이즈리얼', '이즈'],
    'fiddlesticks': ['피들스틱', '피들'],
    'fiora': ['피오라'],
    'fizz': ['피즈'],
    'galio': ['갈리오'],
    'gangplank': ['갱플랭크', '갱플'],
    'garen': ['가렌'],
    'gnar': ['나르'],
    'gragas': ['그라가스', '글가', '그라'],
    'graves': ['그레이브즈', '그브'],
    'gwen': ['그웬'],
    'hecarim': ['헤카림'],
    'heimerdinger': ['하이머딩거', '하딩', '딩거'],
    'hwei': ['흐웨이'],
    'illaoi': ['일라오이', '일라'],
    'irelia': ['이렐리아', '이렐'],
    'ivern': ['아이번'],
    'janna': ['잔나'],
    'jarvaniv': ['자르반 4세', '자르반4세', '자르반', '잘반'],
    'jax': ['잭스'],
    'jayce': ['제이스'],
    'jhin': ['진'],
    'jinx': ['징크스', '징키'],
    'kaisa': ['카이사'],
    'kalista': ['칼리스타'],
    'karma': ['카르마'],
    'karthus': ['카서스'],
    'kassadin': ['카사딘'],
    'katarina': ['카타리나', '카타'],
    'kayle': ['케일'],
    'kayn': ['케인'],
    'kennen': ['케넨'],
    'khazix': ['카직스'],
    'kindred': ['킨드레드', '킨드'],
    'kled': ['클레드'],
    'kogmaw': ['코그모'],
    'ksante': ['크산테', '산테'],
    'leblanc': ['르블랑'],
    'leesin': ['리신', '리 신'],
    'leona': ['레오나'],
    'lillia': ['릴리아'],
    'lissandra': ['리산드라', '리산'],
    'lucian': ['루시안'],
    'lulu': ['룰루', '루루'],
    'lux': ['럭스'],
    'malphite': ['말파이트', '말파'],
    'malzahar': ['말자하'],
    'maokai': ['마오카이', '마오', '마카오이'],
    'masteryi': ['마스터 이', '마스터이', '마이'],
    'mel': ['멜'],
    'milio': ['밀리오'],
    'missfortune': ['미스 포츈', '미스포츈', '미포'],
    'mordekaiser': ['모데카이저', '모데'],
    'morgana': ['모르가나', '몰가나', '몰가'],
    'naafiri': ['나피리'],
    'nami': ['나미'],
    'nasus': ['나서스'],
    'nautilus': ['노틸러스', '노틸'],
    'neeko': ['니코'],
    'nidalee': ['니달리'],
    'nilah': ['닐라'],
    'nocturne': ['녹턴'],
    'nunu': ['누누와 윌럼프', '누누와윌럼프', '누누', '윌럼프'],
    'olaf': ['올라프'],
    'orianna': ['오리아나', '오리'],
    'ornn': ['오른'],
    'pantheon': ['판테온', '판테'],
    'poppy': ['뽀삐', '뽀뽀', '삐뽀'],
    'pyke': ['파이크'],
    'qiyana': ['키아나'],
    'quinn': ['퀸'],
    'rakan': ['라칸'],
    'rammus': ['람머스'],
    'reksai': ['렉사이'],
    'rell': ['렐'],
    'renata': ['레나타 글라스크', '레나타글라스크', '레나타'],
    'renekton': ['레넥톤', '레넥'],
    'rengar': ['렝가'],
    'riven': ['리븐'],
    'rumble': ['럼블'],
    'ryze': ['라이즈'],
    'samira': ['사미라'],
    'sejuani': ['세주아니', '세주'],
    'senna': ['세나'],
    'seraphine': ['세라핀'],
    'sett': ['세트'],
    'shaco': ['샤코'],
    'shen': ['쉔'],
    'shyvana': ['쉬바나'],
    'singed': ['신지드'],
    'sion': ['사이온'],
    'sivir': ['시비르'],
    'skarner': ['스카너'],
    'smolder': ['스몰더'],
    'sona': ['소나'],
    'soraka': ['소라카'],
    'swain': ['스웨인'],
    'sylas': ['사일러스', '사일'],
    'syndra': ['신드라'],
    'tahmkench': ['탐 켄치', '탐켄치', '켄치'],
    'taliyah': ['탈리야', '탈랴'],
    'talon': ['탈론'],
    'taric': ['타릭'],
    'teemo': ['티모'],
    'thresh': ['쓰레쉬', '쓸쉬'],
    'tristana': ['트리스타나', '트리', '트타'],
    'trundle': ['트런들'],
    'tryndamere': ['트린다미어', '트린'],
    'twistedfate': ['트위스티드 페이트', '트위스티드페이트', '트페'],
    'twitch': ['트위치'],
    'udyr': ['우디르'],
    'urgot': ['우르곳'],
    'varus': ['바루스'],
    'vayne': ['베인'],
    'veigar': ['베이가'],
    'velkoz': ['벨코즈'],
    'vex': ['벡스'],
    'vi': ['바이'],
    'viego': ['비에고'],
    'viktor': ['빅토르'],
    'vladimir': ['블라디미르', '블라디'],
    'volibear': ['볼리베어', '볼베'],
    'warwick': ['워윅', '워웍'],
    'wukong': ['오공'],
    'xayah': ['자야'],
    'xerath': ['제라스'],
    'xinzhao': ['신 짜오', '신짜오', '짜오'],
    'yasuo': ['야스오', '야소'],
    'yone': ['요네'],
    'yorick': ['요릭'],
    'yuumi': ['유미', '윾미'],
    'zac': ['자크'],
    'zed': ['제드'],
    'zeri': ['제리'],
    'ziggs': ['직스'],
    'zilean': ['질리언'],
    'zoe': ['조이'],
    'zyra': ['자이라']
}

# display_name으로부터 `닉네임#태그` 가져오기
def get_nickname(member):
    if member is None:
        return '~~롤파크에 더 이상 존재하지 않는 소환사~~'
    return member.display_name.split('/')[0].strip()


# member로부터 `닉네임`만 가져오기
def get_nickname_without_tag(member):
    return get_nickname(member).split('#')[0].strip()


# member로부터 `티어, 점수(티어단계)` 가져오기 (영어로)
def get_tier(member):
    display_tier = member.display_name.split('/')[1].strip().lstrip('🔺🔻')
    level = display_tier[:2].upper() if display_tier.startswith('GM') or display_tier.startswith('gm') else display_tier[0].upper()
    score = int(display_tier[2:] if level == 'GM' else display_tier[1:])

    tier_fullname = {
        'C': 'challenger',
        'GM': 'grandmaster',
        'M': 'master',
        'D': 'diamond',
        'E': 'emerald',
        'P': 'platinum',
        'G': 'gold',
        'S': 'silver',
        'B': 'bronze',
        'I': 'iron',
    }
    return tier_fullname.get(level, 'unranked'), score


def get_full_champion_eng_name(champion_kor):
    for key, values in lol_champion_korean_dict.items():
        if champion_kor in values:
            return key
    return None  # 일치하는 챔피언이 없을 경우 None 반환


def get_full_champion_kor_name(champion):

    import re

    def is_english(text):
        return bool(re.fullmatch(r"[a-zA-Z\s]+", text))

    def is_korean(text):
        return bool(re.fullmatch(r"[가-힣\s]+", text))
    
    if is_english(champion):
        for key, values in lol_champion_korean_dict.items():
            if champion == key:
                return values[0]
    elif is_korean(champion):
        for key, values in lol_champion_korean_dict.items():
            if champion in values:
                return values[0]
    return None  # 일치하는 챔피언이 없을 경우 None 반환


def get_champions_per_line(line_name):
    champions_per_line = {
        'top': [
            'garen', 'gangplank', 'gragas', 'gwen', 'gnar', 'nasus', 'darius',
            'renekton', 'rengar', 'rumble', 'riven', 'maokai', 'malphite', 'mordekaiser', 
            'drmundo', 'volibear', 'poppy', 'sion', 'sylas', 'sett', 'shen', 
            'skarner', 'singed', 'akali', 'aatrox', 'ambessa', 'ornn', 'olaf',
            'wukong', 'udyr', 'urgot', 'warwick', 'yone', 'yorick', 'irelia', 
            'illaoi', 'jax', 'jayce', 'chogath', 'camille', 'cassiopeia', 'kennen', 
            'kayle', 'ksante', 'kled', 'quinn', 'tahmkench', 'tryndamere', 'teemo', 
            'fiora', 'heimerdinger'
        ],
        'jungle': [
            'gragas', 'graves', 'gwen', 'nocturne', 'nunu', 'nidalee', 'diana', 
            'rammus', 'reksai', 'rengar', 'leesin', 'lillia', 'maokai', 'masteryi', 
            'morgana', 'vi', 'belveth', 'brand', 'briar', 'viego', 
            'sejuani', 'shaco', 'shyvana', 'skarner', 'xinzhao', 'amumu', 'ivern', 
            'wukong', 'olaf', 'udyr', 'warwick', 'jarvaniv', 'zyra', 'zac', 
            'jax', 'karthus', 'khazix', 'kayn', 'kindred', 'talon', 'taliyah', 
            'pantheon', 'fiddlesticks', 'poppy', 'volibear', 'hecarim'
        ],
        'mid': [
            'galio', 'neeko', 'diana', 'ryze', 'lux', 'leblanc', 'lissandra',
            'malzahar', 'mel', 'veigar', 'velkoz', 'vex', 'vladimir', 'viktor',
            'sylas', 'swain', 'syndra', 'ahri', 'akali', 'akshan', 'azir',
            'aurelionsol', 'annie', 'anivia', 'yasuo', 'ekko', 'orianna', 'yone',
            'xerath', 'jayce', 'zoe', 'cassiopeia', 'karma', 'kassadin', 'katarina',
            'corki', 'quinn', 'qiyana', 'taliyah', 'talon', 'twistedfate', 'pantheon',
            'fizz', 'hwei'
        ],
        'bot': [
            'nilah', 'draven', 'lucian', 'missfortune', 'mel', 'varus', 'vayne', 
            'samira', 'sivir', 'smolder', 'tristana', 'twitch', 'jhin', 'jinx', 
            'kaisa', 'kalista', 'kogmaw', 'aphelios', 'ashe', 'ezreal', 'xayah', 
            'zeri', 'ziggs', 'hwei'
        ],
        'support': [
            'nami', 'nautilus', 'neeko', 'bard', 'blitzcrank', 'brand', 'braum',
            'maokai', 'morgana', 'leona', 'lulu', 'lux', 'karma', 'rakan',
            'rell', 'renata', 'senna', 'seraphine', 'soraka', 'sona', 'janna',
            'thresh', 'taric', 'tahmkench', 'pyke', 'yuumi', 'alistar', 'elise',
            'velkoz', 'xerath', 'zilean', 'zyra'
        ]
    }

    return champions_per_line[line_name]


def convert_channel_id_to_name(channel_id):
    channel_ids = {
        "A": 1287068501416218665,
        "B": 1287069336896274473,
        "C": 1290352244822114354,
        "D": 1290669974901227640,
        "E": 1294333848527831050,
        "F": 1307731155868713032,
        "FEARLESS": 1294333024753680435,
        "TIER_LIMIT": 1323988492417630250,
        "ARAM": 1323989095004897350
    }
    return next((key for key, value in channel_ids.items() if value == channel_id), None)
