from lolpark_land.land_config import land_database_path
import sqlite3

def execute_select_query(query: str, parameter: any = None):

    conn = sqlite3.connect(land_database_path)
    cursor = conn.cursor()
    
    try:
        if parameter is not None:
            cursor.execute(query, parameter)
        else:
            cursor.execute(query)
        
        data = cursor.fetchall()

        if not data:
            return None
        
        return data
    except Exception as e:
        print(f"값 가져오는 중 오류 발생 : {e}")
    finally:
        conn.close()


def execute_post_query(query, params=None):
    """
    INSERT, UPDATE, DELETE 쿼리를 실행하는 함수
    """
    try:
        conn = sqlite3.connect(land_database_path)
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"POST 쿼리 실행 중 오류: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False