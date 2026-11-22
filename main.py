import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Page configuration
st.set_page_config(
    page_title="다이아몬드 가격 예측 분석 대시보드",
    page_icon="💎",
    layout="wide"
)

plt.rcParams['axes.unicode_minus'] = False

@st.cache_data
def load_data():
    train_df = pd.read_csv('train.csv')
    test_df = pd.read_csv('test.csv')
    return train_df, test_df

@st.cache_resource
def train_and_evaluate(train_df, test_df):
    X_train = train_df.drop(columns=['log_price'])
    y_train = train_df['log_price']
    X_test = test_df.drop(columns=['log_price'])
    y_test = test_df['log_price']

    model = LinearRegression()
    model.fit(X_train, y_train)

    # Predictions (log scale)
    train_pred_log = model.predict(X_train)
    test_pred_log = model.predict(X_test)

    # Dollar scale inverse transformation
    y_test_dollar = np.exp(y_test)
    test_pred_dollar = np.exp(test_pred_log)

    metrics = {
        'train_r2_log': r2_score(y_train, train_pred_log),
        'test_r2_log': r2_score(y_test, test_pred_log),
        'train_rmse_log': np.sqrt(mean_squared_error(y_train, train_pred_log)),
        'test_rmse_log': np.sqrt(mean_squared_error(y_test, test_pred_log)),
        'test_r2_dollar': r2_score(y_test_dollar, test_pred_dollar),
        'test_rmse_dollar': np.sqrt(mean_squared_error(y_test_dollar, test_pred_dollar)),
        'test_mae_dollar': mean_absolute_error(y_test_dollar, test_pred_dollar),
        'test_mape': np.mean(np.abs((y_test_dollar - test_pred_dollar) / y_test_dollar)) * 100,
        'neg_preds': int((test_pred_dollar < 0).sum())
    }

    coef_df = pd.DataFrame({
        'Feature': X_train.columns,
        'Coefficient': model.coef_,
        'Pct_Impact(%)': (np.exp(model.coef_) - 1) * 100
    })

    return model, X_train.columns.tolist(), metrics, coef_df

# Load and train
try:
    train_df, test_df = load_data()
    model, feature_cols, metrics, coef_df = train_and_evaluate(train_df, test_df)
except FileNotFoundError:
    st.error("데이터 파일(`train.csv`, `test.csv`)을 찾을 수 없습니다. GitHub 저장소 루트 폴더에 두 파일을 함께 업로드해 주세요.")
    st.stop()

# Header
st.title("💎 다이아몬드 가격 예측 모델 & 데이터 분석 웹앱")
st.markdown(
    "원본 데이터(53,940건)의 중복·치수 오류 정제, 다중공선성 제거, 자연로그 변환, "
    "원-핫 인코딩 및 **8:2 층화 분할**을 거친 다중선형회귀 분석 대시보드입니다."
)

# Tabs (Residual Diagnostics Tab Removed)
tab1, tab2, tab3 = st.tabs([
    "🔮 실시간 가격 예측",
    "📊 모델 성능 & 상세 전처리 과정",
    "📈 회귀 계수 & 등급 프리미엄"
])

# --- TAB 1: Real-time Prediction ---
with tab1:
    st.subheader("다이아몬드 스펙을 입력해 예상 가격($)을 계산해 보세요")
    col1, col2, col3 = st.columns(3)

    with col1:
        carat = st.slider("캐럿 무게 (Carat)", min_value=0.20, max_value=5.00, value=1.00, step=0.01)
        depth = st.slider("깊이 비율 (Depth %)", min_value=43.0, max_value=79.0, value=61.8, step=0.1)
        table = st.slider("테이블 비율 (Table %)", min_value=43.0, max_value=95.0, value=57.0, step=0.5)

    with col2:
        cut = st.selectbox(
            "커팅 등급 (Cut)",
            options=['Ideal', 'Premium', 'Very Good', 'Good', 'Fair'],
            index=0,
            help="Ideal이 최상위, Fair가 기준(하위) 등급입니다."
        )
        color = st.selectbox(
            "색상 등급 (Color)",
            options=['D', 'E', 'F', 'G', 'H', 'I', 'J'],
            index=2,
            help="D(완전 무색, 최상) -> J(미세한 노란빛, 하위)"
        )

    with col3:
        clarity = st.selectbox(
            "투명도 등급 (Clarity)",
            options=['IF', 'VVS1', 'VVS2', 'VS1', 'VS2', 'SI1', 'SI2', 'I1'],
            index=3,
            help="IF(내포물 없음, 최상) -> I1(육안 식별 내포물, 하위)"
        )

    # Construct single-row feature vector matching training columns
    input_dict = {col: 0.0 for col in feature_cols}
    input_dict['log_carat'] = np.log(carat)
    input_dict['depth'] = depth
    input_dict['table'] = table

    if cut != 'Fair' and f'cut_{cut}' in input_dict:
        input_dict[f'cut_{cut}'] = 1.0
    if color != 'D' and f'color_{color}' in input_dict:
        input_dict[f'color_{color}'] = 1.0
    if clarity != 'I1' and f'clarity_{clarity}' in input_dict:
        input_dict[f'clarity_{clarity}'] = 1.0

    input_df = pd.DataFrame([input_dict])[feature_cols]
    pred_log = model.predict(input_df)[0]
    pred_dollar = np.exp(pred_log)

    # Approximate 68% (+-1 std) prediction interval in dollar terms
    std_log = metrics['test_rmse_log']
    low_dollar = np.exp(pred_log - std_log)
    high_dollar = np.exp(pred_log + std_log)

    st.divider()
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("예측 다이아몬드 가격 ($)", f"${pred_dollar:,.2f}")
    res_col2.metric("예상 적정 범위 (±1σ)", f"${low_dollar:,.0f} ~ ${high_dollar:,.0f}")
    res_col3.metric("캐럿당 단가 ($ / ct)", f"${pred_dollar / carat:,.2f}")

