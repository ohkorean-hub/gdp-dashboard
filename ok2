import streamlit as st
import pandas as pd
from datetime import datetime

# 현재 날짜 가져오기
today = datetime.now()
start_year = today.year
start_month = today.month

def calculate_savings(start_year, start_month, balance, monthly_deposit, annual_rate, increase_amount, max_limit):
    monthly_interest_rate = annual_rate / 12
    results = []
    
    current_year = start_year
    current_month = start_month
    current_deposit = monthly_deposit
    
    for _ in range(120):
        # 매년 1월에 납입액 증액
        if current_month == 1 and not (current_year == start_year and current_month == start_month):
            current_deposit = min(current_deposit + increase_amount, max_limit)

        balance += (balance * monthly_interest_rate)
        balance += current_deposit
        
        results.append({
            "연도": current_year,
            "월": current_month,
            "납입액": current_deposit,
            "잔액": int(balance)
        })

        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
            
    return results

st.title("자산 운용 시뮬레이션")

st.sidebar.header("설정값 변경")
init_balance = st.sidebar.number_input("초기 잔액", value=45000000)
init_deposit = st.sidebar.number_input("월 납입액", value=1500000)
annual_rate = st.sidebar.slider("연 이율 (%)", 0.0, 10.0, 5.01, 0.01) / 100

increase_amount = st.sidebar.number_input("매년 증액 금액", value=100000)
max_limit = st.sidebar.number_input("월 납입 최대 한도", value=2000000)

data = calculate_savings(start_year, start_month, init_balance, init_deposit, annual_rate, increase_amount, max_limit)

# 데이터프레임 변환
df = pd.DataFrame(data)

# 천 단위 콤마 적용 (데이터프레임의 스타일 기능 활용)
st.write("시뮬레이션 결과 데이터:")
st.dataframe(
    df.style.format({
        "납입액": "{:,}",
        "잔액": "{:,}"
    })
)
