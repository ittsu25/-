import streamlit as st
import pandas as pd
import random
import base64

# --- 背景画像を設定する関数 ---
def set_bg_from_local(image_file):
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read())
    
    # 画像の拡張子（jpgかpngか）を判定して設定
    ext = "jpeg" if image_file.endswith(".jpg") else "png"
    
    st.markdown(
        f"""
        <style>
        /* 画面の一番上にある白い帯（ヘッダー）を強力に透明にする */
        [data-testid="stHeader"] {{
            background-color: transparent !important;
        }}
        
        /* 背景画像の設定 */
        .stApp {{
            background-image: url(data:image/{ext};base64,{encoded_string.decode()});
            background-size: cover;       
            background-position: center;  
            background-attachment: fixed; 
        }}
        
        /* 問題文などを白くして読みやすくし、黒い枠線をつける */
        .stMarkdown, .stRadio, .stSelectbox {{
            background-color: rgba(255, 255, 255, 0.8);
            padding: 10px;
            border-radius: 10px;
            border: 2px solid black;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# 背景をセット（※ bg.jpg が無い場合はエラーを出さずに進む）
try:
    set_bg_from_local('bg.jpg') 
except FileNotFoundError:
    pass

# --- 1. データの読み込み ---
try:
    df = pd.read_csv('kobun.csv', encoding='shift_jis')
except UnicodeDecodeError:
    df = pd.read_csv('kobun.csv', encoding='utf-8')

# --- 2. 10語ずつの出題範囲（グループ）を作成 ---
group_labels = []
for i in range(0, len(df), 10):
    start = i + 1
    end = min(i + 10, len(df))
    group_labels.append(f"{start}〜{end}語")

# --- 3. サイドバー（設定メニュー） ---
st.sidebar.title("テスト設定")
selected_group = st.sidebar.selectbox("出題範囲（10語ずつ）", group_labels)

# 選ばれた10語分のデータだけを切り出す
group_idx = group_labels.index(selected_group)
target_df = df.iloc[group_idx * 10 : (group_idx + 1) * 10].reset_index(drop=True)

# --- 4. 状態の管理 ---
if 'current_group' not in st.session_state or st.session_state.current_group != selected_group:
    st.session_state.current_group = selected_group
    st.session_state.q_data = None
    st.session_state.answered = False

if 'q_data' not in st.session_state:
    st.session_state.q_data = None

# --- 5. 問題を作る関数 ---
def make_question():
    idx = random.randint(0, len(target_df) - 1)
    correct_row = target_df.iloc[idx]
    correct_ans = correct_row['意味']
    
    wrong_choices = target_df[target_df['意味'] != correct_ans]['意味'].tolist()
    sample_size = min(3, len(wrong_choices))
    choices = random.sample(wrong_choices, sample_size)
    choices.append(correct_ans)
    random.shuffle(choices)
    
    st.session_state.q_data = {
        "word": correct_row['単語'],
        "correct_ans": correct_ans,
        "choices": choices
    }
    st.session_state.answered = False
    st.session_state.result_msg = ""

if st.session_state.q_data is None:
    make_question()

# --- 6. メイン画面の表示 ---
st.title("古文単語315 マスター (4択テスト)")
st.write(f"**現在の範囲:** {selected_group}")
st.header(f"問題：【 {st.session_state.q_data['word']} 】")

# --- 7. 4択テストの表示 ---
st.write("正しい意味を選んでください。")
for choice in st.session_state.q_data['choices']:
    # ボタンが押された時の処理
    if st.button(choice, disabled=st.session_state.answered, key=choice):
        st.session_state.answered = True
        if choice == st.session_state.q_data['correct_ans']:
            st.session_state.result_msg = "⭕ 大正解！"
        else:
            st.session_state.result_msg = f"❌ 不正解... 正解は「{st.session_state.q_data['correct_ans']}」"
        st.rerun()

# --- 8. 結果と「次の問題へ」ボタン ---
if st.session_state.answered:
    st.subheader(st.session_state.result_msg)
    if st.button("次の問題へ"):
        make_question()
        st.rerun()