# --- TAB 2: Model Performance & Detailed Preprocessing ---
with tab2:
    st.subheader("1. 테스트 세트 모델 평가 지표 (10,755건 기준)")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("테스트 R² (로그 스케일)", f"{metrics['test_r2_log']:.4f}", f"훈련 R²: {metrics['train_r2_log']:.4f}")
    m2.metric("테스트 R² (달러 환산)", f"{metrics['test_r2_dollar']:.4f}")
    m3.metric("달러 기준 RMSE", f"${metrics['test_rmse_dollar']:,.2f}")
    m4.metric("달러 기준 MAE", f"${metrics['test_mae_dollar']:,.2f}")
    m5.metric("평균 백분율 오차(MAPE)", f"{metrics['test_mape']:.2f}%", f"음수 예측: {metrics['neg_preds']}건")

    st.divider()
    st.subheader("2. 단계별 데이터 정제 및 전처리 상세 과정")

    pipeline_df = pd.DataFrame({
        "단계": [
            "원본 데이터 (EDA)",
            "1단계: 완전 중복 행 제거",
            "2단계: 물리적 치수 0 제거",
            "3단계: 극단 표기 오류 제거",
            "4단계: 범주형 원-핫 인코딩",
            "5단계: 변수 선택 및 로그 변환",
            "6단계: 8:2 층화 분할"
        ],
        "세부 처리 기준 및 방법": [
            "diamonds.csv 초기 탐색 (총 10개 변수, 결측치 0건 확인)",
            "모든 열 값이 100% 일치하는 중복 레코드 146건 삭제 (keep='first')",
            "가로(x), 세로(y), 높이(z) 중 하나라도 0mm인 물리적 오류 데이터 19건 삭제",
            "현실적으로 불가능한 치수 오기입(y > 20mm 또는 z > 20mm) 3건만 선별 삭제",
            "cut, color, clarity에 원-핫 인코딩 적용 (더미 변수 함정 방지를 위해 drop_first=True로 기준 범주 각 1개 제외)",
            "carat과 높은 다중공선성을 유발하는 x, y, z 열 제외 + 곱셈적 가격 구조 선형화 및 이분산성·음수 예측 방지를 위해 carat·price에 자연로그(ln) 변환",
            "타겟(log_price)의 10개 분위수 구간(Deciles) 기준으로 훈련 80% / 테스트 20% 층화 분할 (random_state=42)"
        ],
        "변화량": [
            "—",
            "-146행",
            "-19행",
            "-3행",
            "+14열 (10열 → 24열)",
            "-3열 (24열 → 21열)",
            "8 : 2 비율 분리"
        ],
        "데이터 크기 (행 × 열)": [
            "53,940 × 10",
            "53,794 × 10",
            "53,775 × 10",
            "53,772 × 10",
            "53,772 × 24",
            "53,772 × 21",
            f"Train {len(train_df):,} × 21 / Test {len(test_df):,} × 21"
        ]
    })
    st.dataframe(pipeline_df, use_container_width=True, hide_index=True)

    st.markdown("#### 📌 핵심 전처리 의사결정 근거")
    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        with st.expander("① 왜 x, y, z(치수) 변수를 제거했나요?", expanded=True):
            st.markdown(
                "- 다이아몬드의 무게(`carat`)는 부피($x \\times y \\times z$)에 비례하므로 `carat`과 `x, y, z` 간 상관계수가 **0.95 이상**으로 매우 높습니다.\n"
                "- 이를 함께 넣으면 **다중공선성(Multicollinearity)**이 발생해 회귀 계수의 부호가 뒤집히거나 해석이 왜곡되므로 `carat`만 남기고 `x, y, z`를 제거했습니다."
            )

        with st.expander("② 왜 price와 carat에 자연로그(ln)를 적용했나요?", expanded=True):
            st.markdown(
                "- **비율(%) 기반 오차 학습:** 원본 달러로 학습하면 고가 다이아몬드 오차만 줄이려다 저가 구간에서 **음수(-) 가격**을 예측하는 문제가 발생합니다.\n"
                "- **곱셈 구조의 선형화:** 다이아몬드 등급 프리미엄은 금액 추가(+)가 아닌 비율 상승(×)으로 작동하므로, $\\ln(A \\times B) = \\ln(A) + \\ln(B)$ 성질을 이용해 선형회귀에 최적화된 구조로 변환했습니다."
            )

    with exp_col2:
        with st.expander("③ 원-핫 인코딩 기준 범주(Baseline) 구성", expanded=True):
            st.markdown(
                "최종 데이터셋(`21열 = 독립변수 20열 + 타겟 1열`)의 더미 변수 기준은 다음과 같습니다.\n"
                "- **수치형 독립변수 (3열):** `log_carat`, `depth`, `table`\n"
                "- **`cut` 더미 (4열, 기준 `Fair`):** `cut_Good`, `cut_Ideal`, `cut_Premium`, `cut_Very Good`\n"
                "- **`color` 더미 (6열, 기준 `D`):** `color_E`, `color_F`, `color_G`, `color_H`, `color_I`, `color_J`\n"
                "- **`clarity` 더미 (7열, 기준 `I1`):** `clarity_IF`, `clarity_SI1`, `clarity_SI2`, `clarity_VS1`, `clarity_VS2`, `clarity_VVS1`, `clarity_VVS2`\n"
                "- **타겟 변수 (1열):** `log_price` (예측 시 `np.exp()`로 달러 복원)"
            )

        with st.expander("④ 왜 8:2 층화 분할(Stratified Split)을 사용했나요?", expanded=True):
            st.markdown(
                "- 고가·대형 다이아몬드는 전체 데이터에서 차지하는 비중이 작아 단순 무작위 분할 시 훈련/테스트 세트 간 분포 차이가 생길 수 있습니다.\n"
                "- `log_price`를 10개 분위수로 나누어 층화 추출한 결과, 두 세트의 평균 가격이 **$3,929.77 vs $3,936.62**로 거의 동일하게 배분되었습니다."
            )

