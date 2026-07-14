import streamlit as st

st.set_page_config(page_title="深海奇蹟", page_icon="🌊", layout="wide")

st.title("🌊 深海奇蹟")
st.header("深海魚類探索")

st.write("網站正在建置中... 目前使用極簡版")

st.subheader("知名深海魚種")
col1, col2 = st.columns(2)

with col1:
    st.write("**燈籠魚 (Anglerfish)**")
    st.write("利用發光釣竿吸引獵物")

with col2:
    st.write("**鮟鱇魚 (Blobfish)**")
    st.write("外表像果凍的悲傷魚")

st.success("✅ 網站已成功運行！")