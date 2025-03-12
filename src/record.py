import sqlite3
import discord

matches_db = f"/database/matches.db"


# 총 게임 수 가져오기
def get_total_games():
    conn = sqlite3.connect(matches_db)
    cursor = conn.cursor()

    query = "SELECT COUNT(*) FROM GAMES;"
    cursor.execute(query)
    total_games = cursor.fetchone()[0]

    conn.close()
    return total_games


# 라인별 챔피언 승률 가져오기
def get_champions_by_lane_with_winrate(summoner_id):
    conn = sqlite3.connect(matches_db)
    cursor = conn.cursor()

    query = '''
    WITH PlayerGames AS (
        SELECT P.line, P.champion, P.team_name, G.winner_team
        FROM PICKS P
        JOIN GAMES G
        ON P.match_id = G.match_id AND P.game_index = G.game_index
        WHERE P.summoner_id = ?
    )
    SELECT 
        line,
        champion,
        COUNT(*) AS total_games,
        SUM(CASE WHEN team_name = winner_team THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN team_name != winner_team THEN 1 ELSE 0 END) AS loses,
        ROUND(
            (SUM(CASE WHEN team_name = winner_team THEN 1 ELSE 0 END) * 100.0) / 
            NULLIF(COUNT(*), 0), 
            2
        ) AS win_rate
    FROM PlayerGames
    GROUP BY line, champion
    ORDER BY 
        CASE 
            WHEN line = 'top' THEN 1
            WHEN line = 'jungle' THEN 2
            WHEN line = 'mid' THEN 3
            WHEN line = 'bot' THEN 4
            WHEN line = 'support' THEN 5
        END,
        total_games DESC;
    '''

    cursor.execute(query, (summoner_id,))
    result = cursor.fetchall()  # [(line, champion, total_games, wins, loses, win_rate), ...]

    conn.close()

    # 변환: {라인: [{champion, total_games, wins, loses, win_rate}]}
    lane_stats = {}
    for row in result:
        line, champion, total_games, wins, loses, win_rate = row
        if line not in lane_stats:
            lane_stats[line] = []
        lane_stats[line].append({
            "champion": champion,
            "total_games": total_games,
            "wins": wins,
            "loses": loses,
            "win_rate": win_rate
        })

    return lane_stats


# 채널별 승,패 승률 가져오기
def get_summoner_stats_by_channel(member: discord.member):
    
    summoner_id = member.id

    conn = sqlite3.connect(matches_db)
    cursor = conn.cursor()

    query = '''
    WITH PlayerGames AS (
        SELECT M.channel, P.team_name, G.winner_team
        FROM PICKS P
        JOIN GAMES G
        ON P.match_id = G.match_id AND P.game_index = G.game_index
        JOIN MATCHES M
        ON P.match_id = M.match_id
        WHERE P.summoner_id = ?
    )
    SELECT 
        channel,
        COUNT(*) AS total_games,
        SUM(CASE WHEN team_name = winner_team THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN team_name != winner_team THEN 1 ELSE 0 END) AS loses,
        ROUND(
            (SUM(CASE WHEN team_name = winner_team THEN 1 ELSE 0 END) * 100.0) / 
            NULLIF(COUNT(*), 0), 
            2
        ) AS win_rate
    FROM PlayerGames
    GROUP BY channel
    ORDER BY channel ASC;
    '''

    cursor.execute(query, (summoner_id,))
    result = cursor.fetchall()  # [(channel, total_games, wins, loses, win_rate), ...]

    conn.close()

    return {
        row[0]: {
            "total_games": row[1],
            "wins": row[2],
            "loses": row[3],
            "win_rate": row[4]
        }
        for row in result
    }


# 전체 게임 밴 리스트 불러오기
def get_most_banned_champions():
    conn = sqlite3.connect(matches_db)
    cursor = conn.cursor()

    query = '''
    SELECT champion, COUNT(*) AS ban_count
    FROM BANS
    GROUP BY champion
    ORDER BY ban_count DESC;
    '''

    cursor.execute(query)
    result = cursor.fetchall()  # [(champion, ban_count), ...]

    conn.close()

    return [{"champion": row[0], "ban_count": row[1]} for row in result]


# 유저별 라인별로 밴 당한 챔피언 목록

def get_banned_champions_by_position(summoner_id):
    conn = sqlite3.connect(matches_db)
    cursor = conn.cursor()

    query = '''
    WITH PlayerGames AS (
        SELECT P.match_id, P.game_index, P.line,
            CASE WHEN P.team_name = 'team_1' THEN 'team_2'
                    WHEN P.team_name = 'team_2' THEN 'team_1' 
            END AS opposite_team
        FROM PICKS P
        WHERE P.summoner_id = ?
    ),
    LaneGames AS (
        SELECT line, COUNT(DISTINCT match_id || '-' || game_index) AS total_games
        FROM PlayerGames
        GROUP BY line
    )
    -- 먼저 각 라인별 플레이한 게임 수를 출력
    SELECT 
        COALESCE(LG.line, 'top') AS position, 
        'Total Games' AS champion, 
        LG.total_games AS ban_count,
        0 AS sort_order -- "Total Games"를 항상 위에 정렬
    FROM LaneGames LG

    UNION ALL

    -- 이후 각 라인에서 반대팀이 BAN한 챔피언 목록 출력
    SELECT 
        COALESCE(PG.line, 'top') AS position, 
        B.champion, 
        COUNT(*) AS ban_count,
        1 AS sort_order -- 실제 챔피언 BAN 데이터는 아래 정렬
    FROM BANS B
    JOIN PlayerGames PG
    ON B.match_id = PG.match_id 
    AND B.game_index = PG.game_index
    AND B.team_name = PG.opposite_team
    GROUP BY PG.line, B.champion

    ORDER BY 
        1, -- position 기준 정렬 (top → jungle → mid → bot → support)
        sort_order ASC, -- "Total Games"를 항상 위로
        3 DESC; -- ban_count 기준 내림차순 정렬

    '''

    cursor.execute(query, (summoner_id,))
    result = cursor.fetchall()  # [(position, champion, ban_count), ...]

    conn.close()

    return result


# 모스트 픽 가져오기 (TOP 50)
def get_most_picked_champions():
    conn = sqlite3.connect(matches_db)
    cursor = conn.cursor()

    query = '''
    WITH TotalGames AS (
        SELECT COUNT(*) AS total_games FROM GAMES
    ),
    ChampionPicks AS (
        SELECT P.champion, COUNT(*) AS pick_count
        FROM PICKS P
        GROUP BY P.champion
    )
    SELECT 
        CP.champion, 
        CP.pick_count
    FROM ChampionPicks CP
    ORDER BY CP.pick_count DESC;
    '''

    cursor.execute(query)
    result = cursor.fetchall()

    conn.close()

    return result