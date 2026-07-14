import streamlit as st
import os
import sqlite3
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. 網頁基本設定
st.set_page_config(page_title="深海奇蹟", page_icon="🌊", layout="wide")

# 注入自訂 CSS，打造深海科技感視覺
st.markdown("""
<style>
    /* 🟢 修正 1：修改現代 Streamlit 全域背景顏色 */
    [data-testid="stAppViewContainer"] { 
        background: #0a1f3d !important; 
    }

    /* 🟢 修正 2：將按鈕樣式加上 !important 防止被官方主題覆蓋 */
    .stButton>button {
        background-color: #1e3a5f !important;
        color: #00f5ff !important;
        border-radius: 8px !important;
        border: 1px solid #00f5ff !important;
        transition: all 0.3s !important;
    }
    .stButton>button:hover {
        background-color: #00f5ff !important;
        color: #0a1f3d !important;
        box-shadow: 0 0 10px #00f5ff !important;
    }

    /* 🟢 修正 3：將原本的 .fish-card 改綁在 st.container(border=True) 的原生容器上 */
    div[data-testid="stVerticalBlockBorder"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        transition: all 0.3s ease-in-out !important;
    }
    div[data-testid="stVerticalBlockBorder"]:hover {
        transform: translateY(-3px) !important;
        background: rgba(255, 255, 255, 0.06) !important;
        border-color: rgba(0, 242, 254, 0.3) !important;
        box-shadow: 0 12px 40px 0 rgba(0, 242, 254, 0.15) !important;
    }

    /* 內部的文字 HTML 樣式保留，因為這是你自訂的 class，運作完全沒問題 */
    .fish-title {
        color: #00f2fe; 
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .fish-en {
        color: #8a9ba8;
        font-size: 13px;
        font-style: italic;
        margin-bottom: 12px;
    }
    .fish-meta {
        background: rgba(79, 172, 254, 0.1);
        color: #4facfe;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 12px;
    }
    .fish-desc {
        color: #e1e8ed; 
        line-height: 1.6; 
        font-size: 14px; 
        margin-top: 5px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# 2. 資料庫初始化與資料播種 (Seeding)
def init_db():
    conn = sqlite3.connect("fish.db")
    c = conn.cursor()
    # 加上這行：每次初始化時若欄位不對，就直接砍掉重建
    c.execute("DROP TABLE IF EXISTS fish") 
    c.execute("""CREATE TABLE IF NOT EXISTS fish (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    en TEXT,
                    depth TEXT,
                    desc TEXT,
                    img TEXT,
                    likes INTEGER,
                    upload_time TEXT
                )""")
    # ... 後續的 executemany
    
    # 檢查資料庫是否為空，若是，則自動匯入初始經典魚種
    c.execute("SELECT COUNT(*) FROM fish")
    if c.fetchone()[0] == 0:
        default_fish = [
            ("燈籠魚", "Anglerfish", "200-2000米", "頭頂發光釣竿吸引獵物，是最經典的深海魚。", "https://picsum.photos/id/201/500/300", 42, datetime.now().strftime("%Y-%m-%d %H:%M")),
            ("蝰魚", "Viperfish", "500-4000米", "擁有超長尖牙，身軀細長如鋼絲。", "https://picsum.photos/id/251/500/300", 28, datetime.now().strftime("%Y-%m-%d %H:%M")),
            ("加布林鯊", "Goblin Shark", "200-1300米", "活化石級別的鯊魚，可迅速伸出巨大下顎捕食。", "https://picsum.photos/id/866/500/300", 35, datetime.now().strftime("%Y-%m-%d %H:%M")),
            ("水滴魚", "Blobfish", "600-1200米", "在深海高壓下擁有果凍狀的外表，常被稱為最憂傷的魚。", "https://picsum.photos/id/1015/500/300", 51, datetime.now().strftime("%Y-%m-%d %H:%M"))
        ]
        c.executemany("""INSERT INTO fish (name, en, depth, desc, img, likes, upload_time) 
                         VALUES (?, ?, ?, ?, ?, ?, ?)""", default_fish)
    conn.commit()
    conn.close()

init_db()

if not os.path.exists("uploads"):
    os.makedirs("uploads")

# 2. 新增按讚資料庫寫入邏輯
def add_like(fish_id):
    conn = sqlite3.connect("fish.db")
    c = conn.cursor()
    c.execute("UPDATE fish SET likes = likes + 1 WHERE id = ?", (fish_id,))
    conn.commit()
    conn.close()

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
    conn = sqlite3.connect('deepsea.db')
    c = conn.cursor()
    c.execute("SELECT * FROM fish ORDER BY id DESC")
    fish = c.fetchall()
    conn.close()
    return fish

def add_fish(name, en, depth, desc, img):
    conn = sqlite3.connect('deepsea.db')
    c = conn.cursor()
    c.execute("""INSERT INTO fish (name, en, depth, desc, img, likes, upload_time) 
                 VALUES (?, ?, ?, ?, ?, 0, ?)""",
              (name, en, depth, desc, img, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def like_fish(fish_id):
    conn = sqlite3.connect('deepsea.db')
    c = conn.cursor()
    c.execute("UPDATE fish SET likes = likes + 1 WHERE id = ?", (fish_id,))
    conn.commit()
    conn.close()

# ==================== 側邊導航 ====================
page = st.sidebar.selectbox("🌊 選擇頁面", ["🏠 首頁", "🐟 魚類圖鑑", "📸 照片上傳", "📧 聯絡我們", "ℹ️ 關於我們"])
st.sidebar.markdown("---")
st.sidebar.info("🐋 一起守護深海生態！")

# ==================== 頁面邏輯 ====================
all_fish_data = load_fish()

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
    search = st.text_input("🔍 搜尋魚種 (請輸入中文或英文名稱)...", "").lower()
    
    for f in all_fish_data:
    f_id, f_name, f_en, f_depth, f_desc, f_img, f_likes, _ = f
    if search in f_name.lower() or search in f_en.lower():
        # 使用自訂的 CSS 容器包裝
        st.markdown(f'<div class="fish-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(f_img, use_column_width=True)
        with col2:
            # 🟢 調整部分：替換為精緻的 HTML 樣式標題與標籤，其餘邏輯不變
            st.markdown(f"""
                <div class="fish-title">🐟 {f_name}</div>
                <div class="fish-en">{f_en}</div>
                <div class="fish-meta">📍 棲息深度：{f_depth}</div>
                <p class="fish-desc">{f_desc}</p>
            """, unsafe_allow_html=True)
            
            # 原本的互動按鈕，完整保留！
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(f"❤️ 喜歡 ({f_likes})", key=f"like_{f_id}"):
                    like_fish(f_id)
                    st.success("已為牠集氣！")
                    st.rerun()
            with col_b:
                if st.button("🔗 分享專屬連結", key=f"share_{f_id}"):
                    st.code(f"https://share.streamlit.io/your-username/repo-name/~/fish_id={f_id}", language=None)
                    
        st.markdown('</div>', unsafe_allow_html=True)

elif page == "📸 照片上傳":
    st.title("📸 上傳你的深海魚發現")
    with st.form("upload_form", clear_on_submit=True):
        name = st.text_input("魚類中文名稱 *")
        en = st.text_input("英文學名 (選填)")
        depth = st.text_input("發現深度 (例如: 800米) *")
        desc = st.text_area("外觀與習性描述 *")
        uploaded_file = st.file_uploader("選擇照片", type=["jpg", "png", "jpeg"])
        submitted = st.form_submit_button("🚀 發布至圖鑑")
        
        if submitted:
            if uploaded_file and name and depth and desc:
                file_path = os.path.join("uploads", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                add_fish(name, en, depth, desc, file_path)
                st.success("✅ 成功上傳！新物種已加入深海圖鑑。")
                st.balloons()
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