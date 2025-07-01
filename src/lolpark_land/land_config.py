import os

# 데이터베이스 파일
land_database_path = "C:/Users/Desktop/lolpark_githubs/lolpark_land.db" if os.path.exists("C:/Users/Desktop/lolpark_githubs/lolpark_land.db") else f"/database/lolpark_land.db"

####### 랜드 채널 ######

# 출석체크
ATTENDANCE_CHANNEL_ID = 1388892958337667203 