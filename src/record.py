import sqlite3
import discord

matches_db = f"/database/matches.db"

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