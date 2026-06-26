import streamlit as st
import requests

# ---------------------------
# 1) Page settings
# ---------------------------
st.set_page_config(page_title="🎟️ Event Ticketing Assistant", layout="centered")


# ---------------------------
# 2) Language dictionary
# ---------------------------
TEXTS = {
    "en": {
        "title": "🎟️ Event Ticketing Assistant (RAG Prototype)",
        "ask_label": "💬 Ask something about tickets or events (e.g., Can I refund my ticket?)",
        "city_label": "📍 Your city (optional)",
        "tags_label": "🎧 Your interests / tags (comma separated, optional)",
        "ask_button": "Ask",
        "debug_title": "📌 Retrieval details (debug)",
        "tip_query": "💡 Tip: Try asking things like `Any EDM shows in Hong Kong?` or `Rock concerts in Tokyo?`",
        "tip_rebuild": "Tip: if you modify FAQ / Policy / Events, run `python ingest.py` again to rebuild the index.",
        # Web3 部分
        "wallet_section": "👜 Web3 Wallet",
        "wallet_mode_label": "Language mode",
        "wallet_connect_label": "Wallet (mock address)",
        "wallet_connect_btn": "Connect wallet",
        "wallet_disconnect_btn": "Disconnect",
        "wallet_connected": "Connected wallet",
        "wallet_not_connected": "No wallet connected. Connect to view your Web3 tickets.",
        "wallet_tickets_section": "🎫 My Web3 Tickets (Mock)",
        "wallet_fetch_error": "Failed to fetch tickets from backend",
        # Admin
        "admin_section": "🛠 Admin",
        "admin_reload_button": "Reload events.csv",
        "admin_reload_ok": "Reloaded events. Total rows: ",
        "admin_reload_fail": "Failed to reload events",
    },
    "zh": {
        "title": "🎟️ 演出售票助手（RAG 原型）",
        "ask_label": "💬 请输入与门票/演出相关的问题（例如：购票后可以退票吗？）",
        "city_label": "📍 你的城市（可选）",
        "tags_label": "🎧 你的兴趣标签（用逗号分隔，可选）",
        "ask_button": "发送",
        "debug_title": "📌 检索细节（调试）",
        "tip_query": "💡 示例：试试问 `香港有什么EDM演出？` 或 `东京有哪些rock演出？`",
        "tip_rebuild": "提示：如果你修改了 FAQ / Policy / Events，请运行 `python ingest.py` 重新构建索引。",
        # Web3 部分
        "wallet_section": "👜 Web3 钱包",
        "wallet_mode_label": "语言模式",
        "wallet_connect_label": "钱包地址（模拟）",
        "wallet_connect_btn": "连接钱包",
        "wallet_disconnect_btn": "断开连接",
        "wallet_connected": "已连接钱包",
        "wallet_not_connected": "当前未连接钱包。连接后可以查看你的 Web3 票。",
        "wallet_tickets_section": "🎫 我的 Web3 票（示例数据）",
        "wallet_fetch_error": "从后端获取票务数据失败",
        # Admin
        "admin_section": "🛠 管理员",
        "admin_reload_button": "重新加载 events.csv",
        "admin_reload_ok": "已重新加载 events，当前行数：",
        "admin_reload_fail": "重新加载 events 失败",
    },
}


def t(key: str) -> str:
    """Translate UI text based on session language."""
    lang = st.session_state.get("lang", "en")
    return TEXTS.get(lang, TEXTS["en"]).get(key, key)


# ---------------------------
# 3) Session state init
# ---------------------------
if "lang" not in st.session_state:
    st.session_state["lang"] = "en"  # default
if "wallet_address" not in st.session_state:
    st.session_state["wallet_address"] = ""
if "wallet_connected" not in st.session_state:
    st.session_state["wallet_connected"] = False


