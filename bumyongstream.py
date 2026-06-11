import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

st.title("📊 급량비 계산기")

# 파일 업로드
emp_file = st.file_uploader("직원명부.xlsx 업로드", type=['xlsx'])
data_file = st.file_uploader("지문인식.xlsx 업로드", type=['xlsx'])

if emp_file and data_file:
    df_emp = pd.read_excel(emp_file)
    time_map = dict(zip(df_emp['이름'], df_emp['근무시간']))
    df = pd.read_excel(data_file)

    cols = list(df.columns)
    map_date = st.selectbox("발생일자 컬럼", cols)
    map_time = st.selectbox("발생시간 컬럼", cols)
    map_name = st.selectbox("이름 컬럼", cols)
    map_mode = st.selectbox("모드 컬럼", cols)

    if st.button("계산 실행"):
        df = df.rename(columns={map_date: '발생일자', map_time: '발생시간', map_name: '이름', map_mode: '모드'})
        df['모드'] = df['모드'].astype(str).str.strip()
        
        # 날짜/시간 처리
        if map_date == map_time:
            df['일시'] = pd.to_datetime(df['발생일자'])
            df['발생일자'] = df['일시'].dt.normalize()
        else:
            df['발생일자'] = pd.to_datetime(df['발생일자'])
            df['일시'] = pd.to_datetime(df['발생일자'].dt.strftime('%Y-%m-%d') + ' ' + df['발생시간'].astype(str))

        # 피벗 생성
        result = df.pivot_table(index=['이름', '발생일자'], columns='모드', values='일시', aggfunc=['min', 'max'])
        df_pivot = pd.DataFrame(index=result.index)
        df_pivot['출근_퍼스트'] = result.get(('min', '출근'), pd.NaT)
        df_pivot['퇴근_라스트'] = result.get(('max', '퇴근'), pd.NaT)
        df_pivot = df_pivot.reset_index()

        # 급량비 계산 함수
        def calculate_status(row):
            target_hour = time_map.get(row['이름'], 9)
            c_first = pd.to_datetime(row['출근_퍼스트']).time() if pd.notna(row['출근_퍼스트']) else None
            t_last = pd.to_datetime(row['퇴근_라스트']).time() if pd.notna(row['퇴근_라스트']) else None
            # 계산 로직 (기존 코드와 동일)
            c_bin, t_bin, h_bin = 0, 0, 0
            if c_first and c_first <= datetime.time(target_hour - 1, 0, 59): c_bin = 1
            if t_last and t_last >= datetime.time(target_hour + 10, 0): t_bin = 1
            return pd.Series([c_bin, t_bin, h_bin])

        df_pivot[['출근급량비', '퇴근급량비', '휴일급량비']] = df_pivot.apply(calculate_status, axis=1)
        df_pivot['총_발생'] = df_pivot[['출근급량비', '퇴근급량비', '휴일급량비']].sum(axis=1)

        # 요약 생성
        summary = []
        for name, group in df_pivot[df_pivot['총_발생'] > 0].groupby('이름'):
            days = group['발생일자'].dt.day.astype(str).tolist()
            summary.append({'이름': name, '총건수': len(days), '지급금액': len(days)*9000, '발생일자_목록': ", ".join(days)})
        
        df_summary = pd.DataFrame(summary)

        # 결과 표시 및 다운로드
        st.write("### 상세내역", df_pivot)
        st.write("### 지급요약", df_summary)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_pivot.to_excel(writer, sheet_name='상세내역', index=False)
            df_summary.to_excel(writer, sheet_name='지급요약', index=False)
        st.download_button("엑셀 다운로드", data=output.getvalue(), file_name="급량비_결과.xlsx")