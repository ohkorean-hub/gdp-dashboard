import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

st.set_page_config(page_title="급량비 계산기", layout="wide")
st.title("급량비 계산 프로그램")

# 파일 업로더
emp_file = st.file_uploader("직원명부.xlsx 업로드", type=['xlsx'])
data_file = st.file_uploader("지문인식.xlsx 업로드", type=['xlsx'])

# 1. 파일이 모두 업로드되었는지 확인
if emp_file and data_file:
    # 데이터 로드
    df_emp = pd.read_excel(emp_file)
    df = pd.read_excel(data_file)
    
    # 컬럼 매핑 선택 UI
    cols = list(df.columns)
    col1, col2, col3, col4 = st.columns(4)
    map_date = col1.selectbox("발생일자 컬럼", cols)
    map_time = col2.selectbox("발생시간 컬럼", cols)
    map_name = col3.selectbox("이름 컬럼", cols)
    map_mode = col4.selectbox("모드 컬럼", cols)

    if st.button("계산 시작"):
        # 직원명부 필수 컬럼 확인
        if '이름' not in df_emp.columns or '근무시간' not in df_emp.columns:
            st.error("직원명부 파일에 '이름'과 '근무시간' 컬럼이 반드시 포함되어야 합니다.")
        else:
            # 매핑 및 병합
            time_map = dict(zip(df_emp['이름'], df_emp['근무시간']))
            df = df.rename(columns={map_date: '발생일자', map_time: '발생시간', map_name: '이름', map_mode: '모드'})
            
            # 데이터 정제
            df['모드'] = df['모드'].astype(str).str.strip()
            
            # 직원명부에 있는 이름만 필터링하고 근무시간 붙이기
            df = df[df['이름'].isin(time_map.keys()) & df['모드'].isin(['출근', '퇴근'])].copy()
            df['기준근무시간'] = df['이름'].map(time_map)
            
            # 결과 확인
            st.success("계산이 완료되었습니다.")
            st.write(df)
            
            # 만약 명부에 없는 사람이 있으면 경고
            unknown_names = set(df['이름'].unique()) - set(time_map.keys())
            if unknown_names:
                st.warning(f"직원명부에 없는 이름이 포함되어 있습니다: {unknown_names}")
else:
    st.info("파일을 모두 업로드하면 설정을 진행할 수 있습니다.")