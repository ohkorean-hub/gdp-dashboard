import streamlit as st

def calculate_savings(start_year, start_month, balance, monthly_deposit, annual_rate):
    monthly_interest_rate = annual_rate / 12
    results = []
    
    current_year = start_year
    current_month = start_month
    current_deposit = monthly_deposit
    
    for _ in range(120):
        if current_month == 1 and current_year > start_year:
            current_deposit = min(current_deposit + 100000, 2000000)

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

data = calculate_savings(2026, 6, init_balance, init_deposit, annual_rate)

st.table(data)