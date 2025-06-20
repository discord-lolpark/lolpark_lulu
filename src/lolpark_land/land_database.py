from lolpark_land.land_config import land_database_path
import sqlite3
import traceback

def execute_select_query(query: str, parameter: any = None):
    conn = sqlite3.connect(land_database_path)
    cursor = conn.cursor()
    
    try:
        if parameter is not None:
            cursor.execute(query, parameter)
        else:
            cursor.execute(query)
        
        data = cursor.fetchall()
        return data if data else None  # 빈 리스트도 None으로 처리하지 않게 수정
        
    except Exception as e:
        print(f"값 가져오는 중 오류 발생 : {e}")
        print(f"쿼리: {query}")
        print(f"파라미터: {parameter}")
        print("스택 트레이스:")
        traceback.print_exc()
        return None  # 예외 발생시 None 반환
    finally:
        conn.close()


def execute_post_query(query, params=None):
    """
    INSERT, UPDATE, DELETE 쿼리를 실행하는 함수
    """
    conn = None  # 초기화
    try:
        conn = sqlite3.connect(land_database_path)
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        conn.commit()
        return True
        
    except Exception as e:
        print(f"POST 쿼리 실행 중 오류: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def get_now_lolpark_coin(user_id):
    query = "SELECT lolpark_coin FROM users WHERE user_id = ?"
    
    try:
        result = execute_select_query(query, (user_id,))  # 튜플로 전달
        
        if result and len(result) > 0:
            return result[0][0]
        else:
            print(f"[WARNING] 사용자 {user_id}의 코인 정보를 찾을 수 없습니다.")
            return 0
    except Exception as e:
        print(f"[ERROR] get_now_lolpark_coin 오류: {e}")
        return 0