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
col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 1.5, 1.5])

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
                c_first = pd.to_datetime(row['출근_퍼스트']).time() if pd.notna(row['출근_퍼스트']) else None
                t_last = pd.to_datetime(row['퇴근_라스트']).time() if pd.notna(row['퇴근_라스트']) else None
                출근급량비, 퇴근급량비, 휴일급량비 = 0, 0, 0
                
                if is_holiday(date):
                    if c_first and t_last:
                        diff = (datetime.datetime.combine(date, t_last) - datetime.datetime.combine(date, c_first)).total_seconds() / 3600
                        if 1 <= diff < 9: 휴일급량비 = 1
                else:
                    if c_first and c_first <= datetime.time(target_hour - 1, 0, 59): 출근급량비 = 1
                    if t_last and t_last >= datetime.time(target_hour + 10, 0): 퇴근급량비 = 1
                return pd.Series([출근급량비, 퇴근급량비, 휴일급량비])
            
            df_pivot[['출근급량비', '퇴근급량비', '휴일급량비']] = df_pivot.apply(calculate_status, axis=1)
            
            # 하루 인정 기준 옵션 반영
            if day_limit_mode == "하루 최대 1개만 인정":
                # 출근, 퇴근, 휴일 중 하나라도 있으면 하루 발생량을 최대 1로 제한
                df_pivot['총_발생'] = df_pivot[['출근급량비', '퇴근급량비', '휴일급량비']].sum(axis=1).clip(upper=1)
            else:
                # 기본값: 각각 더해서 하루 최대 2개까지 인정 가능
                df_pivot['총_발생'] = df_pivot[['출근급량비', '퇴근급량비', '휴일급량비']].sum(axis=1)
            
            # 요약 데이터 생성 (월간 최대 제한 및 날짜 중복 표시 반영)
            summary_data = []
            for n, g in df_pivot[df_pivot['총_발생'] > 0].groupby('이름'):
                
                # 각 날짜별로 발생한 건수만큼 날짜(일)를 리스트에 추가 (하루 2개면 요약본에 두 번 등장)
                date_list = []
                for _, row in g.iterrows():
                    count = int(row['총_발생'])
                    day_str = str(pd.to_datetime(row['발생일자']).day)
                    date_list.extend([day_str] * count)
                
                actual_count = len(date_list)  # 실제 매칭된 총 건수
                allowed_count = min(actual_count, max_limit)  # 월 마지노선 제한 적용
                
                # 월 제한에 걸린 경우, 날짜 목록도 제한된 개수만큼만 잘라서 표시
                final_date_list = date_list[:allowed_count]
                
                summary_data.append({
                    '이름': n,
                    '실제건수': actual_count,
                    '인정건수': allowed_count,
                    '지급금액': allowed_count * 9000,
                    '발생일자_목록': ", ".join(final_date_list)
                })
            df_summary = pd.DataFrame(summary_data)
            
            # 화면에 결과 미리보기 보여주기
            st.subheader("📋 계산 결과 미리보기")
            tab1, tab2 = st.tabs(["지급 요약", "상세 내역"])
            with tab1:
                if not df_summary.empty:
                    st.dataframe(df_summary, use_container_width=True)
                else:
                    st.info("급량비 발생 내역이 없습니다.")
            with tab2:
                df_display = df_pivot.copy()
                df_display['발생일자'] = df_display['발생일자'].dt.strftime('%Y-%m-%d')
                st.dataframe(df_display, use_container_width=True)
                
            # openpyxl 서식 적용 및 메모리 버퍼 저장 (스트림릿 다운로드용)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_pivot.to_excel(writer, sheet_name='상세내역', index=False)
                df_summary.to_excel(writer, sheet_name='지급요약', index=False)
                wb = writer.book
                for sheet in [wb['상세내역'], wb['지급요약']]:
                    for row in sheet.iter_rows():
                        for cell in row: 
                            cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # 다운로드 버튼 생성
            st.success(f"급량비 계산 완료! ({day_limit_mode} / 인당 월 최대: {max_limit}개 적용)")
            st.download_button(
                label="📥 엑셀 파일 다운로드 (.xlsx)",
                data=buffer.getvalue(),
                file_name="급량비_결과.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
else:
    st.info("💡 두 개의 엑셀 파일(직원명부, 지문인식)을 모두 업로드하면 컬럼 선택 창이 나타납니다.")
