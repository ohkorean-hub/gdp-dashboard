import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

st.set_page_config(page_title="급량비 계산기", layout="wide")
st.title("📊 급량비 계산 프로그램")

# 파일 업로더
emp_file = st.file_uploader("직원명부.xlsx 업로드", type=['xlsx'])
data_file = st.file_uploader("지문인식.xlsx 업로드", type=['xlsx'])

if emp_file and data_file:
    # 1. 로드
    df_emp = pd.read_excel(emp_file)
    time_map = dict(zip(df_emp['이름'], df_emp['근무시간']))
    df = pd.read_excel(data_file)

    # 2. 컬럼 매핑 (사용자가 선택)
    cols = list(df.columns)
    col1, col2, col3, col4 = st.columns(4)
    map_date = col1.selectbox("발생일자 컬럼", cols)
    map_time = col2.selectbox("발생시간 컬럼", cols)
    map_name = col3.selectbox("이름 컬럼", cols)
    map_mode = col4.selectbox("모드 컬럼", cols)

    if st.button("계산 시작"):
        df = df.rename(columns={map_date: '발생일자', map_time: '발생시간', map_name: '이름', map_mode: '모드'})
        
        # 데이터 정제
        df['모드'] = df['모드'].astype(str).str.strip()
        df = df[df['이름'].isin(time_map.keys()) & df['모드'].isin(['출근', '퇴근'])].copy()

        if map_date == map_time:
            df['일시'] = pd.to_datetime(df['발생일자'])
            df['발생일자'] = df['일시'].dt.normalize()
        else:
            df['발생일자'] = pd.to_datetime(df['발생일자'])
            df['일시'] = pd.to_datetime(df['발생일자'].dt.strftime('%Y-%m-%d') + ' ' + df['발생시간'].astype(str))

        # 피벗 및 계산 (휴일 리스트 등 동일 로직)
        result = df.pivot_table(index=['이름', '발생일자'], columns='모드', values='일시', aggfunc=['min', 'max'])
        df_pivot = pd.DataFrame(index=result.index)
        df_pivot['출근_퍼스트'] = result.get(('min', '출근'), pd.NaT)
        df_pivot['퇴근_라스트'] = result.get(('max', '퇴근'), pd.NaT)
        df_pivot = df_pivot.reset_index()

        # ... (이전의 calculate_status 및 요약 로직 동일하게 삽입) ...
        # (생략: 위와 동일한 로직을 여기에 그대로 배치)
        
        st.success("계산 완료!")
        
        # 다운로드 버튼 생성
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_pivot.to_excel(writer, sheet_name='상세내역')
            # ... 요약 시트 추가 ...
        st.download_button("결과 파일 다운로드", data=output.getvalue(), file_name="급량비_결과.xlsx")