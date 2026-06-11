import streamlit as st
import pandas as pd

st.set_page_config(page_title="급량비 계산기", layout="wide")
st.title("급량비 계산 프로그램")

# 파일 업로더
emp_file = st.file_uploader("직원명부.xlsx 업로드", type=['xlsx'])
data_file = st.file_uploader("지문인식.xlsx 업로드", type=['xlsx'])

if emp_file and data_file:
    # 엑셀 파일 읽기 (헤더가 첫 번째 줄에 있다고 가정)
    df_emp = pd.read_excel(emp_file)
    df = pd.read_excel(data_file)
    
    # 엑셀의 컬럼명을 리스트로 가져오기
    cols = df.columns.tolist()
    
    # 사용자로부터 매핑할 컬럼 선택
    col1, col2, col3, col4 = st.columns(4)
    map_date = col1.selectbox("발생일자 컬럼 선택", cols)
    map_time = col2.selectbox("발생시간 컬럼 선택", cols)
    map_name = col3.selectbox("이름 컬럼 선택", cols)
    map_mode = col4.selectbox("모드 컬럼 선택", cols)

    if st.button("계산 시작"):
        # 필수 데이터 확인
        if '이름' not in df_emp.columns or '근무시간' not in df_emp.columns:
            st.error("직원명부 파일에 '이름'과 '근무시간' 컬럼이 정확히 있는지 확인해주세요.")
        else:
            # 명부를 딕셔너리로 변환 (이름: 근무시간)
            time_map = dict(zip(df_emp['이름'], df_emp['근무시간']))
            
            # 선택한 컬럼을 공통된 이름으로 변경
            df_processed = df.rename(columns={
                map_date: '발생일자', 
                map_time: '발생시간', 
                map_name: '이름', 
                map_mode: '모드'
            })
            
            # 데이터 정제 (모드 컬럼 공백 제거)
            df_processed['모드'] = df_processed['모드'].astype(str).str.strip()
            
            # 직원명부에 있는 이름만 필터링하고 '출근' 또는 '퇴근' 데이터만 추출
            df_result = df_processed[
                df_processed['이름'].isin(time_map.keys()) & 
                df_processed['모드'].isin(['출근', '퇴근'])
            ].copy()
            
            # 근무시간 매핑
            df_result['기준근무시간'] = df_result['이름'].map(time_map)
            
            st.success("계산이 완료되었습니다.")
            st.dataframe(df_result)
            
            # 결과물 다운로드 버튼 (필요한 경우)
            csv = df_result.to_csv(index=False).encode('utf-8-sig')
            st.download_button("결과 파일 다운로드(CSV)", csv, "result.csv", "text/csv")
else:
    st.info("파일 두 개를 모두 업로드하면 설정을 진행할 수 있습니다.")