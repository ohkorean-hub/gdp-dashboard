import streamlit as st
import pandas as pd
import datetime
import io
from openpyxl.styles import Alignment

# 스트림릿 페이지 설정
st.set_page_config(page_title="급량비 계산기", layout="wide")
st.title("🍚 지문인식 기반 급량비 계산 시스템")

# 휴일 목록 설정 (2026년)
holiday_list = [
    '2026-01-01', '2026-02-16', '2026-02-17', '2026-02-18', '2026-03-01', '2026-03-02', 
    '2026-05-01', '2026-05-05', '2026-05-24', '2026-05-25', '2026-06-03', '2026-06-06', 
    '2026-07-17', '2026-08-15', '2026-08-17', '2026-09-24', '2026-09-25', '2026-09-26', 
    '2026-10-03', '2026-10-05', '2026-10-09', '2026-12-25'
]

def is_holiday(date_obj):
    return (date_obj.weekday() >= 5) or (date_obj.strftime('%Y-%m-%d') in holiday_list)

# 1. 파일 업로드 및 옵션 설정 섹션
st.subheader("1. 파일 업로드 및 환경 설정")
col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([2, 2, 1.5, 1.5, 1.5])

with col_f1:
    emp_file = st.file_uploader("직원명부.xlsx 파일을 업로드하세요", type=["xlsx"])
with col_f2:
    raw_file = st.file_uploader("지문인식.xlsx 파일을 업로드하세요", type=["xlsx"])
with col_f3:
    # 하루 인정 기준 선택 (기본값: 하루 최대 2개 인정)
    day_limit_mode = st.selectbox(
        "하루 인정 기준 설정",
        ["하루 최대 2개 인정 (출/퇴근 각각)", "하루 최대 1개만 인정"],
        index=0,
        help="하루에 출근/퇴근 급량비가 모두 발생했을 때의 인정 기준입니다."
    )
with col_f4:
    # 급량비 인정 시간 기준 선택 (기본값 2시간)
    # 기존 코드의 1시간 전/후 로직을 1시간, 2시간, 3시간으로 유연하게 선택하도록 구성
    time_threshold = st.selectbox(
        "급량비 시간 기준 설정",
        ["1시간 기준", "2시간 기준", "3시간 기준"],
        index=1,
        help="출근 시 근무시간 N시간 전 출근, 퇴근 시 근무시간 9시간 + N시간 후 퇴근 기준을 적용합니다."
    )
    # 문자열에서 숫자만 추출 (예: "2시간 기준" -> 2)
    threshold_hours = int(time_threshold.split("시간")[0])

with col_f5:
    # 급량비 총 제한 개수 설정 (기본값 20개)
    max_limit = st.number_input("인당 월 최대 인정 개수 제한", min_value=1, max_value=62, value=20, step=1, help="지급 가능한 월 최대 급량비 횟수를 제한합니다.")

# 두 파일이 모두 업로드되었을 때 실행
if emp_file and raw_file:
    try:
        # 데이터 로드
        df_emp = pd.read_excel(emp_file)
        time_map = dict(zip(df_emp['이름'], df_emp['근무시간']))
        df = pd.read_excel(raw_file, sheet_name='Sheet1')
        
        # 2. 컬럼 선택 (스트림릿 Selectbox 활용)
        st.subheader("2. 데이터 컬럼 매핑")
        cols = list(df.columns)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: map_date = st.selectbox("'발생일자' 컬럼 선택", cols, index=0 if len(cols)>0 else 0)
        with c2: map_time = st.selectbox("'발생시간' 컬럼 선택", cols, index=1 if len(cols)>1 else 0)
        with c3: map_name = st.selectbox("'이름' 컬럼 선택", cols, index=2 if len(cols)>2 else 0)
        with c4: map_mode = st.selectbox("'모드' 컬럼 선택", cols, index=3 if len(cols)>3 else 0)
        
        # 분석 시작 버튼
        if st.button("급량비 계산 시작🚀", type="primary"):
            
            # 컬럼명 변경 및 정제
            df = df.rename(columns={map_date: '발생일자', map_time: '발생시간', map_name: '이름', map_mode: '모드'})
            df['모드'] = df['모드'].astype(str).str.strip()
            df = df[df['이름'].isin(time_map.keys()) & df['모드'].isin(['출근', '퇴근'])].copy()
            
            # 날짜/시간 결합 로직
            if map_date == map_time:
                df['일시'] = pd.to_datetime(df['발생일자'])
                df['발생일자'] = df['일시'].dt.normalize()
            else:
                df['발생일자'] = pd.to_datetime(df['발생일자'])
                df['일시'] = pd.to_datetime(df['발생일자'].dt.strftime('%Y-%m-%d') + ' ' + df['발생시간'].astype(str))
            
            # 피벗 및 로직 계산
            result = df.pivot_table(index=['이름', '발생일자'], columns='모드', values='일시', aggfunc=['min', 'max'])
            df_pivot = pd.DataFrame(index=result.index)
            df_pivot['출근_퍼스트'] = result.get(('min', '출근'), pd.NaT)
            df_pivot['퇴근_라스트'] = result.get(('max', '퇴근'), pd.NaT)
            df_pivot = df_pivot.reset_index()
            
            def calculate_status(row):
                name = row['이름']
                date = pd.to_datetime(row['발생일자'])
                target_hour = time_map.get(name, 9)
                c_first = pd.to_datetime(row['출근_퍼스트']).time()
