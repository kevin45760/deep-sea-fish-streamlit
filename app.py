import streamlit as st
import os
import sqlite3
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import uuid
import time  # 🟢 引入時間模組，用來控制提示框顯示的停留時間

# 1. 網頁基本設定
st.set_page_config(page_title="深海奇蹟", page_icon="🌊", layout="wide")

# 🟢 2. 初始化瀏覽器身分代碼 (結合 st.query_params 讓 F5 刷新不失憶)
if "uid" in st.query_params:
    # 如果網址列有帶 uid 參數，直接拿來當作目前使用者的 user_id
    st.session_state.user_id = st.query_params["uid"]
else:
    # 如果網址列沒有（全新訪客），檢查 session 內有沒有，都沒有才發配新的
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    # 將這個 user_id 釘死到網址列上，這樣重整時就能被上方的 if 抓到
    st.query_params["uid"] = st.session_state.user_id

# 初始化側邊欄導航狀態
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "🏠 首頁"

# 注入自訂 CSS，打造深海科技感視覺
st.markdown("""
<style>
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
</style>
""", unsafe_allow_html=True)

DB_NAME = "fish_v3.db"

# 2. 資料庫初始化與資料播種 (Seeding)
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 加上這行：每次初始化時若欄位不對，就直接砍掉重建
    c.execute("""CREATE TABLE IF NOT EXISTS fish (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    en TEXT,
                    depth TEXT,
                    desc TEXT,
                    img TEXT,
                    likes INTEGER DEFAULT 0,
                    upload_time TEXT
                )""")
    # ... 後續的 executemany
    
    # 檢查資料庫是否為空，若是，則自動匯入初始經典魚種
    c.execute("""
        CREATE TABLE IF NOT EXISTS fish (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            en TEXT,
            depth TEXT,
            desc TEXT,
            img TEXT
        )
    """)
    
    # 防呆：如果以前建立的表漏了 likes 欄位，自動幫舊資料庫補上
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
        
    # 播種資料（系統內建的魚，上傳者標註為 "system"）
    c.execute("SELECT COUNT(*) FROM fish")
    if c.fetchone()[0] == 0:
        default_data = [
            ("鮟鱇魚", "Lophiiformes", "1000m - 4000m", "深海中的偽裝大師，頭頂有發光的小燈籠用來引誘食物。", "https://picsum.photos/id/1015/400/300", 0, datetime.now().strftime("%Y-%m-%d %H:%M"), "system"),
            ("大王具足蟲", "Bathynomus giganteus", "200m - 1000m", "深海的溫和清道夫，體型巨大的等足類生物。", "https://picsum.photos/id/1020/400/300", 0, datetime.now().strftime("%Y-%m-%d %H:%M"), "system")
        ]
        c.executemany("""INSERT INTO fish (name, en, depth, desc, img, likes, upload_time, uploader_id) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", default_data)
        
    conn.commit()
    conn.close()

init_db()

if not os.path.exists("uploads"):
    os.makedirs("uploads")

def parse_depth_range(depth_str):
    """將資料庫的深度文字（如 '200m - 1000m' 或 '4000m+'）轉換成 (min, max) 數值"""
    # 提取字串中所有的數字
    numbers = [int(n) for n in re.findall(r'\d+', str(depth_str))]
    if not numbers:
        return 0, 10000  # 若無數字，預設全範圍
    if len(numbers) == 1:
        # 例如 "4000m+" -> (4000, 10000)
        return numbers[0], 10000
    # 例如 "200m - 1000m" -> (200, 1000)
    return min(numbers), max(numbers)

# 3. 安全的郵件寄送功能（改自 Streamlit Secrets）
def send_email(user_name, user_email, subject, message):
    try:
        # 從安全設定檔讀取憑證，避免洩漏於 GitHub
        sender_email = st.secrets["gmail"]["sender_email"]
        sender_password = st.secrets["gmail"]["sender_password"]
        receiver_email = st.secrets["gmail"]["receiver_email"]
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"深海奇蹟網站留言 - {subject or '無主旨'}"
        
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

# 4. 資料庫核心操作
def load_fish():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM fish ORDER BY id DESC")
    fish = c.fetchall()
    conn.close()
    return fish

def get_fish_by_id(fish_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM fish WHERE id = ?", (fish_id,))
    fish = c.fetchone()
    conn.close()
    return fish

# 🟢 修改：將 uploader_id 儲存進資料庫
def add_fish(name, en, depth, desc, img, uploader_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO fish (name, en, depth, desc, img, likes, upload_time, uploader_id) 
                 VALUES (?, ?, ?, ?, ?, 0, ?, ?)""",
              (name, en, depth, desc, img, datetime.now().strftime("%Y-%m-%d %H:%M"), uploader_id))
    conn.commit()
    conn.close()

