import streamlit as st
import pandas as pd
from PIL import Image
import json
import os
from datetime import datetime

st.set_page_config(page_title="深海奇蹟", page_icon="🌊", layout="wide")

# 建立資料夾
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# 載入魚類資料
def load_fish_data():
    try:
        with open("fish_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

fish_list = load_fish_data()

st.title("🌊 深海奇蹟 - 深海魚類探索")
st.markdown("### 認識神秘的深海世界")

# 側邊欄導航
page = st.sidebar.selectbox("選擇頁面", 
    ["🏠 首頁", "🐟 魚類圖鑑", "📸 照片上傳", "📊 資料庫"])

# ==================== 首頁 ====================
if page == "🏠 首頁":
    st.image("https://picsum.photos/id/1015/1200/500", use_column_width=True)
    st.header("歡迎來到深海世界")
    st.write("這裡有各種神奇的深海魚類介紹、照片分享與知識學習！")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("已收錄魚種", len(fish_list) or 12)
    with col2:
        st.metric("深度範圍", "200 - 4000 米")
    with col3:
        st.metric("探索者", "你也是其中之一！")

# ==================== 魚類圖鑑 ====================
elif page == "🐟 魚類圖鑑":
    st.header("深海魚類圖鑑")
    
    # 搜尋
    search = st.text_input("🔍 搜尋魚類名稱")
    
    for fish in fish_list:
        if search.lower() in fish.get("name", "").lower():
            with st.expander(f"🐟 {fish['name']} ({fish.get('english', '')})"):
                col1, col2 = st.columns([1,2])
                with col1:
                    if fish.get("image"):
                        st.image(fish["image"], use_column_width=True)
                with col2:
                    st.write(f"**深度**：{fish.get('depth', '未知')}")
                    st.write(f"**特徵**：{fish.get('feature', '')}")
                    st.write(f"**介紹**：{fish.get('desc', '')}")

# ==================== 照片上傳 ====================
elif page == "📸 照片上傳":
    st.header("上傳你的深海魚照片")
    
    name = st.text_input("魚類名稱")
    uploaded_file = st.file_uploader("上傳照片", type=["jpg", "png", "jpeg"])
    
    if st.button("上傳並儲存"):
        if uploaded_file and name:
            # 儲存照片
            file_path = os.path.join("uploads", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 加入資料
            new_fish = {
                "name": name,
                "english": "",
                "depth": "未知",
                "feature": "使用者上傳",
                "desc": "社群分享照片",
                "image": file_path,
                "upload_time": datetime.now().strftime("%Y-%m-%d")
            }
            fish_list.append(new_fish)
            
            # 儲存到 json
            with open("fish_data.json", "w", encoding="utf-8") as f:
                json.dump(fish_list, f, ensure_ascii=False, indent=2)
            
            st.success(f"✅ {name} 的照片上傳成功！")
        else:
            st.error("請填寫名稱並上傳照片")

# ==================== 資料庫 ====================
elif page == "📊 資料庫":
    st.header("魚類資料庫")
    if fish_list:
        df = pd.DataFrame(fish_list)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("目前還沒有資料，快去上傳吧！")

st.sidebar.info("💡 這是使用 Streamlit 開發的互動式網站")