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
                 (id INTEGER PRIMARY KEY, name TEXT, en TEXT, depth TEXT, 
                  desc TEXT, img TEXT, likes INTEGER DEFAULT 0, upload_time TEXT)''')
    conn.commit()
    conn.close()

init_db()

# 建立上傳資料夾
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# ==================== 資料庫函數 ====================
def load_fish():
    conn = sqlite3.connect('deepsea.db')
    c = conn.cursor()
    c.execute("SELECT * FROM fish")
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
page = st.sidebar.selectbox("🌊 選擇頁面",
    ["🏠 首頁", "🐟 魚類圖鑑", "📸 照片上傳", "ℹ️ 關於我們"])

st.sidebar.markdown("---")
st.sidebar.info("深海探索者們，一起守護海洋！")

# ==================== 首頁 ====================
if page == "🏠 首頁":
    st.title("🌊 深海奇蹟")
    st.subheader("探索黑暗深淵的神秘生物")
    st.image("https://picsum.photos/id/1015/1200/500", use_column_width=True)
    
    fish_count = len(load_fish())
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("已收錄魚種", fish_count + 4)
    with col2: st.metric("最深紀錄", "4000 米")
    with col3: st.metric("探索者", "你也是！")

# ==================== 魚類圖鑑 ====================
elif page == "🐟 魚類圖鑑":
    st.title("🐟 深海魚類圖鑑")
    search = st.text_input("🔍 搜尋魚種（支援中文/英文）", "").lower()
    
    fish_list = load_fish()
    default_fish = [  # 預設魚類
        {"id": 0, "name": "燈籠魚", "en": "Anglerfish", "depth": "200-2000米", "desc": "頭頂發光釣竿吸引獵物", "img": "https://picsum.photos/id/201/500/300", "likes": 42},
        {"id": 0, "name": "蝰魚", "en": "Viperfish", "depth": "500-4000米", "desc": "擁有超長尖牙", "img": "https://picsum.photos/id/251/500/300", "likes": 28},
        {"id": 0, "name": "Goblin Shark", "en": "Goblin Shark", "depth": "200-1300米", "desc": "可伸出巨大下顎的活化石", "img": "https://picsum.photos/id/866/500/300", "likes": 35},
        {"id": 0, "name": "鮟鱇魚", "en": "Blobfish", "depth": "600-1200米", "desc": "外表悲傷的果凍魚", "img": "https://picsum.photos/id/1015/500/300", "likes": 51},
    ]
    
    all_fish = default_fish + [{"id": f[0], "name": f[1], "en": f[2], "depth": f[3], "desc": f[4], "img": f[5], "likes": f[6]} for f in fish_list]
    
    for fish in all_fish:
        if search in fish["name"].lower() or search in fish.get("en","").lower():
            with st.container(border=True):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(fish["img"], use_column_width=True)
                with col2:
                    st.subheader(f"{fish['name']} ({fish.get('en', '')})")
                    st.caption(f"深度：{fish['depth']} | ❤️ {fish['likes']}")
                    st.write(fish["desc"])
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("❤️ 喜歡", key=f"like_{fish['id'] or fish['name']}"):
                            if fish['id'] > 0:  # 只對資料庫的資料增加喜歡
                                like_fish(fish['id'])
                            st.success("已加入喜歡！")
                            st.rerun()
                    with col_b:
                        if st.button("🔗 分享", key=f"share_{fish['name']}"):
                            st.code(f"https://你的網站/fish/{fish['name']}", language=None)

# ==================== 照片上傳 ====================
elif page == "📸 照片上傳":
    st.title("📸 上傳你的深海魚照片")
    name = st.text_input("魚類名稱")
    desc = st.text_area("簡單描述")
    uploaded_file = st.file_uploader("選擇照片", type=["jpg", "png", "jpeg"])
    
    if st.button("🚀 上傳照片"):
        if uploaded_file and name:
            file_path = os.path.join("uploads", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            add_fish(name, "", "未知", desc, file_path)
            st.success(f"✅ {name} 上傳成功！")
            st.balloons()
        else:
            st.error("請填寫名稱並上傳照片")

# ==================== 關於我們 ====================
elif page == "ℹ️ 關於我們":
    st.title("關於深海奇蹟")
    st.write("這個網站使用 Python + Streamlit + SQLite 開發")
    st.info("💡 上傳照片一起豐富深海圖鑑！")

st.caption("🌊 深海探索 永不止步 | 使用 SQLite 持久化資料")