# ---------------------------
# 4) Sidebar: language + wallet + admin
# ---------------------------
with st.sidebar:
    # 语言模式
    st.markdown("### 🌐 Language")
    mode = st.radio(
        t("wallet_mode_label"),
        ["Auto", "English", "中文"],
        index=0
    )

    if mode == "English":
        st.session_state["lang"] = "en"
    elif mode == "中文":
        st.session_state["lang"] = "zh"
    # Auto 模式下，后端检测语言时可以覆盖 lang

    # Web3 钱包区
    st.markdown("---")
    st.markdown(f"### {t('wallet_section')}")

    wallet_input = st.text_input(
        t("wallet_connect_label"),
        value=st.session_state.get("wallet_address", ""),
        placeholder="0x1234... (mock address)",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("wallet_connect_btn")):
            if wallet_input.strip():
                st.session_state["wallet_address"] = wallet_input.strip()
                st.session_state["wallet_connected"] = True
    with col2:
        if st.button(t("wallet_disconnect_btn")):
            st.session_state["wallet_address"] = ""
            st.session_state["wallet_connected"] = False

    if st.session_state["wallet_connected"]:
        st.success(f"{t('wallet_connected')}: {st.session_state['wallet_address']}")
    else:
        st.info(t("wallet_not_connected"))

    # Admin tools
    st.markdown("---")
    st.markdown(f"### {t('admin_section')}")

    if st.button(t("admin_reload_button")):
        try:
            resp = requests.post("http://127.0.0.1:8000/admin/reload_events", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"{t('admin_reload_ok')}{data.get('rows')}")
            else:
                st.error(f"{t('admin_reload_fail')} (HTTP {resp.status_code})")
                st.text(f"Raw response:\n{resp.text}")
        except Exception as e:
            st.error(f"{t('admin_reload_fail')}: {e}")


# ---------------------------
# 5) Main QA UI
# ---------------------------
st.title(t("title"))

q = st.text_input(t("ask_label"))
city = st.text_input(t("city_label"), "Hong Kong")
tags = st.text_input(t("tags_label"), "rock,indie")


if st.button(t("ask_button")):
    payload = {
        "question": q,
        "context": {
            "city": city,
            "liked_tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
            "wallet_address": st.session_state.get("wallet_address") or None,
        },
    }

    try:
        r = requests.post("http://127.0.0.1:8000/ask", json=payload, timeout=30)

        if r.status_code != 200:
            st.error(f"Backend returned status code: {r.status_code}")
            st.text(f"Raw response:\n{r.text}")
        else:
            try:
                data = r.json()
            except Exception as e:
                st.error(f"Failed to parse JSON: {e}")
                st.text(f"Raw response:\n{r.text}")
            else:
                backend_lang = data.get("lang")
                if mode == "Auto" and backend_lang in ("en", "zh"):
                    st.session_state["lang"] = backend_lang

                st.subheader("🤖 Answer")
                st.markdown(data.get("answer", ""))

                with st.expander(t("debug_title")):
                    st.write("Citations:", data.get("citations"))
                    st.write("Similarity scores:", data.get("scores"))
                    if "intent" in data:
                        st.write("Intent:", data["intent"])
                    st.write("Language (backend detected):", backend_lang)

    except Exception as e:
        st.error(f"Request failed: {e}")


# ---------------------------
# 6) Web3 Tickets Section
# ---------------------------
st.markdown("---")
st.markdown(f"## {t('wallet_tickets_section')}")

if st.session_state["wallet_connected"] and st.session_state["wallet_address"]:
    addr = st.session_state["wallet_address"]
    try:
        resp = requests.get(f"http://127.0.0.1:8000/wallet/{addr}/tickets", timeout=10)
        if resp.status_code != 200:
            st.error(f"{t('wallet_fetch_error')}: HTTP {resp.status_code}")
            st.text(f"Raw response:\n{resp.text}")
        else:
            data = resp.json()
            tickets = data.get("tickets", [])
            if not tickets:
                st.info("No tickets found for this wallet.")
            else:
                for tk in tickets:
                    with st.container():
                        st.markdown(f"**{tk['title']}**  ·  `{tk['nft_id']}`")
                        st.write(f"Artist: {tk['artist']} | Genre: {tk['genre']} | City: {tk['city']}")
                        st.write(f"Date: {tk['start_time']}")
                        st.write(f"Desc: {tk['desc']}")
                        st.caption(
                            f"{tk['chain']} · {tk['token_standard']} · "
                            f"Contract: `{tk['contract_address']}` · Status: {tk['status']}"
                        )
                        st.markdown("---")
    except Exception as e:
        st.error(f"{t('wallet_fetch_error')}: {e}")
else:
    st.info(t("wallet_not_connected"))


# ---------------------------
# 7) Footer tips
# ---------------------------
st.markdown(t("tip_query"))
st.caption(t("tip_rebuild"))
