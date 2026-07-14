import streamlit as st
import os
import sqlite3
from datetime import datetime

st.set_page_config(page_title="深海奇蹟", page_icon="🌊", layout="wide")

# 初始化 SQLite 資料庫
def init_db():
    conn = sqlite3.connect('deepsea.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS fish
                 (id INTEGER PRIMARY KEY, name TEXT, en TEXT, depth TEXT, desc TEXT, img TEXT, upload_time TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ==================== 側邊導航 ====================
page = st.sidebar.selectbox("🌊 選擇頁面",
    ["🏠 首頁", "🐟 魚類圖鑑", "📸 照片上傳", "ℹ️ 關於我們"])

# 載入所有魚類
def load_fish():
    conn = sqlite3.connect('deepsea.db')
    c = conn.cursor()
    c.execute("SELECT * FROM fish")
    fish = c.fetchall()
    conn.close()
    return fish

# 新增魚類
def add_fish(name, en, depth, desc, img):
    conn = sqlite3.connect('deepsea.db')
    c = conn.cursor()
    c.execute("INSERT INTO fish (name, en, depth, desc, img, upload_time) VALUES (?, ?, ?, ?, ?, ?)",
              (name, en, depth, desc, img, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

# ==================== 首頁 ====================
if page == "🏠 首頁":
    st.title("🌊 深海奇蹟")
    st.subheader("探索黑暗深淵的神秘生物")
    st.image("https://picsum.photos/id/1015/1200/500", use_column_width=True)
    
    fish_count = len(load_fish())
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("已收錄魚種", fish_count + 4)

# ==================== 魚類圖鑑 ====================
elif page == "🐟 魚類圖鑑":
    st.title("🐟 深海魚類圖鑑")
    search = st.text_input("🔍 搜尋魚種")
    
    fish_list = load_fish()
    for fish in fish_list:
        if search.lower() in fish[1].lower():
            with st.container(border=True):
                col1, col2 = st.columns([1,2])
                with col1:
                    st.image(fish[5], use_column_width=True)  # img path
                with col2:
                    st.subheader(fish[1])
                    st.write(fish[4])

# ==================== 照片上傳 ====================
elif page == "📸 照片上傳":
    st.title("📸 上傳你的深海魚照片")
    name = st.text_input("魚類名稱")
    desc = st.text_area("描述")
    uploaded_file = st.file_uploader("選擇照片", type=["jpg", "png", "jpeg"])
    
    if st.button("上傳"):
        if uploaded_file and name:
            file_path = os.path.join("uploads", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            add_fish(name, "", "未知", desc, file_path)
            st.success("上傳成功！")
            st.balloons()
        else:
            st.error("請填寫名稱並上傳照片")

st.caption("🌊 使用 SQLite 資料庫持久化")