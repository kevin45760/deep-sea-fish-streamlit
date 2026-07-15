import streamlit as st
import os
import sqlite3
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import uuid
import time  # 🟢 用來控制提示框顯示的停留時間
import pandas as pd
import plotly.express as px

# 1. 網頁基本設定
st.set_page_config(page_title="深海未知的奧妙", page_icon="🌊", layout="wide")

# 🟢 初始化瀏覽器身分代碼 (結合 st.query_params 讓 F5 刷新不失憶)
if "uid" in st.query_params:
    st.session_state.user_id = st.query_params["uid"]
else:
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    st.query_params["uid"] = st.session_state.user_id

# 初始化側邊欄導航狀態
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "🏠 首頁"

# 安全跳轉機制，避免直接修改 widget 綁定的 nav_page 導致 Streamlit 報錯或選單閃爍
if "page_goto" in st.session_state:
    st.session_state.nav_page = st.session_state.page_goto
    del st.session_state.page_goto

# 注入自訂 CSS，打造深海科技感視覺
st.markdown("""
<style>
    /* 🔍 利用 :has() 確保只針對「圖鑑搜尋框」套用膠囊深海風格 */
    div[data-testid="stTextInputRootElement"]:has(input[placeholder*="探索深海魚種"]) {
        border-radius: 30px !important; 
        background: rgba(255, 255, 255, 0.04) !important; 
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 4px 12px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    div[data-testid="stTextInputRootElement"]:hover {
        background: rgba(255, 255, 255, 0.07) !important;
        border-color: rgba(0, 229, 255, 0.3) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 229, 255, 0.1) !important;
    }
            
    div[data-testid="stTextInputRootElement"]:focus-within {
        background: rgba(13, 30, 54, 0.9) !important;
        border-color: #00e5ff !important;
        box-shadow: 
            0 0 0 3px rgba(0, 229, 255, 0.25), 
            0 12px 30px rgba(0, 0, 0, 0.5) !important;
    }

    div[data-testid="stTextInputRootElement"] input[placeholder*="探索深海魚種"] {
        padding-left: 38px !important; 
        color: #ffffff !important;
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="%2300e5ff" class="bi bi-search" viewBox="0 0 16 16"><path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/></svg>') !important;
        background-repeat: no-repeat !important;
        background-position: 10px center !important; 
    }   
            
    [data-testid="stAppViewContainer"] { 
        background: radial-gradient(circle at 50% 40%, #0d1e36 0%, #050b14 100%) !important; 
    }

    div[data-testid="stVerticalBlockBorder"] {
        background: linear-gradient(135deg, rgba(22, 38, 64, 0.7) 0%, rgba(10, 18, 30, 0.85) 100%) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.18) !important; 
        border-radius: 20px !important;
        padding: 24px !important;
        margin-bottom: 25px !important;
        box-shadow: 
            0 20px 50px rgba(0, 0, 0, 0.55), 
            inset 0 1px 1px rgba(255, 255, 255, 0.15) !important;
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
    }

    div[data-testid="stVerticalBlockBorder"]:hover {
        transform: translateY(-6px) scale(1.005) !important;
        background: linear-gradient(135deg, rgba(28, 48, 80, 0.8) 0%, rgba(14, 24, 40, 0.9) 100%) !important;
        border-color: rgba(0, 229, 255, 0.35) !important;
        border-top-color: rgba(0, 229, 255, 0.6) !important;
        box-shadow: 
            0 30px 60px rgba(0, 229, 255, 0.12), 
            0 12px 25px rgba(0, 0, 0, 0.6),
            inset 0 1px 1px rgba(255, 255, 255, 0.25) !important;
    }

    .fish-title {
        background: linear-gradient(90deg, #00e5ff 0%, #7c4dff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 24px;
        font-weight: 800;
        margin-bottom: 3px;
        filter: drop-shadow(0 2px 8px rgba(0, 229, 255, 0.2));
    }

    .fish-en {
        color: #708090;
        font-size: 13px;
        font-style: italic;
        margin-bottom: 12px;
        letter-spacing: 0.5px;
    }
            
    .fish-meta {
        background: rgba(0, 229, 255, 0.08);
        color: #00e5ff;
        border: 1px solid rgba(0, 229, 255, 0.2);
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 15px;
    }

    .fish-desc {
        color: #d1dbe5; 
        line-height: 1.7; 
        font-size: 14.5px; 
        margin-top: 5px;
        margin-bottom: 20px;
    }

    .stButton>button {
        background: linear-gradient(135deg, #192d47 0%, #0d1826 100%) !important;
        color: #8be9fd !important;
        border-radius: 12px !important;
        border: 1px solid rgba(139, 233, 253, 0.25) !important;
        border-top: 1px solid rgba(139, 233, 253, 0.5) !important;
        font-weight: 600 !important;
        box-shadow: 
            0 4px 10px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        transition: all 0.2s ease !important;
    }

    .stButton>button:hover {
        background: linear-gradient(135deg, #00e5ff 0%, #00aaff 100%) !important;
        color: #050b14 !important;
        border-color: #00e5ff !important;
        transform: translateY(-2px) !important;
        box-shadow: 
            0 8px 20px rgba(0, 229, 255, 0.35),
            inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
    }

    .stButton>button:active {
        transform: translateY(1px) !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2) !important;
    }
               
    .st-emotion-cache-15zrj4w a, 
    a.anchor-link, 
    [data-testid="stHeaderActionElements"] {
        display: none !important;
    }   

</style>
""", unsafe_allow_html=True)

DB_NAME = "fish_v3.db"