def like_fish(fish_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE fish SET likes = likes + 1 WHERE id = ?", (fish_id,))
    conn.commit()
    conn.close()

# 🟢 新增：修改資料的資料庫更新函數
def update_fish(fish_id, name, en, depth, desc):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""UPDATE fish 
                 SET name = ?, en = ?, depth = ?, desc = ? 
                 WHERE id = ?""", (name, en, depth, desc, fish_id))
    conn.commit()
    conn.close()

# ==================== 側邊導航 ====================
# 🟢 修改點：移除 key="nav_page"，改由變數與 index 控管，完美避開 Widget Key 鎖定限制
menu_options = ["🏠 首頁", "🐟 魚類圖鑑", "📸 相關資料上傳", "📧 聯絡我們", "ℹ️ 關於我們"]
default_idx = menu_options.index(st.session_state.nav_page) if st.session_state.nav_page in menu_options else 0
page = st.sidebar.selectbox("🌊 選擇頁面", menu_options, index=default_idx)
st.session_state.nav_page = page  # 同步點選狀態
st.sidebar.markdown("---")
st.sidebar.info("🐋 一起守護深海生態！")

# ==================== 頁面邏輯 ====================
all_fish_data = load_fish()

# --- 側邊欄：潛水艇下潛儀表板 ---
st.sidebar.markdown("### 🎛️ 潛水艇控制台")

# 雙向拉桿，讓使用者選擇想要探索的深度範圍 (預設 0 ~ 10000m)
depth_range = st.sidebar.slider(
    "⚓ 調整下潛深度 (公尺)",
    min_value=0,
    max_value=10000,
    value=(0, 10000),
    step=100
)

min_selected, max_selected = depth_range

# 根據拉桿數值，動態判定並顯示目前所處的「深海生態帶」
st.sidebar.markdown("---")
st.sidebar.markdown("### 📡 深度探測儀")
if max_selected <= 200:
    st.sidebar.error("☀️ **陽光帶 (Epipelagic)**\n\n海洋最上層，充滿陽光與生命。")
elif min_selected >= 200 and max_selected <= 1000:
    st.sidebar.warning("🌗 **暮色帶 (Mesopelagic)**\n\n微光粼粼，許多生物開始具備發光器。")
elif min_selected >= 1000 and max_selected <= 4000:
    st.sidebar.info("🌑 **半深海帶 (Bathypelagic)**\n\n完全黑暗！這裡的水壓極大，溫度極低。")
elif min_selected >= 4000:
    st.sidebar.success("💀 **深海帶 (Abyssopelagic)**\n\n接近無底深淵，生存著最奇異、最危險的巨獸。")
else:
    st.sidebar.write("🛸 **跨區域探索中...**")

# --- 【核心路由攔截】：成功頁面檢視 ---
if "success_fish_id" in st.session_state:
    st.title("🎉 新物種登錄成功！")
    target_fish = get_fish_by_id(st.session_state.success_fish_id)
    
    if target_fish:
        f_id, f_name, f_en, f_depth, f_desc, f_img, f_likes, f_time, f_uploader_id = target_fish
        st.success(f"✨ 恭喜！您發現的「{f_name}」已成功記錄在航海日誌中。以下為即時通報數據：")
        
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(f_img, use_container_width=True)
            with col2:
                st.markdown(f"""
                    <div class="fish-title">🐟 {f_name}</div>
                    <div class="fish-en">{f_en if f_en else '無學名紀錄'}</div>
                    <div class="fish-meta">📍 發現深度：{f_depth}</div>
                    <p class="fish-desc">{f_desc}</p>
                    <div style="color: #6688aa; font-size: 13px; margin-top: 10px;">🕒 登錄時間：{f_time}</div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ 進入深海圖鑑觀看全部物種", use_container_width=True):
            del st.session_state.success_fish_id
            st.session_state.nav_page = "🐟 魚類圖鑑"
            st.rerun()
    else:
        del st.session_state.success_fish_id
        st.rerun()


if page == "🏠 首頁":
    st.title("🌊 深海奇蹟")
    st.subheader("探索黑暗深淵的神秘生物")
    st.image("https://picsum.photos/id/1015/1200/500", use_column_width=True)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("已收錄魚種", len(all_fish_data))
    with col2: st.metric("最深紀錄", "4,000 米")
    with col3: st.metric("探索者生態圈", "歡迎你的加入")

elif page == "🐟 魚類圖鑑":
    st.title("🐟 深海魚類圖鑑")
    # 🟢 新增修改：若檢查到上傳成功旗標，就在圖鑑最上方顯示成功字樣框做檢視
    if st.session_state.get("upload_success_alert"):
        st.success("🎉 新物種登錄成功！已同步加入下方深海圖鑑供您檢視。")
        del st.session_state.upload_success_alert  # 顯示一次後清除旗標，防止重整時重複跳出
    search = st.text_input("搜尋魚種", placeholder="輸入中文或英文名稱探索深海魚種...", label_visibility="collapsed").lower()
    
    for f in all_fish_data:
        f_id, f_name, f_en, f_depth, f_desc, f_img, f_likes, f_time, f_uploader_id = f
        
        # 解析該魚類的深度區間
        fish_min, fish_max = parse_depth_range(f_depth)
        
        # 判斷式：名字/英文符合，且「魚類深度區間」與「使用者拉桿區間」有重疊
        name_match = search in f_name.lower() or search in f_en.lower()
        depth_match = (fish_min <= max_selected) and (fish_max >= min_selected)
        
        if name_match and depth_match:
            # 🟢 接下來的 st.container 與卡片渲染代碼完全不變，維持你原本寫好的漂亮 UI 即可！
            with st.container(border=True):
                col1, col2 = st.columns([1, 2])
                with col1:
                    # 🟢 順手修正：配合 2026 新版規範將 use_container_width 改為 width="stretch"
                    st.image(f_img, width="stretch")
                with col2:
                    st.markdown(f"""
                        <div class="fish-title">🐟 {f_name}</div>
                        <div class="fish-en">{f_en}</div>
                        <div class="fish-meta">📍 棲息深度：{f_depth}</div>
                        <p class="fish-desc">{f_desc}</p>
                    """, unsafe_allow_html=True)
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button(f"❤️ 喜歡 ({f_likes})", key=f"like_{f_id}"):
                            like_fish(f_id)
                            st.success("已為牠集氣！")
                            st.rerun()
                    with col_b:
                        if st.button("🔗 分享專屬連結", key=f"share_{f_id}"):
                            st.code(f"https://share.streamlit.io/your-username/repo-name/~/fish_id={f_id}", language=None)

                    # 🟢 當 user_id 成功鎖定在網址後，重整網頁這裡依然能通過驗證！
                    if f_uploader_id == st.session_state.user_id:
                        st.markdown("---")
                        show_edit = st.toggle("✏️ 編輯我的發現", key=f"toggle_{f_id}")
                        
                        if show_edit:
                            with st.form(key=f"edit_form_{f_id}"):
                                st.write("📝 **更新魚類資訊**")
                                edit_name = st.text_input("魚類中文名稱", value=f_name)
                                edit_en = st.text_input("英文學名", value=f_en)
                                edit_depth = st.text_input("發現深度", value=f_depth)
                                edit_desc = st.text_area("外觀與習性描述", value=f_desc)
                                
                                submit_edit = st.form_submit_button("💾 儲存修改")
                                if submit_edit:
                                    if edit_name and edit_depth and edit_desc:
                                        update_fish(f_id, edit_name, edit_en, edit_depth, edit_desc)
                                        st.success("✅ 資料更新成功！")
                                        st.rerun()
                                    else:
                                        st.error("❌ 必填欄位不可留白！")

elif page == "📸 相關資料上傳":
    st.title("📸 上傳你的深海魚發現")
    with st.form("upload_form", clear_on_submit=True):
        name = st.text_input("魚類中文名稱 *")
        en = st.text_input("英文學名 (選填)")
        depth = st.text_input("發現深度 (例如: 800米) *")
        desc = st.text_area("外觀與習性描述 *")
        uploaded_file = st.file_uploader("選擇照片", type=["jpg", "png", "jpeg"])
        submitted = st.form_submit_button("🚀 發布至圖鑑")
        
    # 🟢 將上傳成功的邏輯拉到表單外面，這樣提示框會自然渲染在頁面的「中下位置」
    if submitted:
        if uploaded_file and name and depth and desc:
            file_path = os.path.join("uploads", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            add_fish(name, en, depth, desc, file_path, st.session_state.user_id)
            
            # 🟢 這裡的自由變數轉跳再也不會引發錯誤了！
            st.session_state.upload_success_alert = True
            st.session_state.nav_page = "🐟 魚類圖鑑"
            
            st.success("✅ 上傳成功！正在為您導向圖鑑頁面做檢視...")
            
            time.sleep(1.2)
            st.rerun()
        else:
            st.error("❌ 請完整填寫必填欄位並上傳照片！")
        

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
                    st.balloons()
            else:
                st.warning("⚠️ 請完整填寫姓名、電子郵件與訊息內容。")

elif page == "ℹ️ 關於我們":
    st.title("ℹ️ 關於深海奇蹟")
    st.write("本計畫旨在透過現代 Web 技術，向大眾普及極限環境下的深海生態知識。")
    st.info("🛠️ **技術堆疊**：Python 3.10+ / Streamlit / SQLite3")

# ==================== 頁尾 ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #88aadd; padding: 20px;'>
    <p>🌊 深海奇蹟 © 2026 | 守護海洋 從認識開始</p>
</div>
""", unsafe_allow_html=True)