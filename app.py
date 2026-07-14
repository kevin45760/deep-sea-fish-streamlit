import streamlit as st
import os
from datetime import datetime
import json

st.set_page_config(page_title="深海奇蹟", page_icon="🌊", layout="wide")

# CSS 美化
st.markdown("""
<style>
    .main { background-color: #0a1f3d; color: #e0f0ff; }
    .stApp { background-color: #0a1f3d; }
    h1, h2, h3 { color: #00f5ff !important; }
    .fish-card {
        background: linear-gradient(145deg, #1e3a5f, #0f2a4a);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid #00f5ff33;
        transition: all 0.3s;
    }
    .fish-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0, 245, 255, 0.2);
    }
    .bubble {
        position: fixed;
        background: rgba(0, 245, 255, 0.1);
        border-radius: 50%;
        pointer-events: none;
        z-index: -1;
    }
</style>
""", unsafe_allow_html=True)

# 建立資料夾
if not os.path.exists("uploads"):
    os.makedirs("uploads")

def load_data():
    try:
        with open("fish_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open("fish_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

fish_data = load_data()

# 側邊導航
page = st.sidebar.selectbox("🌊 選擇頁面", 
    ["🏠 首頁", "🐟 魚類圖鑑", "📸 照片上傳", "ℹ️ 關於我們"])

st.sidebar.markdown("---")
st.sidebar.info("一起探索深海的奇妙世界！")

# ==================== 首頁 ====================
if page == "🏠 首頁":
    st.title("🌊 深海奇蹟")
    st.subheader("黑暗深淵中的生命奇蹟")
    
    st.image("https://picsum.photos/id/1015/1400/500", use_column_width=True)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("魚種數量", len(fish_data) + 8)
    with col2: st.metric("最深紀錄", "4000 米")
    with col3: st.metric("探索者", "持續增加中")

# ==================== 魚類圖鑑 ====================
elif page == "🐟 魚類圖鑑":
    st.title("🐟 深海魚類圖鑑")
    
    search = st.text_input("🔍 搜尋魚種", placeholder="輸入魚名...")
    
    # 預設魚類 + 優化卡片佈局
    default_fish = [
        {"name": "燈籠魚", "en": "Anglerfish", "depth": "200-2000米", "desc": "頭頂發光釣竿吸引獵物，深海最經典的捕食者。", "img": "https://picsum.photos/id/201/600/350"},
        {"name": "蝰魚", "en": "Viperfish", "depth": "500-4000米", "desc": "尖銳長牙，能吞下比自己更大的生物。", "img": "https://picsum.photos/id/251/600/350"},
        {"name": "Goblin Shark", "en": "Goblin Shark", "depth": "200-1300米", "desc": "可伸出巨大下顎的活化石鯊魚。", "img": "https://picsum.photos/id/866/600/350"},
        {"name": "鮟鱇魚", "en": "Blobfish", "depth": "600-1200米", "desc": "高壓下像果凍，在正常壓力下外表悲傷。", "img": "https://picsum.photos/id/1015/600/350"},
    ]
    
    all_fish = default_fish + fish_data
    cols = st.columns(2)
    
    for i, fish in enumerate(all_fish):
        if search.lower() in fish["name"].lower():
            with cols[i % 2]:
                st.markdown(f'<div class="fish-card">', unsafe_allow_html=True)
                st.image(fish["img"], use_column_width=True)
                st.subheader(fish["name"])
                st.caption(f"{fish['en']} • {fish['depth']}")
                st.write(fish["desc"])
                st.markdown('</div>', unsafe_allow_html=True)

# ==================== 照片上傳 ====================
elif page == "📸 照片上傳":
    st.title("📸 分享你的深海發現")
    
    col1, col2 = st.columns([2,1])
    with col1:
        name = st.text_input("魚類名稱 *")
        desc = st.text_area("描述這張照片")
        uploaded_file = st.file_uploader("上傳照片", type=["jpg", "png", "jpeg"])
        
        if st.button("🌊 上傳到圖鑑", type="primary"):
            if uploaded_file and name:
                file_path = os.path.join("uploads", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                new_fish = {
                    "name": name,
                    "en": "",
                    "depth": "社群分享",
                    "desc": desc or "使用者上傳的精彩照片",
                    "img": file_path
                }
                fish_data.append(new_fish)
                save_data(fish_data)
                st.success("上傳成功！感謝你的貢獻～")
                st.balloons()
            else:
                st.error("請填寫名稱並上傳照片")

# ==================== 關於我們 ====================
elif page == "ℹ️ 關於我們":
    st.title("關於深海奇蹟")
    st.write("這個網站使用 Python + Streamlit 開發，目的是推廣深海生態知識。")
    st.info("💡 歡迎大家上傳照片，一起豐富這個深海圖鑑！")

st.caption("🌊 深海奇蹟 | 守護海洋從認識開始")