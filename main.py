import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# 페이지 기본 설정
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

    # 로그 스케일 예측
    train_pred_log = model.predict(X_train)
    test_pred_log = model.predict(X_test)

    # 달러($) 단위로 역변환 (지수함수)
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

    eval_data = {
        'y_test_log': y_test,
        'y_pred_log': test_pred_log,
        'residuals_log': y_test - test_pred_log,
        'y_actual_dollar': y_test_dollar,
        'y_pred_dollar': test_pred_dollar
    }

    return model, X_train.columns.tolist(), metrics, coef_df, eval_data

# 데이터 로드 및 모델 학습
try:
    train_df, test_df = load_data()
    model, feature_cols, metrics, coef_df, eval_data = train_and_evaluate(train_df, test_df)
except FileNotFoundError:
    st.error("데이터 파일(`train.csv`, `test.csv`)을 찾을 수 없습니다. GitHub 저장소 루트 폴더에 두 파일을 함께 업로드해 주세요.")
    st.stop()

# 상단 타이틀
st.title("💎 다이아몬드 가격 예측 모델 & 데이터 분석 웹앱")
st.markdown(
    "데이터 정제(53,772건), 다중공선성 제거(`x, y, z` 제외), 로그 변환(`log_carat`, `log_price`), "
    "원-핫 인코딩 및 **8:2 층화 분할**을 거친 다중선형회귀 분석 결과입니다."
)

# 4개 탭 구성
tab1, tab2, tab3, tab4 = st.tabs([
    "🔮 실시간 가격 예측",
    "📊 모델 성능 & 데이터 요약",
    "📈 회귀 계수 & 등급 프리미엄",
    "🔍 잔차 분석(시각화)"
])

# --- TAB 1: 실시간 가격 예측 ---
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

    # 학습 데이터와 동일한 열 순서로 입력 벡터 생성
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

    # ±1 표준편차(약 68% 신뢰구간) 예측 범위 계산
    std_log = metrics['test_rmse_log']
    low_dollar = np.exp(pred_log - std_log)
    high_dollar = np.exp(pred_log + std_log)

    st.divider()
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("예측 다이아몬드 가격 ($)", f"${pred_dollar:,.2f}")
    res_col2.metric("예상 적정 범위 (±1σ)", f"${low_dollar:,.0f} ~ ${high_dollar:,.0f}")
    res_col3.metric("캐럿당 단가 ($ / ct)", f"${pred_dollar / carat:,.2f}")