# --- TAB 3: Regression Coefficients ---
with tab3:
    st.subheader("회귀 계수 및 기준 등급 대비 가격 변화율(%)")
    st.info(
        f"**절편(Intercept):** `{model.intercept_:.4f}` | "
        f"**`log_carat` 계수:** `+{coef_df.loc[coef_df['Feature']=='log_carat', 'Coefficient'].values[0]:.4f}` "
        "(캐럿 1% 증가 시 가격 약 **1.88%** 상승, 무게 2배 시 가격 약 **3.69배** 상승)"
    )

    c_left, c_right = st.columns([1.2, 1])

    with c_left:
        cat_coefs = coef_df[coef_df['Feature'].str.startswith(('cut_', 'color_', 'clarity_'))].copy()
        fig_coef, ax = plt.subplots(figsize=(8, 6))
        colors = ['#2ca02c' if val > 0 else '#d62728' for val in cat_coefs['Pct_Impact(%)']]
        ax.barh(cat_coefs['Feature'], cat_coefs['Pct_Impact(%)'], color=colors, alpha=0.85)
        ax.axvline(0, color='black', linewidth=1)
        ax.set_xlabel('Price Change vs. Baseline Category (%)')
        ax.set_title('Premium / Discount by Grade (Baseline: Fair, D, I1)')
        ax.grid(axis='x', linestyle=':', alpha=0.6)
        plt.tight_layout()
        st.pyplot(fig_coef)

    with c_right:
        st.dataframe(
            coef_df.style.format({'Coefficient': '{:.4f}', 'Pct_Impact(%)': '{:+.2f}%'}),
            use_container_width=True,
            height=460,
            hide_index=True
        )
