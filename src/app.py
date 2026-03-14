"""
AI Web Scraper — Streamlit Frontend
Run: streamlit run src/app.py
"""

import sys
import os
import json
import subprocess

# Install Playwright browsers at runtime (required on Streamlit Cloud)
subprocess.run(["playwright", "install", "chromium"], check=False)



# Path setup — same as scrape.py
_src = os.path.dirname(os.path.abspath(__file__))
for _sub in ("agents", "extractors", "scrapers", "pipeline"):
    sys.path.insert(0, os.path.join(_src, _sub))
sys.path.insert(0, _src)

import streamlit as st
import pandas as pd

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Web Scraper",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0f1117; }
    .metric-card {
        background: #1e2130;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #4f8ef7;
    }
    .status-success { color: #4caf50; font-weight: 600; }
    .status-skip    { color: #ff9800; font-weight: 600; }
    .status-error   { color: #f44336; font-weight: 600; }
    .url-chip {
        background: #1e2130;
        border-radius: 6px;
        padding: 6px 12px;
        margin: 4px 0;
        font-size: 13px;
        word-break: break-all;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    st.divider()

    output_format = st.selectbox(
        "Output Format",
        ["json", "csv", "excel", "all"],
        index=0
    )

    use_vision = st.toggle("Vision AI (GPT-4o)", value=False,
                           help="Uses screenshot + GPT-4o to generate CSS selectors. Slower.")

    use_ai_cleaning = st.toggle("AI Cleaning", value=True,
                                help="Uses GPT-3.5 to validate and clean scraped items.")

    st.divider()
    st.caption("Output saved to `src/output/`")
    st.caption("Logs at `src/logs/scraper.log`")

    # Show load_url.json if it exists
    load_url_path = os.path.join(_src, "output", "load_url.json")
    if os.path.exists(load_url_path):
        st.divider()
        st.markdown("**Last Search URLs**")
        with open(load_url_path, encoding='utf-8') as f:
            lu = json.load(f)
        st.caption(f"Query: {lu.get('search_query', '')}")
        for u in lu.get("urls", [])[:5]:
            st.markdown(
                f'<div class="url-chip">#{u["rank"]} {u["title"][:50]}<br>'
                f'<a href="{u["url"]}" target="_blank" style="color:#4f8ef7;font-size:11px">'
                f'{u["url"][:60]}...</a></div>',
                unsafe_allow_html=True
            )


# ── Main area ─────────────────────────────────────────────────────────────────
st.title("🤖 AI Web Scraper")
st.caption("Enter a natural language prompt. The agent searches, visits websites, skips login pages, and extracts content.")

col1, col2 = st.columns([3, 1])
with col1:
    prompt = st.text_input(
        "What do you want to scrape?",
        placeholder="e.g. top 10 blogs on digital marketing strategies",
        label_visibility="collapsed"
    )
with col2:
    url_input = st.text_input(
        "URL (optional)",
        placeholder="https://... (leave empty to auto-search)",
        label_visibility="collapsed"
    )

run_btn = st.button("🚀 Start Scraping", type="primary", use_container_width=True,
                    disabled=not prompt.strip())

# ── Run scraper ───────────────────────────────────────────────────────────────
if run_btn and prompt.strip():

    try:
        with st.spinner("Agent is working... searching, visiting URLs, extracting content..."):
            from pipeline.main_scraper import WebScraper
            scraper = WebScraper(
                use_vision=use_vision,
                use_intelligent_cleaning=use_ai_cleaning,
                output_dir=os.path.join(_src, "output")
            )
            result = scraper.scrape(
                prompt=prompt.strip(),
                url=url_input.strip() or None,
                output_format=output_format
            )
    except Exception as e:
        st.error(f"❌ {e}")
        st.stop()

    if not result.get("success"):
        st.error(f"❌ Scraping failed: {result.get('error', 'Unknown error')}")
        st.stop()

    # ── Metrics row ───────────────────────────────────────────────────────────
    meta = result.get("metadata", {})
    items = result.get("items", [])
    raw_items = result.get("raw_items", [])

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Requested", meta.get("quantity_requested", "—"))
    m2.metric("Extracted (raw)", len(raw_items))
    m3.metric("After cleaning", len(items))
    m4.metric("Content type", meta.get("content_type", "—").capitalize())

    # ── Saved files ───────────────────────────────────────────────────────────
    saved = result.get("saved_files", {})
    file_paths = []
    for stage in ("raw", "cleaned"):
        for fmt, path in (saved.get(stage) or {}).items():
            file_paths.append((stage.upper(), fmt.upper(), path))

    if file_paths:
        with st.expander("📁 Saved Files", expanded=False):
            for stage, fmt, path in file_paths:
                st.code(path, language=None)

    if result.get("load_url_json"):
        with st.expander("🔗 Search URLs (load_url.json)", expanded=False):
            try:
                with open(result["load_url_json"], encoding='utf-8') as f:
                    lu_data = json.load(f)
                st.caption(f"Query: **{lu_data.get('search_query')}** — {lu_data.get('total_results')} URLs")
                for u in lu_data.get("urls", []):
                    st.markdown(
                        f"`#{u['rank']}` [{u['title'][:70]}]({u['url']})",
                        unsafe_allow_html=False
                    )
            except Exception:
                st.code(result["load_url_json"])

    # ── Results table ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader(f"Results — {len(items)} items")

    if not items:
        st.warning("No items were collected.")
        st.stop()

    # Build display dataframe
    rows = []
    for item in items:
        rows.append({
            "Title": item.get("title", ""),
            "Description": (item.get("description") or "")[:120] + ("..." if len(item.get("description") or "") > 120 else ""),
            "Content Length": f"{len(item.get('content', ''))} chars",
            "Author": item.get("author", ""),
            "Date": item.get("date", ""),
            "URL": item.get("source_url", ""),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True,
                 column_config={
                     "URL": st.column_config.LinkColumn("URL"),
                     "Title": st.column_config.TextColumn("Title", width="large"),
                     "Description": st.column_config.TextColumn("Description", width="large"),
                 })

    # ── Detail expanders ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("Full Content")

    for i, item in enumerate(items, 1):
        title = item.get("title") or f"Item {i}"
        with st.expander(f"{i}. {title[:80]}"):
            c1, c2 = st.columns([2, 1])
            with c1:
                if item.get("description"):
                    st.caption(item["description"])
                content = item.get("content", "")
                if content:
                    st.text_area("Content", content, height=200, key=f"content_{i}",
                                 label_visibility="collapsed")
                else:
                    st.info("No content extracted.")
            with c2:
                if item.get("source_url"):
                    st.markdown(f"**Source:** [{item['source_url'][:50]}...]({item['source_url']})")
                if item.get("author"):
                    st.markdown(f"**Author:** {item['author']}")
                if item.get("date"):
                    st.markdown(f"**Date:** {item['date']}")
                st.markdown(f"**Content:** {len(content):,} chars")

    # ── Download button ───────────────────────────────────────────────────────
    st.divider()
    json_str = json.dumps(items, indent=2, ensure_ascii=False)
    st.download_button(
        label="⬇️ Download Results (JSON)",
        data=json_str,
        file_name=f"scraped_{meta.get('content_type', 'data')}.json",
        mime="application/json",
        use_container_width=True
    )