# --- TAB 2: 모델 성능 & 데이터 요약 ---
with tab2:
    st.subheader("1. 테스트 세트 평가 지표 (10,755건 기준)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("테스트 R² (로그 스케일)", f"{metrics['test_r2_log']:.4f}", f"훈련 R²: {metrics['train_r2_log']:.4f}")
    m2.metric("테스트 R² (달러 환산)", f"{metrics['test_r2_dollar']:.4f}")
    m3.metric("달러 기준 RMSE", f"${metrics['test_rmse_dollar']:,.2f}")
    m4.metric("달러 기준 MAE / MAPE", f"${metrics['test_mae_dollar']:,.2f}", f"오차율 {metrics['test_mape']:.2f}%")

    st.divider()
    st.subheader("2. 데이터 전처리 및 분할 파이프라인 요약")
    pipeline_df = pd.DataFrame({
        "단계": ["원본 데이터", "1단계: 중복 제거", "2단계: 치수 0 제거", "3단계: 극단 오기입 제거", "4단계: 최종 전처리", "5단계: 8:2 층화 분할"],
        "처리 내용": [
            "초기 EDA 수행 (결측치 0건 확인)",
            "완전 중복 146건 제거",
            "x, y, z 중 0이 포함된 19건 제거",
            "y > 20 또는 z > 20 극단 표기 3건 제거",
            "x,y,z 제외 + log(carat), log(price) 변환 + 원-핫 인코딩",
            "log_price 10분위수 기준 Train 80% / Test 20% 분할"
        ],
        "데이터 크기": [
            "53,940행 × 10열",
            "53,794행 × 10열",
            "53,775행 × 10열",
            "53,772행 × 10열",
            "53,772행 × 21열",
            f"Train {len(train_df):,}행 / Test {len(test_df):,}행"
        ]
    })
    st.dataframe(pipeline_df, use_container_width=True, hide_index=True)

# --- TAB 3: 회귀 계수 & 등급 프리미엄 ---
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

# --- TAB 4: 잔차 분석(시각화) ---
with tab4:
    st.subheader("테스트 세트 잔차(Residual) 진단 시각화")
    res_log = eval_data['residuals_log']
    pred_log = eval_data['y_pred_log']
    act_dollar = eval_data['y_actual_dollar']
    pred_dollar = eval_data['y_pred_dollar']

    r1, r2, r3 = st.columns(3)
    r1.metric("로그 잔차 평균", f"{res_log.mean():.6f}", "0에 수렴 (편향 없음)")
    r2.metric("로그 잔차 표준편차", f"{res_log.std():.4f}")
    r3.metric("±2σ 이내 비율", f"{(np.abs(res_log) <= 2 * res_log.std()).mean() * 100:.2f}%")

    fig_res, axes = plt.subplots(2, 2, figsize=(13, 10))
    plt.subplots_adjust(hspace=0.32, wspace=0.25)

    # 1. 예측값 vs 잔차
    ax1 = axes[0, 0]
    ax1.scatter(pred_log, res_log, alpha=0.15, s=8, color='#2b5c8f', edgecolors='none')
    ax1.axhline(0, color='#d62728', linestyle='--', linewidth=1.5, label='Zero Residual (y = 0)')
    bins = pd.qcut(pred_log, q=20, duplicates='drop')
    trend = pd.DataFrame({'pred': pred_log, 'res': res_log, 'bin': bins}).groupby('bin', observed=False)[['pred', 'res']].mean()
    ax1.plot(trend['pred'], trend['res'], color='#ff7f0e', linewidth=2, marker='o', markersize=4, label='Binned Mean Trend')
    ax1.set_title('1. Residuals vs. Fitted Values (Log Scale)', fontweight='bold')
    ax1.set_xlabel('Predicted log(Price)')
    ax1.set_ylabel('Residuals')
    ax1.legend(loc='upper right', fontsize=8)
    ax1.grid(True, linestyle=':', alpha=0.5)

    # 2. 잔차 히스토그램 + KDE
    ax2 = axes[0, 1]
    sns.histplot(res_log, bins=60, kde=True, stat='density', color='#2b5c8f', alpha=0.45, ax=ax2, label='Residuals')
    x_grid = np.linspace(res_log.min(), res_log.max(), 200)
    ax2.plot(x_grid, stats.norm.pdf(x_grid, res_log.mean(), res_log.std()), color='#d62728', linestyle='--', linewidth=1.8, label='Normal Fit')
    ax2.set_title('2. Distribution of Log Residuals', fontweight='bold')
    ax2.set_xlabel('Residuals (log_price)')
    ax2.legend(loc='upper right', fontsize=8)
    ax2.grid(True, linestyle=':', alpha=0.5)

    # 3. 정규 Q-Q 플롯
    ax3 = axes[1, 0]
    (osm, osr), (slope, intercept, r) = stats.probplot(res_log, dist='norm')
    ax3.scatter(osm, osr, alpha=0.25, s=8, color='#2b5c8f', edgecolors='none')
    ax3.plot(osm, slope * osm + intercept, color='#d62728', linestyle='--', linewidth=1.5, label=f'Normal Line (R={r:.4f})')
    ax3.set_title('3. Normal Q-Q Plot', fontweight='bold')
    ax3.set_xlabel('Theoretical Quantiles')
    ax3.set_ylabel('Ordered Residuals')
    ax3.legend(loc='upper left', fontsize=8)
    ax3.grid(True, linestyle=':', alpha=0.5)

    # 4. 실제 가격 vs 예측 가격 ($)
    ax4 = axes[1, 1]
    ax4.scatter(act_dollar, pred_dollar, alpha=0.15, s=8, color='#2ca02c', edgecolors='none')
    ax4.plot([0, 20000], [0, 20000], color='#d62728', linestyle='--', linewidth=1.5, label='Perfect Prediction (y = x)')
    ax4.set_xlim(0, 20000)
    ax4.set_ylim(0, 22000)
    ax4.set_title('4. Actual vs. Predicted Price ($ Scale)', fontweight='bold')
    ax4.set_xlabel('Actual Price ($)')
    ax4.set_ylabel('Predicted Price ($)')
    ax4.legend(loc='upper left', fontsize=8)
    ax4.grid(True, linestyle=':', alpha=0.5)

    st.pyplot(fig_res)
