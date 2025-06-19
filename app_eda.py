import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Population Trends 데이터셋**  
                - 제공처: [통계청](https://kosis.kr)  
                - 설명: 2008년부터 2023년까지 대한민국의 행정구역별 인구, 출생아 수, 사망자 수 통계를 수록한 데이터  
                - 주요 변수:  
                - `지역`: 시도 및 세부 지역명  
                - `시점`: 연도 (2008 ~ 2023)  
                - `인구`: 해당 연도의 전체 인구 수  
                - `출생아수(명)`: 출생한 신생아 수  
                - `사망자수(명)`: 사망자 수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (population trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)

         # 1. '세종' 지역의 '-' 값을 0으로 치환
        sejong_mask = df['지역'].str.contains('세종', na=False)
        df.loc[sejong_mask] = df.loc[sejong_mask].replace('-', 0)

        # 2. 숫자 변환
        cols = ['인구', '출생아수(명)', '사망자수(명)']
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 3. 데이터프레임 구조 출력 (df.info())
        st.subheader("📋 데이터프레임 구조 (`df.info()`)")
        buffer = io.StringIO()
        df.info(buf=buffer)
        st.text(buffer.getvalue())

        # 4. 요약 통계 (df.describe())
        st.subheader("📊 요약 통계량 (`df.describe()`)")
        st.dataframe(df.describe())

        tabs = st.tabs([
            "1. 기초 통계",
            "2. 연도별 추이",
            "3. 지역별 분석",
            "4. 변화량 분석",
            "5. 시각화"
        ])

    with tabs[0]:
        st.header("🔍 기초 통계")
        st.markdown(f"""
        - **population_trends.csv**: 2008–2023년까지 대한민국 지역별 인구 통계 기록
        - 총 관측치: {df.shape[0]}개
        - 주요 변수:
        - **시점**: 연도 (2008 ~ 2023)
        - **지역**: 시도 및 세부 지역 이름
        - **인구**: 전체 인구 수
        - **출생아수(명)**: 해당 연도의 출생자 수
        - **사망자수(명)**: 해당 연도의 사망자 수
        """)

        st.subheader("1) 데이터 구조 (`df.info()`)")
        buffer = io.StringIO()
        df.info(buf=buffer)
        st.text(buffer.getvalue())

        st.subheader("2) 기초 통계량 (`df.describe()`)")
        st.dataframe(numeric_df.describe())

        st.subheader("3) 샘플 데이터 (첫 5행)")
        st.dataframe(df.head())

    with tabs[1]:
        st.header("🕒 연도별 전체 인구 추이 분석")
        nationwide = df[df['지역'].str.contains('전국', na=False)].copy()
        nationwide = nationwide.sort_values('시점') # Use '시점' as the year column

        years = nationwide['시점'].astype(int).tolist()
        population = nationwide['인구'].astype(float).tolist()
        births = nationwide['출생아수(명)'].astype(float).tolist()
        deaths = nationwide['사망자수(명)'].astype(float).tolist()

        # 최근 3년 평균 자연 증가량 계산 (assuming '시점' is sorted)
        recent = nationwide.tail(3)
        avg_growth = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()

        last_year = years[-1]
        target_year = 2035
        # Use the last actual population for prediction base
        predicted_population = population[-1] + avg_growth * (target_year - last_year)

        years_extended = years + [target_year]
        population_extended = population + [predicted_population]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(years, population, marker='o', label="Observed Population")
        ax.plot([target_year], [predicted_population], 'ro', label=f"Projected {target_year} Population")
        ax.plot(years_extended, population_extended, linestyle='--', color='gray', alpha=0.7, label="Projection Line")
        ax.set_title("National Population Trend and 2035 Projection")
        ax.set_xlabel("Year")
        ax.set_ylabel("Population")
        ax.ticklabel_format(style='plain', axis='y') # Prevent scientific notation
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
        st.markdown(f"**Projected population in {target_year}: {int(predicted_population):,}**")

        st.subheader("Natural Increase/Decrease Trend")
        fig_nat, ax_nat = plt.subplots(figsize=(10, 6))
        ax_nat.plot(years, [b - d for b, d in zip(births, deaths)], marker='x', color='green', label="Natural Increase (Births - Deaths)")
        ax_nat.axhline(0, color='red', linestyle='--', linewidth=0.7)
        ax_nat.set_title("National Natural Increase/Decrease Trend")
        ax_nat.set_xlabel("Year")
        ax_nat.set_ylabel("Natural Change (Births - Deaths)")
        ax_nat.ticklabel_format(style='plain', axis='y')
        ax_nat.legend()
        ax_nat.grid(True)
        st.pyplot(fig_nat)
        st.markdown("""
        - The natural increase/decrease is calculated as the number of births minus the number of deaths.
        - A positive value indicates population growth due to natural factors, while a negative value indicates a decline.
        """)

    with tabs[2]:
        st.header("🗺️ 지역별 인구 변화량 순위 분석")
        region_map = {
            '서울특별시': 'Seoul', '부산광역시': 'Busan', '대구광역시': 'Daegu', '인천광역시': 'Incheon',
            '광주광역시': 'Gwangju', '대전광역시': 'Daejeon', '울산광역시': 'Ulsan', '세종특별자치시': 'Sejong',
            '경기도': 'Gyeonggi', '강원도': 'Gangwon', '충청북도': 'Chungbuk', '충청남도': 'Chungnam',
            '전라북도': 'Jeonbuk', '전라남도': 'Jeonnam', '경상북도': 'Gyeongbuk', '경상남도': 'Gyeongnam',
            '제주특별자치도': 'Jeju'
        }

        df_local = df[~df['지역'].str.contains('전국', na=False)].copy()
        latest_year = df_local['시점'].astype(int).max()
        recent_years = list(range(latest_year - 4, latest_year + 1))
        df_recent = df_local[df_local['시점'].astype(int).isin(recent_years)]

        pop_change = df_recent.groupby('지역').agg(
            pop_old=('인구', lambda x: x.iloc[0]), # Population at the start of the 5-year period
            pop_new=('인구', lambda x: x.iloc[-1]) # Population at the end of the 5-year period
        )
        pop_change['change'] = (pop_change['pop_new'] - pop_change['pop_old']) / 1000  # in thousands
        # Avoid division by zero for rate calculation if pop_old is 0
        pop_change['rate'] = pop_change.apply(lambda row: ((row['pop_new'] - row['pop_old']) / row['pop_old']) * 100 if row['pop_old'] != 0 else 0, axis=1)

        pop_change['region_en'] = pop_change.index.map(region_map)

        pop_change_sorted = pop_change.sort_values('change', ascending=False)

        st.subheader("Population Change (in thousands) over the last 5 years")
        fig1, ax1 = plt.subplots(figsize=(10, 8))
        sns.barplot(data=pop_change_sorted, y='region_en', x='change', ax=ax1, palette='coolwarm')
        ax1.set_title("Population Change by Region")
        ax1.set_xlabel("Change (thousands)")
        ax1.set_ylabel("Region")
        for i, v in enumerate(pop_change_sorted['change']):
            ax1.text(v + (pop_change_sorted['change'].abs().max() * 0.02 * (1 if v >=0 else -1)), i, f"{v:.1f}", va='center', ha='left' if v >= 0 else 'right')
        st.pyplot(fig1)

        st.markdown("""
        - The chart above shows the **absolute population change** over the past 5 years in each region.
        - Regions like Gyeonggi and Sejong have seen significant growth, while some traditional provinces show decline.
        """)

        pop_change_sorted_rate = pop_change.sort_values('rate', ascending=False)
        st.subheader("Population Growth Rate (%) over the last 5 years")
        fig2, ax2 = plt.subplots(figsize=(10, 8))
        sns.barplot(data=pop_change_sorted_rate, y='region_en', x='rate', ax=ax2, palette='viridis')
        ax2.set_title("Population Growth Rate by Region")
        ax2.set_xlabel("Growth Rate (%)")
        ax2.set_ylabel("Region")
        for i, v in enumerate(pop_change_sorted_rate['rate']):
            ax2.text(v + (pop_change_sorted_rate['rate'].abs().max() * 0.02 * (1 if v >=0 else -1)), i, f"{v:.1f}%", va='center', ha='left' if v >= 0 else 'right')
        st.pyplot(fig2)

        st.markdown("""
        - This chart illustrates the **percentage growth rate**.
        - Sejong consistently shows the highest population growth rate, largely due to its development as a new administrative city.
        - Many rural regions exhibit negative growth rates, indicating ongoing population shrinkage.
        """)

    with tabs[3]:
        st.header("🧮 증감률 상위 지역 및 연도 도출")

        df_local = df[~df['지역'].str.contains('전국', na=False)].copy()
        df_local = df_local.sort_values(['지역', '시점'])

        # Calculate difference based on '인구'
        df_local['증감'] = df_local.groupby('지역')['인구'].diff().fillna(0)

        # Sort by absolute change and get top 100
        top_diff = df_local.reindex(df_local['증감'].abs().sort_values(ascending=False).index).head(100)

        # Format numbers for display
        top_diff['인구'] = top_diff['인구'].astype(int).apply(lambda x: f"{x:,}")
        top_diff['증감'] = top_diff['증감'].astype(int)

        def highlight_diff(val):
            color = ''
            if isinstance(val, (int, float)): # Ensure val is numeric before comparison
                if val > 0:
                    color = f'background-color: rgba(0, 120, 255, {min(abs(val) / 50000, 1):.2f}); color: white;'
                elif val < 0:
                    color = f'background-color: rgba(255, 60, 60, {min(abs(val) / 50000, 1):.2f}); color: white;'
            return color

        styled_df = top_diff[['지역', '시점', '인구', '증감']].style \
            .applymap(highlight_diff, subset=['증감']) \
            .format({'증감': "{:,}"})

        st.dataframe(styled_df, use_container_width=True)

        st.markdown("""
        > **설명**
        > - `증감` 컬럼은 전년도 대비 인구 수 차이를 나타냄
        > - 증가한 경우는 파란색, 감소한 경우는 빨간색으로 강조
        > - 가장 큰 변화가 있었던 지역/연도 Top 100 사례만 표시
        """)

    with tabs[4]:
        st.header("🔗 히트맵 또는 막대그래프 시각화")
        region_map = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
            '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
            '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
            '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
            '제주': 'Jeju'
        }

        df_local = df[~df['지역'].str.contains('전국', na=False)].copy()

        # Map Korean region names to English for better plot labels
        # Use .apply() with a lambda for more robust mapping to catch partial matches
        df_local['region_en'] = df_local['지역'].apply(lambda x: next((eng for kor, eng in region_map.items() if kor in x), x))

        pivot_df = df_local.pivot_table(index='시점', columns='region_en', values='인구', aggfunc='sum')

        fig_area, ax_area = plt.subplots(figsize=(12, 6))
        pivot_df.plot.area(ax=ax_area, cmap='tab20')
        ax_area.set_title("Population Trends by Region (2008–2023)", fontsize=14)
        ax_area.set_xlabel("Year")
        ax_area.set_ylabel("Population")
        ax_area.ticklabel_format(style='plain', axis='y') # Prevent scientific notation
        ax_area.legend(loc='center left', bbox_to_anchor=(1, 0.5), title="Region")
        ax_area.grid(True)
        plt.tight_layout() # Adjust layout to prevent labels from overlapping
        st.pyplot(fig_area)

        st.markdown("""
        > **설명**
        > - 연도별로 전체 인구를 지역별로 나누어 누적 영역 그래프로 표현하였습니다.
        > - 각 색상은 하나의 지역을 나타내며, 전체 높이는 총합 인구를 의미합니다.
        > - 오른쪽 범례를 통해 지역 이름(영문 표기)을 확인할 수 있습니다.
        """)

    


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()