# 2. 資料庫初始化與資料播種 (Seeding)
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 建立主魚類資料表
    c.execute("""CREATE TABLE IF NOT EXISTS fish (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    en TEXT,
                    depth TEXT,
                    desc TEXT,
                    img TEXT,
                    likes INTEGER DEFAULT 0,
                    upload_time TEXT,
                    uploader_id TEXT,
                    habitat TEXT DEFAULT '未標記'
                )""")
                
    # 建立按讚紀錄資料表
    c.execute("""
        CREATE TABLE IF NOT EXISTS likes_registry (
            user_id TEXT,
            fish_id INTEGER,
            PRIMARY KEY (user_id, fish_id)
        )
    """)
    
    # 自動向後相容升級
    try:
        c.execute("ALTER TABLE fish ADD COLUMN uploader_id TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE fish ADD COLUMN likes INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE fish ADD COLUMN upload_time TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute("ALTER TABLE fish ADD COLUMN habitat TEXT DEFAULT '未標記'")
    except sqlite3.OperationalError:
        pass
        
    # 播種資料
    c.execute("SELECT COUNT(*) FROM fish")
    if c.fetchone()[0] == 0:
        default_data = [
            ("鮟鱇魚", "Lophiiformes", "1000m - 4000m", "深海中的偽裝大師，頭頂有發光的小燈籠用來引誘食物。", "https://picsum.photos/id/1015/400/300", 0, datetime.now().strftime("%Y-%m-%d %H:%M"), "system", "太平洋 (Pacific Ocean)"),
            ("大王具足蟲", "Bathynomus giganteus", "200m - 1000m", "深海的溫和清道夫，體型巨大的等足類生物。", "https://picsum.photos/id/1020/400/300", 0, datetime.now().strftime("%Y-%m-%d %H:%M"), "system", "印度洋 (Indian Ocean)")
        ]
        c.executemany("""INSERT INTO fish (name, en, depth, desc, img, likes, upload_time, uploader_id, habitat) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", default_data)
        
    conn.commit()
    conn.close()

init_db()

if not os.path.exists("uploads"):
    os.makedirs("uploads")

def parse_depth_range(depth_str):
    numbers = [int(n) for n in re.findall(r'\d+', str(depth_str))]
    if not numbers:
        return 0, 10000  
    if len(numbers) == 1:
        return numbers[0], 10000
    return min(numbers), max(numbers)

# 安全的郵件寄送功能
def send_email(user_name, user_email, subject, message):
    try:
        sender_email = st.secrets["gmail"]["sender_email"]
        sender_password = st.secrets["gmail"]["sender_password"]
        receiver_email = st.secrets["gmail"]["receiver_email"]
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"您在深海未知的奧妙有留言 - {subject or '無主旨'}"
        
        body = f"收到新留言！\n\n姓名：{user_name}\n信箱：{user_email}\n主旨：{subject}\n\n訊息內容：\n{message}\n\n時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"郵件系統錯誤：{str(e)}（請檢查 Secrets 設定是否正確）")
        return False

# 🟢 載入資料庫內所有「不重複」的棲息地區，並與預設選項合併
def load_habitats():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT habitat FROM fish WHERE habitat IS NOT NULL AND habitat != '未標記' AND habitat != ''")
    db_habitats = [row[0] for row in c.fetchall()]
    conn.close()
    
    presets = [
        "太平洋 (Pacific Ocean)", 
        "大西洋 (Atlantic Ocean)", 
        "印度洋 (Indian Ocean)", 
        "北冰洋 (Arctic Ocean)", 
        "南冰洋 (Southern Ocean)"
    ]
    
    all_habs = []
    for h in (presets + db_habitats):
        if h not in all_habs:
            all_habs.append(h)
    return all_habs

def load_fish():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT id, name, en, depth, desc, img, likes, upload_time, uploader_id, habitat 
                 FROM fish ORDER BY id DESC""")
    fish = c.fetchall()
    conn.close()
    return fish

def get_fish_by_id(fish_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT id, name, en, depth, desc, img, likes, upload_time, uploader_id, habitat 
                 FROM fish WHERE id = ?""", (fish_id,))
    fish = c.fetchone()
    conn.close()
    return fish

def add_fish(name, en, depth, desc, img, uploader_id, habitat):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO fish (name, en, depth, desc, img, likes, upload_time, uploader_id, habitat) 
                 VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)""",
              (name, en, depth, desc, img, datetime.now().strftime("%Y-%m-%d %H:%M"), uploader_id, habitat))
    conn.commit()
    conn.close()

def has_user_liked(user_id, fish_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM likes_registry WHERE user_id = ? AND fish_id = ?", (user_id, fish_id))
    result = c.fetchone()
    conn.close()
    return result is not None

def toggle_like_fish(fish_id, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if has_user_liked(user_id, fish_id):
        c.execute("DELETE FROM likes_registry WHERE user_id = ? AND fish_id = ?", (user_id, fish_id))
        c.execute("UPDATE fish SET likes = MAX(0, likes - 1) WHERE id = ?", (fish_id,))
        status = "removed"
    else:
        c.execute("INSERT INTO likes_registry (user_id, fish_id) VALUES (?, ?)", (user_id, fish_id))
        c.execute("UPDATE fish SET likes = likes + 1 WHERE id = ?", (fish_id,))
        status = "added"
    conn.commit()
    conn.close()
    return status

def update_fish(fish_id, name, en, depth, desc, habitat):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""UPDATE fish 
                 SET name = ?, en = ?, depth = ?, desc = ?, habitat = ? 
                 WHERE id = ?""", (name, en, depth, desc, habitat, fish_id))
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_NAME)

def get_top_5_liked_fish():
    conn = get_db_connection()
    query = """
        SELECT f.name as "魚類名稱", COUNT(l.fish_id) as "人氣指數"
        FROM fish f
        LEFT JOIN likes_registry l ON f.id = l.fish_id
        GROUP BY f.id
        ORDER BY "人氣指數" DESC, f.name ASC
        LIMIT 5
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty or df["人氣指數"].sum() == 0:
        df = pd.DataFrame({"魚類名稱": ["尚無數據"], "人氣指數": [0]})
    return df

def get_depth_statistics():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, depth FROM fish")
    rows = cursor.fetchall()
    conn.close()
    
    total_species = len(rows)
    if total_species == 0:
        return (0, 0, 0), ("無數據", 0)
        
    max_depth = 0
    deepest_fish_name = "未知"
    total_avg_depth = 0
    
    for name, depth_str in rows:
        d_min, d_max = parse_depth_range(depth_str)
        avg_single = (d_min + d_max) / 2.0
        total_avg_depth += avg_single
        
        if d_max > max_depth:
            max_depth = d_max
            deepest_fish_name = name
            
    avg_depth = total_avg_depth / total_species if total_species > 0 else 0
    stats = (total_species, avg_depth, max_depth)
    deepest_fish = (deepest_fish_name, max_depth)
    return stats, deepest_fish

def render_dashboard():
    st.markdown("## 🛰️ 萬米深海數據觀測儀")
    st.markdown("即時同步潛水艇收集之聲納數據與隊員喜好回饋。")
    st.markdown("<br>", unsafe_allow_html=True)
    
    try:
        stats, deepest_fish = get_depth_statistics()
        total_species, avg_depth, max_depth = stats
        deepest_fish_name = deepest_fish[0] if deepest_fish else "未知"
    except Exception as e:
        st.error(f"📡 數據載入失敗，請確認資料庫設定：{e}")
        return

    col1, col2, col3 = st.columns(3)
    
    metric_style = """
    <div style="
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0.01) 100%);
        border: 1px solid rgba(0, 229, 255, 0.15);
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    ">
        <p style="margin: 0; color: #8892b0; font-size: 13px; letter-spacing: 0.5px;">{title}</p>
        <h2 style="margin: 8px 0 0 0; color: {color}; font-size: 24px; font-family: sans-serif; font-weight: bold;">{value}</h2>
    </div>
    """
    
    with col1:
        st.markdown(metric_style.format(
            title="🏷️ 已觀測物種總數", 
            value=f"{total_species} 種", 
            color="#64ffda"
        ), unsafe_allow_html=True)
        
    with col2:
        st.markdown(metric_style.format(
            title="🌡️ 平均棲息深度", 
            value=f"{int(avg_depth) if avg_depth else 0} 公尺", 
            color="#00e5ff"
        ), unsafe_allow_html=True)
        
    with col3:
        st.markdown(metric_style.format(
            title="👑 真正的深海之王", 
            value=f"{deepest_fish_name}", 
            color="#ff007f"
        ), unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown("### 🏆 隊員最喜愛深海生物排行")
    
    df_likes = get_top_5_liked_fish()
    
    fig = px.bar(
        df_likes, 
        x="人氣指數", 
        y="魚類名稱", 
        orientation='h',
        color="人氣指數",
        color_continuous_scale=["#0a192f", "#0088cc", "#00e5ff", "#64ffda"], 
    )
    
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#8be9fd",
        title_font_color="#00e5ff",
        showlegend=False,
        margin=dict(l=20, r=20, t=10, b=10),
        height=320,
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.05)",
            tickformat="d", 
            title=""
        ),
        yaxis=dict(
            autorange="reversed", 
            showgrid=False,
            title=""
        ),
        coloraxis_showscale=False 
    )
    
    fig.update_traces(
        marker_line_color='#00e5ff',
        marker_line_width=1.5,
        opacity=0.85,
        hovertemplate="<b>%{y}</b><br>獲得 👍 %{x} 個讚<extra></extra>"
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="
        background: rgba(10, 25, 47, 0.4);
        border-left: 4px solid #ff007f;
        border-radius: 4px 12px 12px 4px;
        padding: 15px 20px;
    ">
        <p style="margin: 0 0 5px 0; color: #ff007f; font-weight: bold; font-size: 14px;">📡 聲納探索報告：</p>
        <p style="margin: 0; color: #a8b2d1; font-size: 13.5px; line-height: 1.6;">
            本艦觀測發現，目前已登錄的深海生物 average 棲息在 <b>{int(avg_depth) if avg_depth else 0} 公尺</b> 的無光帶。
            其中 <b>{deepest_fish_name}</b> 以高達 <b>{max_depth if max_depth else 0} 公尺</b> 的極限生存深度，稱霸深淵。
            其體內演化出的獨特化學抗壓機制，仍是目前艦艇科學家積極研究的謎題。
        </p>
    </div>
    """, unsafe_allow_html=True)

# ==================== 側邊導航 ====================
menu_options = ["🏠 首頁", "🐟 魚類圖鑑", "📸 相關資料上傳", "📧 聯絡我們", "ℹ️ 關於我們"]
page = st.sidebar.selectbox("🌊 選擇頁面", menu_options, key="nav_page")
st.sidebar.markdown("---")
st.sidebar.info("🐋 一起守護深海生態！")

# ==================== 頁面邏輯 ====================
all_fish_data = load_fish()

st.sidebar.markdown("### 📡 深海環境音")

audio_tracks = {
    "📡 潛艇主聲納 (Sonar)": "https://raw.githubusercontent.com/kevin45760/deep-sea-fish-streamlit/main/sonar.mp3",
    "🫧 深海微光氣泡 (Bubbles)": "https://raw.githubusercontent.com/kevin45760/deep-sea-fish-streamlit/main/Bubble.mp3",
    "🐋 遠古鯨魚歌聲 (Whales)": "https://raw.githubusercontent.com/kevin45760/deep-sea-fish-streamlit/main/whale.mp3",
    "🌀 萬米深海暗流 (Abyss Hum)": "https://raw.githubusercontent.com/kevin45760/deep-sea-fish-streamlit/main/abyss.mp3"
}

options_html = ""
for name, url in audio_tracks.items():
    options_html += f'<option value="{url}">{name}</option>'

default_url = list(audio_tracks.values())[0]

audio_control_html = f"""
<div style="font-family: system-ui, -apple-system, sans-serif; padding: 5px;">
    <select id="audio-select" onchange="changeTrack()" style="
        width: 100%;
        background: #0d1826;
        color: #00e5ff;
        border: 1px solid rgba(0, 229, 255, 0.3);
        border-radius: 10px;
        padding: 8px;
        font-size: 13.5px;
        font-weight: 500;
        outline: none;
        cursor: pointer;
        box-shadow: 0 0 10px rgba(0, 229, 255, 0.05);
        margin-bottom: 12px;
        transition: all 0.3s ease;
    " onfocus="this.style.borderColor='#00e5ff'; this.style.boxShadow='0 0 15px rgba(0,229,255,0.2)';" onblur="this.style.borderColor='rgba(0, 229, 255, 0.3)';">
        {options_html}
    </select>

    <audio id="ambient-audio" loop src="{default_url}"></audio> 
    
    <button onclick="toggleAudio()" id="sonar-btn" style="
        width: 100%;
        background: linear-gradient(135deg, #00e5ff 0%, #00aaff 100%); 
        color: #050b14; 
        border: none; 
        padding: 8px 16px; 
        border-radius: 12px; 
        font-weight: bold; 
        cursor: pointer; 
        box-shadow: 0 0 15px rgba(0, 229, 255, 0.3); 
        transition: all 0.3s ease;
    ">
        ▶️ 啟動環境音效
    </button>
</div>

<script>
    var audio = document.getElementById('ambient-audio');
    var btn = document.getElementById('sonar-btn');
    var select = document.getElementById('audio-select');

    function changeTrack() {{
        var isPlaying = !audio.paused;
        audio.src = select.value;
        audio.load();
        if (isPlaying) {{
            audio.play().catch(function(error) {{
                console.log("播放被瀏覽器阻擋: ", error);
            }});
        }}
    }}

    function toggleAudio() {{
        if (audio.paused) {{
            audio.play().then(function() {{
                btn.innerHTML = '⏸️ 暫停深海音效';
                btn.style.background = 'linear-gradient(135deg, #ff4b4b 0%, #ff2b2b 100%)';
                btn.style.color = '#ffffff';
                btn.style.boxShadow = '0 0 15px rgba(255, 75, 75, 0.4)';
            }}).catch(function(error) {{
                alert("請先與網頁任意地方互動，才能開啟音效喔！");
            }});
        }} else {{
            audio.pause();
            btn.innerHTML = '▶️ 啟動環境音效';
            btn.style.background = 'linear-gradient(135deg, #00e5ff 0%, #00aaff 100%)';
            btn.style.color = '#050b14';
            btn.style.boxShadow = '0 0 15px rgba(0, 229, 255, 0.3)';
        }}
    }}
</script>
"""

with st.sidebar:
    st.components.v1.html(audio_control_html, height=110)

# --- 【核心路由攔截】：成功頁面檢視 ---
if "success_fish_id" in st.session_state:
    st.title("🎉 新物種登錄成功！")
    target_fish = get_fish_by_id(st.session_state.success_fish_id)
    
    if target_fish:
        f_id, f_name, f_en, f_depth, f_desc, f_img, f_likes, f_time, f_uploader_id, f_habitat = target_fish
        st.success(f"✨ 恭喜！您發現的「{f_name}」已成功記錄在航海日誌中。以下為即時通報數據：")
        
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(f_img, use_container_width=True)
            with col2:
                st.markdown(f"""
                    <div class="fish-title">🐟 {f_name}</div>
                    <div class="fish-en">{f_en if f_en else '無學名紀錄'}</div>
                    <div class="fish-meta">📍 發現深度：{f_depth} | 🗺️ 棲息地區：{f_habitat}</div>
                    <p class="fish-desc">{f_desc}</p>
                    <div style="color: #6688aa; font-size: 13px; margin-top: 10px;">🕒 登錄時間：{f_time}</div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ 進入深海圖鑑觀看全部物種", use_container_width=True):
            del st.session_state.success_fish_id
            st.session_state.page_goto = "🐟 魚類圖鑑"  
            st.rerun()
    else:
        del st.session_state.success_fish_id
        st.rerun()


if page == "🏠 首頁":
    st.title("🌊 深海未知的奧妙")
    st.markdown("<p style='color: #64ffda; font-size: 14px; margin-top: -15px;'>By Kevin Chen</p>", unsafe_allow_html=True)
    st.subheader("探索黑暗深淵的神秘生物")
    
    carousel_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { margin: 0; padding: 0; background: transparent; font-family: system-ui, -apple-system, sans-serif; overflow: hidden; }
            .slider-container {
                position: relative;
                width: 100%;
                height: 380px;
                overflow: hidden;
                border-radius: 20px;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            .slide {
                display: none;
                position: relative;
                width: 100%;
                height: 100%;
                animation: fade 0.6s ease-in-out;
            }
            .slide img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            .slide-active { display: block; }
            .nav-zone {
                position: absolute;
                top: 0;
                bottom: 0;
                width: 18%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                color: rgba(255, 255, 255, 0.15);
                font-size: 36px;
                font-weight: bold;
                transition: all 0.3s ease;
                user-select: none;
                z-index: 10;
            }
            .nav-left { 
                left: 0; 
                background: linear-gradient(to right, rgba(5, 11, 20, 0.45), transparent); 
                padding-right: 20px;
            }
            .nav-right { 
                right: 0; 
                background: linear-gradient(to left, rgba(5, 11, 20, 0.45), transparent); 
                padding-left: 20px;
            }
            .nav-zone:hover {
                color: #00e5ff;
                text-shadow: 0 0 12px rgba(0, 229, 255, 0.8);
                font-size: 44px;
            }
            .nav-left:hover { background: linear-gradient(to right, rgba(0, 229, 255, 0.12), transparent); }
            .nav-right:hover { background: linear-gradient(to left, rgba(0, 229, 255, 0.12), transparent); }
            .caption-panel {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(to top, rgba(5, 11, 20, 0.95) 0%, rgba(13, 30, 54, 0.5) 100%);
                backdrop-filter: blur(15px);
                -webkit-backdrop-filter: blur(15px);
                padding: 18px 40px;
                color: #ffffff;
                z-index: 5;
                border-top: 1px solid rgba(255, 255, 255, 0.05);
            }
            .caption-title {
                font-size: 20px;
                font-weight: 800;
                color: #00e5ff;
                margin-bottom: 5px;
                filter: drop-shadow(0 2px 6px rgba(0, 229, 255, 0.3));
            }
            .caption-desc {
                font-size: 13.5px;
                color: #d1dbe5;
                line-height: 1.5;
                max-width: 80%;
            }
            .dots-container {
                position: absolute;
                bottom: 22px;
                right: 40px;
                z-index: 6;
            }
            .dot {
                width: 6px;
                height: 6px;
                margin: 0 4px;
                background-color: rgba(255, 255, 255, 0.25);
                border-radius: 50%;
                display: inline-block;
                transition: all 0.4s ease;
                cursor: pointer;
            }
            .dot-active { 
                background-color: #00e5ff; 
                width: 16px; 
                border-radius: 3px;
                box-shadow: 0 0 8px #00e5ff; 
            }
            @keyframes fade {
                from { opacity: 0.6; transform: scale(1.01); }
                to { opacity: 1; transform: scale(1); }
            }
        </style>
    </head>
    <body>
        <div class="slider-container">
            <div class="nav-zone nav-left" onclick="moveSlide(-1)">&#10094;</div>
            <div class="nav-zone nav-right" onclick="moveSlide(1)">&#10095;</div>

            <div class="slide slide-active">
                <img src="https://images.unsplash.com/photo-1551244072-5d12893278ab?q=80&w=1200" alt="馬里亞納海溝">
                <div class="caption-panel">
                    <div class="caption-title">1. 馬里亞納海溝 (Mariana Trench) · 太平洋</div>
                    <div class="caption-desc">地球已知最深的海溝，其「斐查茲海淵」深達近 11,000 米，是一片完全黑暗、承受千倍水壓的超深淵荒漠。</div>
                </div>
            </div>

            <div class="slide">
                <img src="https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1200" alt="湯加海溝">
                <div class="caption-panel">
                    <div class="caption-title">2. 湯加海溝 (Tonga Trench) · 西南太平洋</div>
                    <div class="caption-desc">南半球最深邃的地帶，其極點「地平線海淵」深達 10,882 米，由太平洋板塊劇烈俯衝隱沒而形成。</div>
                </div>
            </div>

            <div class="slide">
                <img src="https://images.unsplash.com/photo-1544551763-46a013bb70d5?q=80&w=1200" alt="菲律賓海溝">
                <div class="caption-panel">
                    <div class="caption-title">3. 菲律賓海溝 (Philippine Trench) · 西太平洋</div>
                    <div class="caption-desc">又稱民答那峨海溝，深達 10,540 米。地處活躍板塊邊緣，是一條如深邃刀疤般縱貫菲律賓東側的海底大裂縫。</div>
                </div>
            </div>

            <div class="slide">
                <img src="https://images.unsplash.com/photo-1439405326854-014607f694d7?q=80&w=1200" alt="克馬德克海溝">
                <div class="caption-panel">
                    <div class="caption-title">4. 克馬德克海溝 (Kermadec Trench) · 南太平洋</div>
                    <div class="caption-desc">深度達 10,047 米，與湯加海溝相連。科學家曾在此處捕捉到打破體型紀錄的超巨大深海端足類甲殼生物。</div>
                </div>
            </div>

            <div class="slide">
                <img src="https://images.unsplash.com/photo-1682687220063-4742bd7fd538?q=80&w=1200" alt="波多黎各海溝">
                <div class="caption-panel">
                    <div class="caption-title">5. 波多黎各海溝 (Puerto Rico Trench) · 大西洋</div>
                    <div class="caption-desc">大西洋與加勒比海交界處的最深地帶（8,376 米）。此處地質結構極其複雜，是極具破壞力的海嘯海溝。</div>
                </div>
            </div>

            <div class="slide">
                <img src="https://images.unsplash.com/photo-1439405326854-014607f694d7?q=80&w=1200" alt="爪哇海溝">
                <div class="caption-panel">
                    <div class="caption-title">6. 爪哇海溝 (Java Trench) · 印度洋</div>
                    <div class="caption-desc">印度洋唯一突破官方七千米深度的海溝（最深 7,725 米），綿延於蘇門答臘與爪哇島南側，是引發南亞海嘯的源頭。</div>
                </div>
            </div>

            <div class="slide">
                <img src="https://images.unsplash.com/photo-1518837695005-2083093ee35b?q=80&w=1200" alt="南桑威奇海溝">
                <div class="caption-panel">
                    <div class="caption-title">7. 南桑威奇海溝 (South Sandwich Trench) · 南冰洋</div>
                    <div class="caption-desc">深達 8,266 米，地處冰天雪地的南極圈邊緣。它是地球上唯一充滿冰冷寒流隱沒、環境最惡劣的極地超深淵。</div>
                </div>
            </div>

            <div class="slide">
                <img src="https://images.unsplash.com/photo-1520114878144-6123749968dd?q=80&w=1200" alt="日本海溝">
                <div class="caption-panel">
                    <div class="caption-title">8. 日本海溝 (Japan Trench) · 西太平洋</div>
                    <div class="caption-desc">位於日本列島以東，最深處達 8,412 米。這裡是太平洋板塊隱沒的核心地帶，頻繁引發大型深源地震與海嘯。</div>
                </div>
            </div>

            <div class="slide">
                <img src="https://images.unsplash.com/photo-1520114878144-6123749968dd?q=80&w=1200" alt="莫洛伊海淵">
                <div class="caption-panel">
                    <div class="caption-title">9. 莫洛伊海淵 (Molloy Deep) · 北冰洋</div>
                    <div class="caption-desc">位於格陵蘭島海域，深達 5,550 米。雖然深度不及太平洋，但它是北極圈內最寒冷、最與世隔絕的無底巨坑。</div>
                </div>
            </div>

            <div class="slide">
                <img src="https://images.unsplash.com/photo-1568430462989-4b16f61d2cfc?q=80&w=1200" alt="加拉巴哥裂谷熱泉">
                <div class="caption-panel">
                    <div class="caption-title">10. 加拉巴哥裂谷熱泉 (Galapagos Rift) · 東太平洋</div>
                    <div class="caption-desc">科學界首個發現深海「黑煙囪」的地方。熱泉高達數百度並夾帶硫化物，卻孕育出完全不仰賴陽光的化學合成奇特生態系。</div>
                </div>
            </div>

            <div class="dots-container">
                <div class="dot dot-active" onclick="jumpToSlide(0)"></div>
                <div class="dot" onclick="jumpToSlide(1)"></div>
                <div class="dot" onclick="jumpToSlide(2)"></div>
                <div class="dot" onclick="jumpToSlide(3)"></div>
                <div class="dot" onclick="jumpToSlide(4)"></div>
                <div class="dot" onclick="jumpToSlide(5)"></div>
                <div class="dot" onclick="jumpToSlide(6)"></div>
                <div class="dot" onclick="jumpToSlide(7)"></div>
                <div class="dot" onclick="jumpToSlide(8)"></div>
                <div class="dot" onclick="jumpToSlide(9)"></div>
            </div>
        </div>

        <script>
            let currentIndex = 0;
            const slides = document.querySelectorAll('.slide');
            const dots = document.querySelectorAll('.dot');
            let autoTimer = setInterval(() => { moveSlide(1); }, 7000);

            function updateCarousel() {
                slides.forEach((slide, i) => {
                    if (i === currentIndex) {
                        slide.classList.add('slide-active');
                        dots[i].classList.add('dot-active');
                    } else {
                        slide.classList.remove('slide-active');
                        dots[i].classList.remove('dot-active');
                    }
                });
            }

            function moveSlide(step) {
                clearInterval(autoTimer);
                currentIndex += step;
                if (currentIndex >= slides.length) currentIndex = 0;
                if (currentIndex < 0) currentIndex = slides.length - 1;
                updateCarousel();
                autoTimer = setInterval(() => { moveSlide(1); }, 7000);
            }

            function jumpToSlide(index) {
                clearInterval(autoTimer);
                currentIndex = index;
                updateCarousel();
                autoTimer = setInterval(() => { moveSlide(1); }, 7000);
            }
        </script>
    </body>
    </html>
    """
    
    st.components.v1.html(carousel_html, height=390)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("已收錄魚種", len(all_fish_data))
    with col2: st.metric("最深紀錄", "4,000 米")
    with col3: st.metric("探索者生態圈", "歡迎你的加入")

elif page == "🐟 魚類圖鑑":
    
    OCEAN_ZONES = [
        {"name": "☀️ 表層帶 (Epipelagic)", "min": 0, "max": 200, "color": "#FFD700", "desc": "光線充足，是海洋生物最繁盛、光合作用活躍的區域。"},
        {"name": "🌅 中層帶 / 半深海帶 (Mesopelagic)", "min": 200, "max": 1000, "color": "#5FD5FC", "desc": "微弱光線的弱光帶，許多深海生物白天在此隱匿，晚上浮上表層覓食。"},
        {"name": "🌌 深層帶 / 深海帶 (Bathypelagic)", "min": 1000, "max": 4000, "color": "#4169E1", "desc": "進入完全黑暗的無光帶，這裡的生物多具有發光器官，承受巨大水壓。"},
        {"name": "🌋 深淵帶 (Abyssopelagic)", "min": 4000, "max": 6000, "color": "#00e5ff", "desc": "接近冰點的漆黑世界，水壓極高，棲息著奇特、演化特殊的深海怪物。"},
        {"name": "🕳️ 超深淵帶 / 海溝帶 (Hadalpelagic)", "min": 6000, "max": 11000, "color": "#ff4081", "desc": "地球上最深邃的海溝，生命跡象極為稀少，但仍有極限生物頑強生存。"}
    ]

    if "depth_range" not in st.session_state:
        st.session_state.depth_range = (200, 4000)

    st.markdown("### 📍 快速定位海洋分層")
    col1, col2, col3, col4, col5 = st.columns(5)

    if col1.button("☀️ 表層", use_container_width=True):
        st.session_state.depth_range = (0, 200)
        st.rerun()
    if col2.button("🌅 半深海", use_container_width=True):
        st.session_state.depth_range = (200, 1000)
        st.rerun()
    if col3.button("🌌 深海", use_container_width=True):
        st.session_state.depth_range = (1000, 4000)
        st.rerun()
    if col4.button("🌋 深淵", use_container_width=True):
        st.session_state.depth_range = (4000, 6000)
        st.rerun()
    if col5.button("🕳️ 超深淵", use_container_width=True):
        st.session_state.depth_range = (6000, 11000)
        st.rerun()

    depth_range = st.slider(
        "🔍 拖曳滑桿選擇自訂深度範圍 (公尺)",
        min_value=0,
        max_value=11000,
        key="depth_range",  
        step=100
    )

    sel_min, sel_max = depth_range

    active_zones = []
    for zone in OCEAN_ZONES:
        if not (sel_max < zone["min"] or sel_min > zone["max"]):
            active_zones.append(zone)

    st.markdown("### 🏷️ 您目前正在探索的生態帶：")

    if active_zones:
        cols = st.columns(len(active_zones))
        for idx, zone in enumerate(active_zones):
            with cols[idx]:
                st.markdown(
                    f"""
                    <div style="
                        background-color: {zone['color']}15; 
                        border-left: 4px solid {zone['color']}; 
                        padding: 12px; 
                        border-radius: 6px;
                        margin-bottom: 15px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        min-height: 140px;
                    ">
                        <strong style="color: {zone['color']}; font-size: 15px;">{zone['name']}</strong><br/>
                        <code style="background-color: transparent; color: #888; font-size: 11px;">{zone['min']}m - {zone['max']}m</code><br/>
                        <p style="font-size: 12px; margin-top: 5px; color: #ddd; line-height: 1.4;">{zone['desc']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.info("請拖曳滑桿以探索特定深度！")

    st.markdown("---")
    st.title("🐟 深海魚類圖鑑")
    
    tab_encyclopedia, tab_dashboard = st.tabs(["🗺️ 探索圖鑑", "📊 深海數據觀測站"])
    
    with tab_encyclopedia:
        if st.session_state.get("upload_success_alert"):
            st.success("🎉 新物種登錄成功！已同步加入下方深海圖鑑供您檢視!")
            del st.session_state.upload_success_alert  
        
        search = st.text_input("搜尋魚種", placeholder="輸入中文或英文名稱探索深海魚種...", label_visibility="collapsed").lower()
        
        # 🟢 讀取資料庫現存所有棲息地選項
        db_habitats = load_habitats()

        for f in all_fish_data:
            f_id, f_name, f_en, f_depth, f_desc, f_img, f_likes, f_time, f_uploader_id, f_habitat = f
            
            fish_min, fish_max = parse_depth_range(f_depth)
            
            name_match = search in f_name.lower() or search in f_en.lower()
            depth_match = (fish_min <= sel_max) and (fish_max >= sel_min)
            
            if name_match and depth_match:
                with st.container(border=True):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.image(f_img, width="stretch")
                    with col2:
                        st.markdown(f"""
                            <div class="fish-title">🐟 {f_name}</div>
                            <div class="fish-en">{f_en}</div>
                            <div class="fish-meta">📍 棲息深度：{f_depth} | 🗺️ 棲息地區：{f_habitat}</div>
                            <p class="fish-desc">{f_desc}</p>
                        """, unsafe_allow_html=True)
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            user_already_liked = has_user_liked(st.session_state.user_id, f_id)
                            btn_label = f"❤️ 已喜歡 ({f_likes})" if user_already_liked else f"🤍 喜歡 ({f_likes})"
                            if st.button(btn_label, key=f"like_{f_id}"):
                                res = toggle_like_fish(f_id, st.session_state.user_id)
                                if res == "added": st.toast("已加入你的喜歡清單！")
                                else: st.toast("已收回讚。")
                                time.sleep(0.3)
                                st.rerun()  
                                
                        with col_b:
                            if st.button("🔗 分享連結", key=f"share_{f_id}"):
                                st.code(f"https://share.streamlit.io/your-username/repo-name/~/fish_id={f_id}", language=None)
                                
                        with col_c:
                            tts_html = f"""
                            <button onclick="speakDescription()" style="
                                width: 100%;
                                height: 35px;
                                background: linear-gradient(135deg, #192d47 0%, #0d1826 100%);
                                color: #8be9fd;
                                border-radius: 12px;
                                border: 1px solid rgba(139, 233, 253, 0.25);
                                border-top: 1px solid rgba(139, 233, 253, 0.5);
                                font-size: 14px;
                                font-weight: 600;
                                cursor: pointer;
                                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
                                transition: all 0.2s ease;
                            " onmouseover="this.style.background='linear-gradient(135deg, #00e5ff 0%, #00aaff 100%)'; this.style.color='#050b14';" onmouseout="this.style.background='linear-gradient(135deg, #192d47 0%, #0d1826 100%)'; this.style.color='#8be9fd';">
                                🔊 聽取導覽
                            </button>
                            <script>
                                function speakDescription() {{
                                    window.speechSynthesis.cancel();
                                    var msg = new SpeechSynthesisUtterance({repr(f_desc)});
                                    msg.lang = 'zh-TW'; 
                                    msg.rate = 1.0;     
                                    msg.pitch = 0.8;    
                                    window.speechSynthesis.speak(msg);
                                }}
                            </script>
                            """
                            st.components.v1.html(tts_html, height=45)

                        if f_uploader_id == st.session_state.user_id:
                            st.markdown("---")
                            show_edit = st.toggle("✏️ 編輯我的發現", key=f"toggle_{f_id}")
                            
                            if show_edit:
                                st.write("📝 **更新魚類資訊**")
                                edit_name = st.text_input("魚類中文名稱", value=f_name, key=f"edit_name_{f_id}")
                                edit_en = st.text_input("英文學名", value=f_en, key=f"edit_en_{f_id}")
                                edit_depth = st.text_input("發現深度", value=f_depth, key=f"edit_depth_{f_id}")
                                
                                # 決定選單的預設選取 index
                                if f_habitat in db_habitats:
                                    default_idx = db_habitats.index(f_habitat) + 1
                                else:
                                    default_idx = 0  
                                    
                                # 初始化編輯用 habitat 數值
                                if f"edit_hab_val_state_{f_id}" not in st.session_state:
                                    st.session_state[f"edit_hab_val_state_{f_id}"] = f_habitat

                                # 編輯專用 Callback
                                def make_edit_callback(fid):
                                    def callback():
                                        sel = st.session_state[f"edit_hab_sel_{fid}"]
                                        if sel != "-- 手動自訂輸入 --":
                                            st.session_state[f"edit_hab_val_state_{fid}"] = sel
                                        else:
                                            st.session_state[f"edit_hab_val_state_{fid}"] = ""
                                    return callback

                                edit_habitat_sel = st.selectbox(
                                    "🔮 選擇現有地區 * (可選取快速帶入)", 
                                    ["-- 手動自訂輸入 --"] + db_habitats, 
                                    index=default_idx, 
                                    key=f"edit_hab_sel_{f_id}",
                                    on_change=make_edit_callback(f_id)
                                )
                                
                                # 當選了固定地區時，防呆鎖定輸入框
                                # 當選了固定地區時，防呆鎖定輸入框
                                is_edit_disabled = (edit_habitat_sel != "-- 手動自訂輸入 --") # 🟢 改用這個，編輯切換也順暢無阻！
                                    
                                edit_habitat = st.text_input(
                                    "自訂地區 (支援直接自訂輸入)", 
                                    key=f"edit_hab_val_state_{f_id}",
                                    disabled=is_edit_disabled,
                                    placeholder="可在這直接打字或直接修改...", 
                                    help="若要手動打字，請將上方的選擇現有地區切換為『-- 手動自訂輸入 --』"
                                )
                                
                                edit_desc = st.text_area("外觀與習性描述", value=f_desc, key=f"edit_desc_{f_id}")
                                
                                submit_edit = st.button("💾 儲存修改", key=f"btn_edit_{f_id}", use_container_width=True)
                                if submit_edit:
                                    if edit_name and edit_depth and edit_desc and edit_habitat.strip():
                                        update_fish(f_id, edit_name, edit_en, edit_depth, edit_desc, edit_habitat.strip())
                                        st.success("✅ 資料更新成功！")
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.error("❌ 必填欄位不可留白！")

    with tab_dashboard:
        render_dashboard()

elif page == "📸 相關資料上傳":
    st.title("📸 上傳你的深海魚發現")
    
    db_habitats = load_habitats()
    
    # 初始化 session state 變數
    if "upload_habitat_val" not in st.session_state:
        st.session_state.upload_habitat_val = ""

    # 定義下拉選單變動時的 Callback 函式
    # 定義下拉選單變動時的 Callback 函式
    def on_habitat_select_change():
        selected = st.session_state.upload_habitat_sel  # 🟢 修正為這行即可！
        if selected != "-- 手動自訂輸入 --":
            # 選了具體地區，自動帶入自訂地區框並鎖定
            st.session_state.upload_habitat_val = selected
        else:
            # 切換回自訂時，清空讓使用者自己打
            st.session_state.upload_habitat_val = ""

    with st.container(border=True):
        # 頂部紅字提醒
        st.markdown("<span style='color: #d93025; font-size: 0.9rem;'>*必填</span>", unsafe_allow_html=True)
        st.write("") 

        # 魚類中文名稱 (必填)
        st.markdown("魚類中文名稱 :red[*]")
        name = st.text_input("魚類中文名稱", label_visibility="collapsed")
        
        # 英文學名 (選填)
        st.markdown("英文學名 (選填)")
        en = st.text_input("英文學名", label_visibility="collapsed")
        
        # 發現深度 (必填)
        st.markdown("發現深度 (例如: 800米) :red[*]")
        depth = st.text_input("發現深度", label_visibility="collapsed")
        
        # ------------------- 調整區塊開始 -------------------
        
        # 1. 選擇現有地區 -> 🚀 改名為「🔮 選擇地區」並改為【必填 (加紅色星號)】
        st.markdown("🔮 選擇地區 :red[*]")
        selected_habitat = st.selectbox(
            "選擇地區", 
            ["-- 手動自訂輸入 --"] + db_habitats,
            key="upload_habitat_sel",
            on_change=on_habitat_select_change,
            label_visibility="collapsed"
        )
        
        # 2. 棲息地區 -> 🚀 改名為「✍️ 自訂地區」並改為【選填 (無紅色星號)】
        # 2. 棲息地區 -> 🚀 改名為「✍️ 自訂地區」並改為【選填 (無紅色星號)】
        st.markdown("✍️ 自訂地區 (選填)")
        is_disabled = (selected_habitat != "-- 手動自訂輸入 --") # 🟢 改用這個，切換時反應最即時！
        
        final_habitat = st.text_input(
            "自訂地區", 
            key="upload_habitat_val",
            placeholder="若上方選取『-- 手動自訂輸入 --』，請在此處打字輸入全新地區...",
            disabled=is_disabled,
            label_visibility="collapsed",
            help="若要手動打字，請先將上方的『選擇地區』切換為『-- 手動自訂輸入 --』"
        )
        
        # ------------------- 調整區塊結束 -------------------
            
        # 外觀與習性描述 (必填)
        st.markdown("外觀與習性描述 :red[*]")
        desc = st.text_area("外觀與習性描述", label_visibility="collapsed")
        
        # 選擇照片 (必填)
        st.markdown("選擇照片 :red[*]")
        uploaded_file = st.file_uploader("選擇照片", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
        
        st.write("") 
        submitted = st.button("🚀 發布至圖鑑", use_container_width=True)
        
    if submitted:
        # 🔴 核心防呆驗證邏輯：
        # 只有當選取「手動自訂輸入」時，final_habitat 內部才絕對不能是空的！
        habitat_is_valid = True
        chosen_habitat = ""
        
        if selected_habitat == "-- 手動自訂輸入 --":
            chosen_habitat = final_habitat.strip()
            if not chosen_habitat:
                habitat_is_valid = False
        else:
            chosen_habitat = selected_habitat

        # 判斷所有必填項
        if uploaded_file and name and depth and desc and habitat_is_valid:
            file_path = os.path.join("uploads", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 將整理好的地區存入資料庫
            add_fish(name, en, depth, desc, file_path, st.session_state.user_id, chosen_habitat)
            
            st.session_state.upload_success_alert = True
            st.session_state.page_goto = "🐟 魚類圖鑑"  
            
            st.success("✅ 上傳成功！正在為您導向圖鑑頁面做檢視...")
            time.sleep(1.2)
            st.rerun()
        else:
            # 依據沒通過的條件給出對應的錯誤提示
            if not habitat_is_valid:
                st.error("❌ 您選擇了『-- 手動自訂輸入 --』，請務必在『自訂地區』輸入框內填寫新地區名稱！")
            else:
                st.error("❌ 請確認所有必填欄位（帶 * 號）皆已填寫，並已上傳照片！")
        

elif page == "📧 聯絡我們":
    st.title("📧 聯絡我們")
    st.write("對深海世界有任何想法或指教？歡迎留言給我們！")
    
    with st.form("contact_form"):
        col1, col2 = st.columns(2)
        with col1: name = st.text_input("您的姓名 *")
        with col2: email = st.text_input("電子郵件 *")
        subject = st.text_input("主旨")
        message = st.text_area("您的訊息 *", height=150)
        submitted = st.form_submit_button("📤 送出訊息")
        
        if submitted:
            if name and email and message:
                if send_email(name, email, subject, message):
                    st.success("✅ 訊息已成功送出！我們將儘速與您聯繫。")
            else:
                st.warning("⚠️ 請完整填寫姓名、電子郵件與訊息內容。")

elif page == "ℹ️ 關於我們":
    st.title("⚓ 關於本站與開發者")
    
    st.markdown("## 🌊 為什麼建立「深海奇蹟」？")
    st.markdown("""
    > **「人類對火星表面的了解，甚至超過了對地球深海的認識。」**
    
    深海是一片佔據地球龐大體積、卻極少被人類窺探的神秘領域。建立這個網頁的初衷，是希望能透過**現代化的網頁視覺技術**與**動態互動介面**，將那些隱身於千米之下、打破生物學常理的深海奇觀，以最直覺且具備科技感的方式呈現給大眾。
    
    我們試圖打造一個不僅僅是數據堆疊的圖鑑，而是一個兼具探險儀式感與視覺饗宴的「數位深海觀測站」，點燃每個人對未知深淵的強烈好奇心。
    """)
    st.markdown("---")
    
    st.markdown("## 💻 遇見開發者")
    
    developer_html = """
    <style>
        @keyframes deepSeaZoom {
            from { transform: scale(0.7); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
    </style>

    <div style="
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%);
        border-radius: 15px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        position: relative;
    ">
        
        <div id="avatarModal" onclick="closeAvatarModal()" style="
            display: none; 
            position: fixed; 
            top: 0; 
            left: 0; 
            width: 100%; 
            height: 100%; 
            background: rgba(5, 11, 20, 0.85); 
            backdrop-filter: blur(8px); 
            -webkit-backdrop-filter: blur(8px);
            z-index: 999; 
            align-items: center; 
            justify-content: center; 
            cursor: zoom-out;
        ">
            <img src="https://i.ibb.co/gL8gG7wP/F4-EDD8-BD-C778-4-E4-B-B752-801-DB1863375.jpg" style="
                max-height: 260px; 
                max-width: 260px; 
                border-radius: 15px; 
                border: 2px solid #00e5ff; 
                box-shadow: 0 0 35px rgba(0, 229, 255, 0.6); 
                animation: deepSeaZoom 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            ">
        </div>

        <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 20px;">
            <img src="https://i.ibb.co/gL8gG7wP/F4-EDD8-BD-C778-4-E4-B-B752-801-DB1863375.jpg" onclick="openAvatarModal()" style="
                width: 60px; 
                height: 60px; 
                border-radius: 50%; 
                object-fit: cover;
                border: 2px solid #00e5ff;
                box-shadow: 0 0 15px rgba(0, 229, 255, 0.5);
                cursor: zoom-in;
                transition: transform 0.2s ease;
            " onmouseover="this.style.transform='scale(1.08)'" onmouseout="this.style.transform='scale(1)'">
            
            <div>
                <h3 style="margin: 0; color: #ffffff; font-size: 22px; font-family: sans-serif;">Kevin Chen</h3>
                <p style="margin: 5px 0 0 0; color: #00e5ff; font-size: 14px; font-weight: 500; letter-spacing: 0.5px;">
                    Full-Stack Enthusiast & Cloud Explorer
                </p>
            </div>
        </div>
        
        <p style="color: #d1dbe5; line-height: 1.6; font-size: 14.5px; margin-bottom: 15px;">
            嗨！我是 Kevin，目前就讀於<b>資訊工程系</b>。我熱衷於全端網頁開發、自動化系統部署以及現代 UI/UX 視覺設計。喜歡將複雜的後端邏輯與數據，轉化為優雅、流暢且具備科技感的網頁互動體驗。目前有個可愛女友(施羽軒寶寶，也稱作寶貝小公主、小軒)，她是我生活中最大的動力來源，也常給我許多創意靈感。
        </p>
        
        <div style="margin-top: 20px;">
            <h4 style="color: #64ffda; margin-bottom: 10px; font-size: 15px;">🛠️ 技術雷達與專長</h4>
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                <span style="background: rgba(0, 229, 255, 0.1); color: #00e5ff; padding: 4px 10px; border-radius: 20px; font-size: 12px; border: 1px solid rgba(0, 229, 255, 0.2);">Python Flask / Streamlit</span>
                <span style="background: rgba(0, 229, 255, 0.1); color: #00e5ff; padding: 4px 10px; border-radius: 20px; font-size: 12px; border: 1px solid rgba(0, 229, 255, 0.2);">Linux Admin & Nginx</span>
                <span style="background: rgba(0, 229, 255, 0.1); color: #00e5ff; padding: 4px 10px; border-radius: 20px; font-size: 12px; border: 1px solid rgba(0, 229, 255, 0.2);">Modern UI Design</span>
            </div>
        </div>

        <div style="margin-top: 25px; padding-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.05); display: flex; flex-direction: column; gap: 8px; color: #a8b2d1; font-size: 13px;">
            <div>🌟 <b>專業認證：</b> 已考取 Microsoft Azure 多項雲端核心認證 (AZ-900, DP-900, AI-900)。</div>
            <div>💡 <b>其他實踐：</b> 課餘時間擔任數位學伴，嘗試用科技與熱忱帶領小朋友探索世界。</div>
            <div>🎵 <b>程式燃料：</b> 寫 Code 時不可或缺的是 JADE、Deca Joins 與 Sunset Rollercoaster 的獨立音樂。</div>
        </div>
    </div>

    <script>
        function openAvatarModal() {
            document.getElementById('avatarModal').style.display = 'flex';
        }
        function closeAvatarModal() {
            document.getElementById('avatarModal').style.display = 'none';
        }
    </script>
    """
    st.components.v1.html(developer_html, height=1200, scrolling=True)

# ==================== 頁尾 ====================
st.markdown("<br><br><br>", unsafe_allow_html=True) 
st.markdown("""
    <div style="text-align: center; padding: 20px 0; border-top: 1px solid rgba(255, 255, 255, 0.05);">
        <p>🌊 深海奇蹟 | 守護海洋 從認識開始</p>
        <p style="color: #6a7b95; font-size: 13px; letter-spacing: 1px;">
            © 2026 Designed & Built by <span style="color: #00e5ff; font-weight: bold;">Kevin Chen</span>. All Rights Reserved.
        </p>
    </div>
""", unsafe_allow_html=True)