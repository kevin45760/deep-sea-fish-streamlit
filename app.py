import streamlit as st
import os
import json
from datetime import datetime

st.set_page_config(page_title="深海奇蹟", page_icon="🌊", layout="wide")

# 建立資料夾與載入資料
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
st.sidebar.info("深海探索者們，一起守護海洋！")

# ==================== 首頁 ====================
if page == "🏠 首頁":
    st.title("🌊 深海奇蹟")
    st.subheader("探索黑暗深淵的神秘生物")
    st.image("https://picsum.photos/id/1015/1200/500", use_column_width=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("已收錄魚種", len(fish_data) + 8)
    with col2:
        st.metric("最深紀錄", "4000 米")
    with col3:
        st.metric("探索者", "你也是！")

# ==================== 魚類圖鑑 ====================
elif page == "🐟 魚類圖鑑":
    st.title("🐟 深海魚類圖鑑")
    
    # 優化搜尋
    search = st.text_input("🔍 搜尋魚種（支援中文/英文）", "").lower()
    
    default_fish = [
        {"name": "燈籠魚", "en": "Anglerfish", "depth": "200-2000米", "desc": "頭頂有發光釣竿，用來吸引獵物。雌魚遠大於雄魚。", "img": "https://picsum.photos/id/201/500/300", "likes": 42},
        {"name": "蝰魚", "en": "Viperfish", "depth": "500-4000米", "desc": "擁有超長尖牙，能吞下比自己更大的獵物。", "img": "https://picsum.photos/id/251/500/300", "likes": 28},
        {"name": "Goblin Shark", "en": "Goblin Shark", "depth": "200-1300米", "desc": "活化石級別，可伸出巨大下顎捕食。", "img": "https://picsum.photos/id/866/500/300", "likes": 35},
        {"name": "鮟鱇魚", "en": "Blobfish", "depth": "600-1200米", "desc": "在深海高壓下像果凍，外表看起來很悲傷。", "img": "https://picsum.photos/id/1015/500/300", "likes": 51},
    ]
    
    all_fish = default_fish + fish_data
    
    # 搜尋過濾
    filtered_fish = [fish for fish in all_fish if 
                     search in fish["name"].lower() or 
                     search in fish.get("en","").lower() or 
                     search in fish["desc"].lower()]
    
    for fish in filtered_fish:
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(fish["img"], use_column_width=True)
            with col2:
                st.subheader(f"{fish['name']} ({fish.get('en', '')})")
                st.caption(f"深度：{fish['depth']}")
                st.write(fish["desc"])
                
                # 喜歡按鈕 + 分享
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("❤️", key=f"like_{fish['name']}"):
                        st.success("已加入收藏！")
                with col_b:
                    if st.button("🔗 分享", key=f"share_{fish['name']}"):
                        st.code(f"https://你的網站網址/fish/{fish['name']}", language=None)

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
            
            new_fish = {
                "name": name,
                "en": "",
                "depth": "未知",
                "desc": desc or "社群分享照片",
                "img": file_path
            }
            fish_data.append(new_fish)
            save_data(fish_data)
            
            st.success(f"✅ {name} 的照片上傳成功！")
            st.balloons()
        else:
            st.error("請填寫名稱並上傳照片")

# ==================== 關於我們 ====================
elif page == "ℹ️ 關於我們":
    st.title("關於深海奇蹟")
    st.write("這個網站使用 Python + Streamlit 開發")
    st.write("目的是讓更多人認識深海生態，珍惜我們的海洋。")
    st.info("💡 你也可以上傳照片一起豐富這個圖鑑！")

st.caption("🌊 深海探索 永不止步 | 目前版本已加入喜歡與分享功能")