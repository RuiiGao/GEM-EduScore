"""GEM-EduScore Streamlit application.

Run with: streamlit run app.py

The app supports both a deterministic UI preview and live LLM evaluation.
"""

from __future__ import annotations

import base64
import html
import hmac
import os
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import plotly.graph_objects as go
import streamlit as st

from modules import (
    analyze_benchmark_portfolio,
    benchmark_case_options,
    build_benchmark_reference,
    compare_projects,
    DEFAULT_BENCHMARK_IDS,
    evaluate_demo_case,
    extract_document_text,
    extract_wiki_material,
    format_comparison_markdown,
    generate_comparison_docx,
    generate_comparison_pdf,
    generate_docx_report,
    generate_evaluation_report,
    generate_pdf_report,
    get_benchmark_comparison,
    get_demo_evidence_profile,
    get_improvement_roadmap,
    LLMConfig,
    LLMConfigurationError,
    LLMRequestError,
    load_prompt_bundle,
    PROVIDER_PRESETS,
    provider_for_base_url,
)
from modules.localization import OutputLanguage, localized_text


APP_DIR = Path(__file__).resolve().parent
DEMO_FILE = APP_DIR.parent / "Demo" / "JLUCP_input.md"
TUTORIAL_DIR = APP_DIR / "assets" / "tutorial"
HISTORY_LIMIT = 12

st.set_page_config(
    page_title="GEM-EduScore · Education Practice Evaluation",
    page_icon="◇",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #17233d;
            --muted: #60708c;
            --surface: #ffffff;
            --line: #e6eaf2;
            --indigo: #4f46e5;
            --violet: #7c3aed;
            --teal: #0f9f8f;
            --amber: #d97706;
        }
        .stApp {
            background:
                radial-gradient(circle at 92% -4%, rgba(124,58,237,.15), transparent 31rem),
                radial-gradient(circle at -3% 34%, rgba(20,184,166,.11), transparent 27rem),
                linear-gradient(135deg, rgba(255,255,255,.7), rgba(247,248,252,.9)),
                #f7f8fc;
            color: var(--ink);
            isolation: isolate;
        }
        .stApp::before {
            content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
            background-image:
                linear-gradient(rgba(99,102,241,.026) 1px, transparent 1px),
                linear-gradient(90deg, rgba(99,102,241,.026) 1px, transparent 1px);
            background-size: 46px 46px;
            mask-image: linear-gradient(to bottom, black, transparent 78%);
        }
        .stApp::after {
            content: ""; position: fixed; z-index: -1; pointer-events: none;
            width: 22rem; height: 22rem; right: -10rem; top: 42%; border-radius: 50%;
            border: 1px solid rgba(79,70,229,.1); box-shadow:
                0 0 0 3rem rgba(79,70,229,.025),
                0 0 0 7rem rgba(15,159,143,.018);
        }
        .block-container {
            position: relative; z-index: 1; max-width: 1240px;
            padding-top: 1.45rem; padding-bottom: 4rem;
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] { background: #f8fafc; }
        h1, h2, h3 { color: var(--ink); letter-spacing: -.025em; }
        p { color: var(--muted); }
        .brand-row { display: flex; align-items: center; gap: .7rem; margin-bottom: 1.05rem; }
        .brand-mark {
            display: grid; place-items: center; width: 2.15rem; height: 2.15rem;
            border-radius: .7rem; color: white; font-weight: 800;
            background: linear-gradient(135deg, var(--indigo), var(--violet));
            box-shadow: 0 8px 24px rgba(79,70,229,.26);
        }
        .brand-name { font-size: 1rem; font-weight: 800; color: var(--ink); }
        .brand-spacer { flex: 1; }
        .partner-logos {
            display: flex; align-items: center; gap: .5rem; margin-right: .15rem;
            padding-right: .72rem; border-right: 1px solid rgba(148,163,184,.22);
        }
        .partner-logo {
            display: grid; place-items: center; height: 2.55rem;
            padding: .22rem; border: 1px solid rgba(148,163,184,.3); border-radius: .8rem;
            background: rgba(255,255,255,.76); box-shadow: 0 7px 20px rgba(42,55,92,.06);
            opacity: .86; backdrop-filter: blur(9px); overflow: hidden;
        }
        .partner-logo:first-child { width: 2.55rem; border-radius: 50%; padding: .12rem; }
        .partner-logo:nth-child(2) { width: 3.55rem; padding: .22rem .32rem; }
        .partner-logo img { display: block; max-width: 100%; max-height: 100%; object-fit: contain; }
        .partner-logo:hover { opacity: 1; transform: translateY(-1px); transition: .18s ease; }
        .version-pill {
            padding: .35rem .65rem; border-radius: 999px;
            background: #eef2ff; color: #4338ca; font-size: .72rem; font-weight: 750;
        }
        .hero {
            position: relative; overflow: hidden; isolation: isolate;
            padding: clamp(2rem, 4vw, 3.4rem); margin: .35rem 0 1.35rem;
            border: 1px solid rgba(213,219,239,.92); border-radius: 1.8rem;
            background:
                linear-gradient(135deg, rgba(255,255,255,.96), rgba(244,246,255,.88) 54%, rgba(239,253,250,.76));
            box-shadow: 0 28px 80px rgba(57,65,112,.105), inset 0 1px 0 rgba(255,255,255,.95);
        }
        .hero::before {
            content: ""; position: absolute; inset: 0; z-index: -2; pointer-events: none;
            background-image:
                linear-gradient(rgba(79,70,229,.032) 1px, transparent 1px),
                linear-gradient(90deg, rgba(79,70,229,.032) 1px, transparent 1px);
            background-size: 34px 34px;
            mask-image: linear-gradient(100deg, black 0%, rgba(0,0,0,.35) 58%, transparent 90%);
        }
        .hero::after {
            content: ""; position: absolute; z-index: -1; pointer-events: none;
            width: 23rem; height: 23rem; right: -8rem; top: -9rem; border-radius: 50%;
            background: radial-gradient(circle at 38% 42%, rgba(129,140,248,.24), rgba(124,58,237,.08) 42%, transparent 70%);
            border: 1px solid rgba(99,102,241,.13);
        }
        .hero-content { position: relative; z-index: 2; max-width: 1040px; }
        .eyebrow {
            display: inline-flex; align-items: center; gap: .45rem; color: #4338ca;
            background: #eef2ff; border: 1px solid #dfe3ff; border-radius: 999px;
            padding: .42rem .72rem; font-size: .75rem; font-weight: 750;
            letter-spacing: .025em; text-transform: uppercase;
        }
        .hero h1 {
            display: flex; flex-direction: column; align-items: flex-start;
            font-family: "Arial Black", "Microsoft YaHei UI", "PingFang SC", "Noto Sans SC", sans-serif;
            font-size: clamp(2.55rem, 4.05vw, 4.05rem); line-height: 1.06; max-width: 1080px;
            margin: 1rem 0 .55rem !important; padding: 0 !important;
            letter-spacing: -.045em; font-weight: 900;
            text-wrap: balance; text-shadow: 0 1px 0 rgba(255,255,255,.9);
        }
        .hero-line { display: block; white-space: nowrap; }
        .gradient-word {
            position: relative; display: inline-block; color: #4f46e5;
            background: none; -webkit-text-fill-color: currentColor;
            text-shadow: 0 10px 28px rgba(79,70,229,.13);
        }
        .gradient-word::after {
            content: ""; position: absolute; left: .02em; right: .01em; bottom: -.1em;
            height: .075em; min-height: 3px; border-radius: 999px;
            background: linear-gradient(90deg, #4f46e5, #7c3aed 58%, #0f9f8f); opacity: .8;
        }
        .hero-copy { max-width: 850px; font-size: 1.02rem; line-height: 1.68; margin: 0; }
        .hero-orbit {
            position: absolute; z-index: 1; right: 2.2rem; bottom: 1.7rem;
            width: 7.6rem; height: 7.6rem; opacity: .68; pointer-events: none;
        }
        .hero-orbit::before, .hero-orbit::after {
            content: ""; position: absolute; inset: 0; border-radius: 50%;
            border: 1px solid rgba(79,70,229,.24);
        }
        .hero-orbit::after { inset: 1.25rem; border-color: rgba(15,159,143,.3); }
        .hero-orbit-core {
            position: absolute; inset: 2.7rem; border-radius: 50%;
            background: linear-gradient(135deg, var(--indigo), var(--teal));
            box-shadow: 0 0 0 .55rem rgba(99,102,241,.08), 0 10px 28px rgba(79,70,229,.2);
        }
        .hero-orbit-dot {
            position: absolute; width: .62rem; height: .62rem; border-radius: 50%;
            background: #7c3aed; box-shadow: 0 0 0 .28rem rgba(124,58,237,.1);
        }
        .hero-orbit-dot.one { left: .3rem; top: 3.15rem; }
        .hero-orbit-dot.two { right: .55rem; top: 1.25rem; background: #0f9f8f; }
        .hero-orbit-dot.three { right: 1.45rem; bottom: .45rem; background: #6366f1; }
        .process-row { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1.45rem; }
        .process-step {
            background: rgba(255,255,255,.8); border: 1px solid var(--line); color: #475569;
            border-radius: .65rem; padding: .48rem .7rem; font-size: .76rem; font-weight: 650;
        }
        .process-arrow { color: #a5b4fc; align-self: center; }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            position: relative; overflow: hidden;
            background: linear-gradient(145deg, rgba(255,255,255,.76), rgba(248,250,255,.58));
            border-color: rgba(203,213,232,.72) !important; border-radius: 1.15rem;
            box-shadow: 0 22px 65px rgba(42,55,92,.07), inset 0 1px 0 rgba(255,255,255,.92);
            backdrop-filter: blur(20px) saturate(125%);
        }
        label[data-testid="stWidgetLabel"] p {
            color: #53627c; font-weight: 650; letter-spacing: -.01em;
        }
        [data-baseweb="input"] > div, [data-baseweb="select"] > div {
            border-radius: .76rem !important; border-color: rgba(209,217,233,.82) !important;
            background: rgba(255,255,255,.72); box-shadow: inset 0 1px 0 rgba(255,255,255,.82);
            backdrop-filter: blur(12px);
        }
        .section-kicker { color: #4f46e5; font-weight: 800; font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; }
        .section-title { font-weight: 800; font-size: 1.55rem; color: var(--ink); margin: .15rem 0 .3rem; }
        .section-copy { font-size: .9rem; margin-bottom: 1.1rem; }
        .format-row { display:flex; flex-wrap:wrap; gap:.42rem; margin:-.2rem 0 1rem; }
        .format-chip {
            padding:.28rem .52rem; border-radius:.5rem; background:rgba(242,245,251,.72);
            border:1px solid rgba(218,226,240,.8); color:#62718a; font-size:.68rem; font-weight:750;
        }
        .trust-box {
            min-height: 100%; padding: 1.15rem; border-radius: .9rem;
            background: linear-gradient(145deg, rgba(238,242,255,.68), rgba(240,253,250,.52));
            border: 1px solid rgba(211,222,246,.78); box-shadow: inset 0 1px 0 rgba(255,255,255,.78);
            backdrop-filter: blur(16px) saturate(120%);
        }
        .trust-box strong { display: block; color: var(--ink); margin-bottom: .5rem; }
        .trust-item { color: #52617a; font-size: .82rem; margin: .65rem 0; }
        .notice {
            padding: .9rem 1rem; border: 1px solid #c7d2fe; background: #eef2ff;
            color: #3730a3; border-radius: .8rem; font-size: .84rem; margin: 1rem 0 1.4rem;
        }
        .notice strong { color: #312e81; }
        .result-head { margin: 2.5rem 0 1rem; }
        .result-head h2 { font-size: 2rem; margin: .2rem 0 .45rem; }
        .score-card {
            padding: 1.2rem 1.25rem; border-radius: .95rem; min-height: 142px;
            border: 1px solid rgba(211,219,235,.78); background: rgba(255,255,255,.7);
            box-shadow: 0 16px 38px rgba(42,55,92,.055), inset 0 1px 0 rgba(255,255,255,.9);
            backdrop-filter: blur(16px) saturate(120%);
        }
        .score-label { color: #6b7890; font-size: .76rem; font-weight: 750; text-transform: uppercase; letter-spacing: .055em; }
        .score-value { color: var(--ink); font-size: 2.45rem; line-height: 1.15; font-weight: 850; margin: .45rem 0 .25rem; letter-spacing: -.05em; }
        .score-value small { font-size: .9rem; color: #8490a5; letter-spacing: 0; }
        .score-note { color: #758198; font-size: .76rem; line-height: 1.4; }
        .score-accent-indigo { border-top: 3px solid #6366f1; }
        .score-accent-teal { border-top: 3px solid #14b8a6; }
        .score-accent-amber { border-top: 3px solid #f59e0b; }
        .score-accent-slate { border-top: 3px solid #94a3b8; }
        .evidence-card {
            padding: 1rem; border-radius: .8rem; background: #fbfcfe;
            border: 1px solid var(--line); margin-bottom: .75rem;
        }
        .evidence-card strong { color: var(--ink); font-size: .91rem; }
        .evidence-card p { margin: .4rem 0; font-size: .83rem; line-height: 1.55; }
        .quote { color: #68758d; font-size: .76rem; border-left: 2px solid #a5b4fc; padding-left: .65rem; }
        .source-link { margin-top:.55rem; font-size:.72rem; font-weight:700; }
        .source-link a { color:#4f46e5; text-decoration:none; }
        .gap-item {
            display: flex; gap: .65rem; align-items: flex-start; padding: .72rem .8rem;
            border-radius: .7rem; background: #fff7ed; border: 1px solid #ffedd5;
            color: #7c4a16; font-size: .82rem; margin-bottom: .55rem;
        }
        .gap-dot { width: .45rem; height: .45rem; border-radius: 50%; background: #f59e0b; margin-top: .35rem; flex: none; }
        .benchmark-chip {
            display: inline-block; margin: .2rem .25rem .2rem 0; padding: .4rem .6rem;
            background: #f0fdfa; color: #0f766e; border: 1px solid #ccfbf1;
            border-radius: 999px; font-size: .74rem; font-weight: 650;
        }
        .roadmap-stage { font-size: .72rem; font-weight: 850; letter-spacing: .06em; text-transform: uppercase; }
        .roadmap-time { color: #8290a6; font-size: .75rem; margin-left: .3rem; }
        .roadmap-title { font-weight: 800; font-size: 1.03rem; color: var(--ink); margin: .55rem 0 .8rem; }
        .live-badge {
            display: inline-flex; align-items: center; gap: .4rem; padding: .35rem .62rem;
            border-radius: 999px; background: #ecfdf5; color: #047857;
            border: 1px solid #a7f3d0; font-size: .72rem; font-weight: 800;
        }
        .live-dot { width: .45rem; height: .45rem; border-radius: 50%; background: #10b981; }
        .report-shell {
            background: rgba(255,255,255,.7); border: 1px solid rgba(211,219,235,.78); border-radius: 1rem;
            padding: clamp(1.1rem, 3vw, 2.2rem); margin-top: .8rem;
            box-shadow: 0 18px 48px rgba(42,55,92,.06), inset 0 1px 0 rgba(255,255,255,.9);
            backdrop-filter: blur(18px) saturate(120%);
        }
        .history-card {
            padding: .72rem .78rem; margin: .4rem 0 .55rem; border-radius: .78rem;
            border: 1px solid rgba(211,219,235,.78);
            background: linear-gradient(145deg, rgba(255,255,255,.82), rgba(246,248,255,.62));
            box-shadow: inset 0 1px 0 rgba(255,255,255,.9);
        }
        .history-type {
            color: #4f46e5; font-size: .66rem; font-weight: 820; letter-spacing: .055em;
            text-transform: uppercase;
        }
        .history-title { color: var(--ink); font-size: .88rem; font-weight: 780; margin: .18rem 0 .08rem; }
        .history-meta { color: #8490a5; font-size: .7rem; line-height: 1.4; }
        .tutorial-intro {
            display: flex; flex-direction: column; gap: .25rem; margin: -.2rem 0 1rem;
            padding: .85rem 1rem; border-radius: .85rem;
            border: 1px solid rgba(199,210,254,.72);
            background: linear-gradient(135deg, rgba(238,242,255,.72), rgba(240,253,250,.5));
        }
        .tutorial-intro strong { color: var(--ink); font-size: 1rem; }
        .tutorial-intro span { color: #718096; font-size: .8rem; line-height: 1.5; }
        div[data-testid="stPopover"] > button {
            background: rgba(255,255,255,.66); border-color: rgba(203,213,232,.78);
            backdrop-filter: blur(14px); font-weight: 720;
        }
        .footer-note { text-align: center; color: #8a96aa; font-size: .74rem; margin-top: 2.5rem; }
        .stButton > button[kind="primary"] {
            background: linear-gradient(100deg, #4f46e5, #7c3aed); border: none;
            box-shadow: 0 8px 22px rgba(79,70,229,.23); font-weight: 750; color: white !important;
        }
        .stButton > button[kind="primary"] p { color: white !important; }
        .stButton > button { border-radius: .7rem; }
        div[data-testid="stButton"] button[kind="secondary"] {
            border-color: #d7ddea; background: rgba(255,255,255,.78);
            color: #53627c; font-weight: 720; backdrop-filter: blur(8px);
        }
        div[data-testid="stButton"] button[kind="secondary"]:hover {
            border-color: #a5b4fc; color: #3730a3; background: #f7f7ff;
        }
        .st-key-open_tutorial_video button {
            border: 0 !important; color: white !important;
            background: linear-gradient(110deg, #4338ca, #6366f1 58%, #7c3aed) !important;
            box-shadow: 0 11px 26px rgba(79,70,229,.24), inset 0 1px 0 rgba(255,255,255,.2);
            font-weight: 800 !important; letter-spacing: .01em;
        }
        .st-key-open_tutorial_video button p,
        .st-key-open_tutorial_video button span { color: white !important; }
        .st-key-open_tutorial_video button:hover {
            color: white !important; background: linear-gradient(110deg, #3730a3, #4f46e5 58%, #6d28d9) !important;
            box-shadow: 0 13px 30px rgba(79,70,229,.3), inset 0 1px 0 rgba(255,255,255,.22);
            transform: translateY(-1px);
        }
        .st-key-reset_single_evaluation button, .st-key-reset_comparison_evaluation button {
            border-color: #fecaca !important; color: #b42318 !important;
            background: rgba(255,250,250,.9) !important;
            box-shadow: 0 7px 18px rgba(180,35,24,.06);
        }
        .st-key-reset_single_evaluation button:hover, .st-key-reset_comparison_evaluation button:hover {
            border-color: #f87171 !important; color: #991b1b !important;
            background: #fff1f2 !important;
        }
        [data-testid="stFileUploaderDropzone"] { background: #fafbff; border-color: #d9def0; border-radius: .8rem; }
        [data-baseweb="tab-list"] { gap: .35rem; }
        [data-baseweb="tab"] { border-radius: .6rem; padding: .55rem .85rem; }
        hr { border-color: var(--line); }
        @media (max-width: 900px) {
            .hero-line { white-space: normal; }
            .hero h1 { max-width: 760px; }
            .hero-orbit { opacity: .3; right: -1.5rem; bottom: -1.5rem; }
        }
        @media (max-width: 700px) {
            .block-container { padding-top: 1rem; }
            .hero { padding-bottom: 1.6rem; }
            .hero h1 { font-size: clamp(2.25rem, 11vw, 3rem); line-height: 1.12; letter-spacing: -.045em; }
            .hero-copy { line-height: 1.62; }
            .process-arrow { display: none; }
            .brand-row { margin-bottom: 1rem; flex-wrap: wrap; }
            .version-pill { font-size: .62rem; }
            .partner-logos {
                order: 3; width: 100%; justify-content: flex-end; margin: -.2rem 0 0;
                padding: 0; border: 0;
            }
            .partner-logo { height: 2.15rem; }
            .partner-logo:first-child { width: 2.15rem; }
            .partner-logo:nth-child(2) { width: 3.15rem; }
            .partner-logos { gap: .35rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _corner_logo_data() -> list[tuple[str, str]]:
    """Return optional user-supplied corner logos as embedded data URIs."""
    logo_dir = APP_DIR / "assets" / "brand"
    results: list[tuple[str, str]] = []
    mime_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".svg": "image/svg+xml"}
    for index, label in ((1, "JLU-CP Computer Science & Public Health"), (2, "iGEM")):
        for suffix, mime_type in mime_types.items():
            path = logo_dir / f"corner-logo-{index}{suffix}"
            if not path.exists():
                continue
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            results.append((label, f"data:{mime_type};base64,{encoded}"))
            break
    return results


def tutorial_video_path() -> Path | None:
    """Return the first supported tutorial video bundled with the deployment."""
    for filename in ("tutorial-web.mp4", "tutorial.mp4", "tutorial.webm", "tutorial.m4v"):
        path = TUTORIAL_DIR / filename
        if path.is_file():
            return path
    return None


@st.dialog("GEM-EduScore 使用教程", width="large")
def render_tutorial_dialog() -> None:
    """Show the tutorial in a seekable native video player."""
    st.markdown(
        '<div class="tutorial-intro"><strong>从材料输入到评估报告</strong>'
        '<span>跟随视频快速了解文件、Wiki、基准比较与报告下载。</span></div>',
        unsafe_allow_html=True,
    )
    video_path = tutorial_video_path()
    if video_path is None:
        st.info("教程播放器已经就绪。请将网页优化版视频命名为 tutorial-web.mp4，并放入 assets/tutorial/ 目录。")
        st.caption("推荐使用 MP4（H.264 视频 + AAC 音频），以获得最稳定的浏览器兼容性。")
        return
    video_format = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".m4v": "video/mp4",
    }[video_path.suffix.lower()]
    st.video(str(video_path), format=video_format, autoplay=False, loop=False, width="stretch")
    st.caption("可使用播放器控制栏播放、暂停、调节音量、全屏，并拖动时间轴调整播放进度。")


def render_brand() -> None:
    logo_html = "".join(
        f'<span class="partner-logo" title="{html.escape(label)}"><img src="{uri}" alt="{html.escape(label)}"></span>'
        for label, uri in _corner_logo_data()
    )
    st.markdown(
        f"""
        <div class="brand-row">
            <div class="brand-mark">G</div>
            <div class="brand-name">GEM-EduScore</div>
            <div class="brand-spacer"></div>
            <div class="partner-logos">{logo_html}</div>
            <div class="version-pill">iGEM SHOWCASE · V0.11.0</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <section class="hero">
            <div class="hero-content">
                <div class="eyebrow">◇ iGEM Education Intelligence · Project Showcase</div>
                <h1>
                    <span class="hero-line">让教育实践从“活动描述”</span>
                    <span class="hero-line">走向 <span class="gradient-word">证据驱动的持续改进</span></span>
                </h1>
                <p class="hero-copy">
                    面向 iGEM 团队的证据驱动教育实践评估平台：理解设计质量、发现证据缺口，
                    从优秀案例中提取可复用的改进路径。
                </p>
                <div class="process-row">
                    <span class="process-step">01 · 材料输入</span><span class="process-arrow">→</span>
                    <span class="process-step">02 · 证据提取</span><span class="process-arrow">→</span>
                    <span class="process-step">03 · 十维评价</span><span class="process-arrow">→</span>
                    <span class="process-step">04 · 基准比较</span><span class="process-arrow">→</span>
                    <span class="process-step">05 · 项目对比</span><span class="process-arrow">→</span>
                    <span class="process-step">06 · 改进路线</span>
                </div>
            </div>
            <div class="hero-orbit" aria-hidden="true">
                <span class="hero-orbit-core"></span>
                <span class="hero-orbit-dot one"></span>
                <span class="hero-orbit-dot two"></span>
                <span class="hero-orbit-dot three"></span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def runtime_setting(name: str, default: str = "") -> str:
    """Read deployment secrets first, with environment-variable fallback."""
    environment_value = os.getenv(name, "").strip()
    if environment_value:
        return environment_value
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default
    return str(value).strip() if value is not None else default


def setting_is_true(name: str) -> bool:
    return runtime_setting(name).lower() in {"1", "true", "yes", "on"}


def reset_evaluation_session() -> None:
    """Clear current work while preserving managed quota usage and session history."""
    managed_count = st.session_state.get("managed_analysis_count")
    history = st.session_state.get("evaluation_history", [])
    for key in list(st.session_state):
        del st.session_state[key]
    if managed_count is not None:
        st.session_state["managed_analysis_count"] = managed_count
    if history:
        st.session_state["evaluation_history"] = history
    st.session_state["evaluation_reset_notice"] = True


def add_history_record(record_type: str, title: str, subtitle: str, payload: dict) -> None:
    """Keep a privacy-friendly, session-only snapshot of a completed evaluation."""
    history = list(st.session_state.get("evaluation_history", []))
    history.insert(
        0,
        {
            "id": uuid4().hex[:12],
            "type": record_type,
            "title": str(title).strip() or "Untitled evaluation",
            "subtitle": str(subtitle).strip(),
            "created_at": datetime.now().strftime("%m-%d %H:%M"),
            "payload": payload,
        },
    )
    st.session_state["evaluation_history"] = history[:HISTORY_LIMIT]


def restore_history_record(record: dict) -> None:
    """Restore one history snapshot into the active result workspace."""
    payload = record.get("payload", {})
    if record.get("type") == "comparison":
        st.session_state["analysis_workspace"] = "双项目对比分析"
        st.session_state["comparison_results"] = payload["comparison_results"]
        st.session_state["result_mode"] = "comparison"
    else:
        st.session_state["analysis_workspace"] = "单项目深度评估"
        for key in ("llm_result", "document_info", "benchmark_ids", "report_language", "demo_mode"):
            if key in payload:
                st.session_state[key] = payload[key]
        st.session_state["result_mode"] = "live"
    st.session_state["evaluation_ready"] = True
    st.session_state["history_restored_notice"] = record.get("title", "历史报告")


def render_history_popover() -> None:
    """Render compact session history with restore and remove actions."""
    history = list(st.session_state.get("evaluation_history", []))
    with st.popover(f"历史记录 · {len(history)}", width="stretch"):
        st.markdown("**评估历史**")
        st.caption(f"仅保存在当前浏览器会话中，最多保留 {HISTORY_LIMIT} 条；不会写入共享服务器磁盘。")
        if not history:
            st.info("完成一次单项目评估或双项目对比后，结果会出现在这里。")
            return
        for record in history:
            record_type = "双项目对比" if record.get("type") == "comparison" else "单项目评估"
            st.markdown(
                '<div class="history-card">'
                f'<div class="history-type">{html.escape(record_type)}</div>'
                f'<div class="history-title">{html.escape(record.get("title", "历史报告"))}</div>'
                f'<div class="history-meta">{html.escape(record.get("subtitle", ""))} · '
                f'{html.escape(record.get("created_at", ""))}</div></div>',
                unsafe_allow_html=True,
            )
            open_col, remove_col = st.columns([3, 1], gap="small")
            with open_col:
                if st.button("重新打开", key=f'history_open_{record["id"]}', width="stretch"):
                    restore_history_record(record)
                    st.rerun()
            with remove_col:
                if st.button(
                    "移除",
                    key=f'history_remove_{record["id"]}',
                    width="stretch",
                    help="仅从当前会话历史中移除，不影响已经下载的报告。",
                ):
                    st.session_state["evaluation_history"] = [
                        item for item in history if item.get("id") != record.get("id")
                    ]
                    st.rerun()
        st.divider()
        if st.button("清空全部历史", key="clear_evaluation_history", width="stretch"):
            st.session_state["evaluation_history"] = []
            st.rerun()


@st.cache_data(ttl=1800, show_spinner=False)
def cached_extract_wiki_material(
    wiki_url: str,
    crawl_related: bool,
    max_wiki_pages: int,
) -> tuple[str, dict]:
    """Reuse a successful Wiki extraction during the current showcase session."""
    return extract_wiki_material(
        wiki_url,
        crawl_related=crawl_related,
        max_pages=max_wiki_pages,
    )


@st.cache_data(show_spinner=False)
def cached_pdf_report(
    dashboard: dict,
    language: OutputLanguage,
    wiki_pages: list[dict] | None,
) -> bytes:
    """Cache deterministic PDF bytes so widget reruns stay responsive."""
    return generate_pdf_report(dashboard, language, wiki_pages)


@st.cache_data(show_spinner=False)
def cached_docx_report(
    dashboard: dict,
    language: OutputLanguage,
    wiki_pages: list[dict] | None,
) -> bytes:
    """Cache deterministic Word bytes so widget reruns stay responsive."""
    return generate_docx_report(dashboard, language, wiki_pages)


@st.cache_data(show_spinner=False)
def cached_comparison_pdf(
    comparison: dict,
    dashboard_a: dict,
    dashboard_b: dict,
    language: OutputLanguage,
    sources_a: list[dict] | None,
    sources_b: list[dict] | None,
) -> bytes:
    """Cache deterministic two-project PDF bytes."""
    return generate_comparison_pdf(comparison, dashboard_a, dashboard_b, language, sources_a, sources_b)


@st.cache_data(show_spinner=False)
def cached_comparison_docx(
    comparison: dict,
    dashboard_a: dict,
    dashboard_b: dict,
    language: OutputLanguage,
    sources_a: list[dict] | None,
    sources_b: list[dict] | None,
) -> bytes:
    """Cache deterministic two-project Word bytes."""
    return generate_comparison_docx(comparison, dashboard_a, dashboard_b, language, sources_a, sources_b)


def ui_text(zh: str, en: str, language: OutputLanguage) -> str:
    return localized_text(zh, en, language)


def render_input_panel() -> None:
    managed_mode = setting_is_true("GEM_EDUSCORE_MANAGED_API")
    environment_key = runtime_setting("OPENAI_API_KEY")
    base_url = runtime_setting("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = runtime_setting("OPENAI_MODEL", "gpt-5-mini")
    endpoint_setting = runtime_setting("OPENAI_ENDPOINT", "responses").lower()
    endpoint_label = (
        "Chat Completions（兼容模式）" if endpoint_setting == "chat_completions" else "Responses API（OpenAI 推荐）"
    )
    provider = provider_for_base_url(base_url)
    structured_output = "auto"
    max_output_tokens = 8192
    access_code_required = runtime_setting("GEM_EDUSCORE_ACCESS_CODE") if managed_mode else ""
    try:
        session_limit = max(1, int(runtime_setting("GEM_EDUSCORE_SESSION_LIMIT", "3")))
    except ValueError:
        session_limit = 3
    api_key_input = ""
    access_code_input = ""
    uploaded_files = []
    wiki_url = ""
    crawl_related = True
    max_wiki_pages = 6
    output_language: OutputLanguage = "zh"
    selected_benchmark_ids = list(DEFAULT_BENCHMARK_IDS)

    with st.container(border=True):
        left, right = st.columns([1.7, 1], gap="large")
        with left:
            st.markdown('<div class="section-kicker">Start an evaluation</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">输入 Education 证据材料</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-copy">上传教育实践材料，平台会提取正文、执行十维评价并生成可视化诊断报告。</div>',
                unsafe_allow_html=True,
            )
            source_mode = st.radio(
                "材料来源",
                ["上传文件", "分析 Wiki", "文件 + Wiki 综合分析"],
                horizontal=True,
                help="综合分析会把文件记录与 Wiki 页面作为同一次评价的独立证据来源。",
            )
            use_files = source_mode != "分析 Wiki"
            use_wiki = source_mode != "上传文件"

            if use_files:
                st.markdown(
                    '<div class="format-row">'
                    '<span class="format-chip">MD</span><span class="format-chip">TXT</span>'
                    '<span class="format-chip">WORD · DOCX</span><span class="format-chip">PDF</span>'
                    '<span class="format-chip">POWERPOINT · PPTX</span><span class="format-chip">HTML</span>'
                    '<span class="format-chip">CSV</span></div>',
                    unsafe_allow_html=True,
                )
                uploaded_files = st.file_uploader(
                    "Education material",
                    type=["md", "txt", "docx", "pdf", "pptx", "html", "htm", "csv"],
                    accept_multiple_files=True,
                    label_visibility="collapsed",
                    help="最多同时上传 5 份材料，单文件上限 20 MB。PDF 需包含可选择的文本；纯扫描件请先 OCR。",
                )

            if use_wiki:
                wiki_url = st.text_input(
                    "队伍 Wiki 或 Education 页面",
                    placeholder="https://2025.igem.wiki/team-name/education",
                    help="可以填写 Education 页面，也可以填写该队伍 Wiki 首页。",
                )
                wiki_col, page_col = st.columns([1.35, 1], gap="medium")
                with wiki_col:
                    crawl_related = st.toggle(
                        "自动发现教育相关页面",
                        value=True,
                        help="仅在同一站点、同一 iGEM 队伍路径内发现 Communication、Engagement、Outreach 等页面。",
                    )
                with page_col:
                    max_wiki_pages = st.number_input(
                        "最多读取页面",
                        min_value=1,
                        max_value=12,
                        value=6,
                        step=1,
                        disabled=not crawl_related,
                    )
                st.caption("支持静态 HTML 与常见 Vite/React Wiki；只解析公开内容，不在服务器执行网页脚本。")

            with st.container(border=True):
                st.markdown("**报告语言 / Report language**")
                language_label = st.radio(
                    "报告语言 / Report language",
                    ["中文", "English", "中英双语 / Bilingual"],
                    horizontal=True,
                    label_visibility="collapsed",
                    help="控制模型生成内容、结果界面和可下载报告的语言。证据原文保持来源语言，不自动改写。",
                    key="report_language_selector",
                )
                output_language = {
                    "中文": "zh",
                    "English": "en",
                    "中英双语 / Bilingual": "bilingual",
                }[language_label]
                st.caption(
                    "证据引文保留原文；双语模式会同时生成中文、English 和中英双语三个可下载版本。"
                )
            benchmark_options = benchmark_case_options(output_language)
            default_benchmark_labels = [
                label for label, case_id in benchmark_options.items() if case_id in DEFAULT_BENCHMARK_IDS
            ]
            selected_benchmark_labels = st.multiselect(
                "优秀教育案例基准库",
                options=list(benchmark_options),
                default=default_benchmark_labels,
                help="可同时选择多个历年优秀案例。获奖事实来自官方结果，十维画像是 GEM-EduScore 的公开证据分析值。",
            )
            selected_benchmark_ids = [benchmark_options[label] for label in selected_benchmark_labels]
            if not selected_benchmark_ids:
                st.caption("未选择案例时，将使用默认四案例组合基准。")
            use_demo = st.toggle(
                "使用内置 JLU-CP 演示材料",
                value=False,
                help="开启后可直接用项目内置材料测试真实 API 分析。",
            )

            if managed_mode:
                with st.expander("平台连接状态", expanded=False):
                    if environment_key:
                        st.success(f"平台托管模型已就绪 · {model}")
                    else:
                        st.error("平台尚未配置 API Key，请联系项目维护者。")
                    st.caption("访客无需准备项目文件、Python 环境或 API Key。")
                if access_code_required:
                    access_code_input = st.text_input(
                        "展示访问码",
                        type="password",
                        placeholder="请输入项目展示访问码",
                    )
            else:
                with st.expander("模型与 API 设置", expanded=True):
                    provider_labels = [item.label for item in PROVIDER_PRESETS]
                    provider_label = st.selectbox(
                        "API 服务提供商",
                        provider_labels,
                        index=provider_labels.index(provider.label),
                        help="预设只负责填入官方兼容地址；模型名称和地址仍可手动修改。",
                        key="api_provider_label",
                    )
                    provider = next(item for item in PROVIDER_PRESETS if item.label == provider_label)
                    st.caption(provider.description)

                    protocol_options = ["OpenAI-compatible Chat（推荐）"]
                    if provider.supports_responses:
                        protocol_options.insert(0, "OpenAI Responses（原生结构化）")
                    endpoint_label = st.selectbox(
                        "调用协议",
                        protocol_options,
                        help="非 OpenAI 服务统一使用兼容 Chat；平台会自动协商其结构化能力。",
                        key=f"endpoint_{provider.id}",
                    )

                    initial_base_url = base_url if provider.id == "custom" else provider.base_url
                    initial_model = model if provider.id == "custom" else provider.default_model
                    base_url = st.text_input(
                        "API 地址",
                        value=initial_base_url,
                        placeholder="https://api.openai.com/v1",
                        help="填写 SDK 使用的 Base URL，不要追加 /chat/completions。",
                        key=f"base_url_{provider.id}",
                    )
                    model = st.text_input(
                        "模型名称",
                        value=initial_model,
                        placeholder="输入该服务实际提供的模型 ID",
                        key=f"model_{provider.id}",
                    )
                    api_key_input = st.text_input(
                        "API Key",
                        type="password",
                        placeholder=(
                            "Ollama 本地服务可留空"
                            if provider.api_key_optional
                            else ("已从安全配置读取" if environment_key else "仅在当前会话中使用")
                        ),
                        help="仅保存在当前应用会话内，不写入项目文件。",
                        key=f"api_key_{provider.id}",
                    )
                    if environment_key and not api_key_input:
                        st.caption("✓ 已检测到安全配置中的 API Key")

                    with st.expander("高级兼容设置", expanded=False):
                        strategy_label = st.selectbox(
                            "结构化输出策略",
                            [
                                "自动协商（JSON Schema → JSON → 提示词）",
                                "优先 JSON Schema",
                                "优先 JSON Object",
                                "仅提示词约束",
                            ],
                            help="推荐自动协商。服务拒绝某种格式时会自动降级，而不是直接报错。",
                            key=f"structured_strategy_{provider.id}",
                        )
                        strategy_map = {
                            "自动协商（JSON Schema → JSON → 提示词）": "auto",
                            "优先 JSON Schema": "json_schema",
                            "优先 JSON Object": "json_object",
                            "仅提示词约束": "prompt_only",
                        }
                        structured_output = strategy_map[strategy_label]
                        max_output_tokens = st.slider(
                            "最大输出长度",
                            min_value=2048,
                            max_value=16384,
                            value=8192,
                            step=1024,
                            help="十维完整报告建议至少 8,192。输出过短是 JSON 被截断的常见原因。",
                            key=f"max_tokens_{provider.id}",
                        )
                    if provider.id == "siliconflow":
                        st.caption("已启用 SiliconFlow / Qwen3 专项适配：/v1、非思考模式、8K 输出与截断恢复。")

            action_col, preview_col, reset_col = st.columns([1.35, 1, .8], gap="small")
            with action_col:
                start = st.button("生成 AI 评估报告  →", type="primary", width="stretch")
            with preview_col:
                preview = st.button("查看界面示例", width="stretch")
            with reset_col:
                restart = st.button(
                    "停止 / 重来",
                    type="secondary",
                    icon=":material/stop_circle:",
                    help="清空当前输入和评估结果，历史记录与已计入的托管调用次数会保留。",
                    width="stretch",
                    key="reset_single_evaluation",
                )

        with right:
            st.markdown(
                """
                <div class="trust-box">
                    <strong>完整分析流程</strong>
                    <div class="trust-item">01　读取文件或队伍 Wiki 公开页面</div>
                    <div class="trust-item">02　加载 Master Prompt V1.0</div>
                    <div class="trust-item">03　附加 Rubric 与 Benchmark 参考</div>
                    <div class="trust-item">04　调用模型生成完整 Evaluation Report</div>
                    <div class="trust-item">05　在线查看并下载 Markdown / PDF / Word 报告</div>
                    <div class="trust-item">◇　No Evidence → No Claim</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if restart:
        reset_evaluation_session()
        st.rerun()

    if preview:
        st.session_state["evaluation_ready"] = True
        st.session_state["result_mode"] = "demo"
        st.session_state["demo_mode"] = True
        st.session_state["document_info"] = {"name": "JLUCP_input.md", "extension": "MD"}
        st.session_state["report_language"] = output_language
        return

    if not start:
        return

    if not use_demo:
        if use_files and not uploaded_files:
            st.warning("请至少上传一份 Education 材料。")
            return
        if use_wiki and not wiki_url.strip():
            st.warning("请填写队伍 Wiki 或 Education 页面网址。")
            return
    if not use_demo and len(uploaded_files) > 5:
        st.error("一次最多分析 5 份材料。请合并或移除部分文件后重试。")
        return

    if managed_mode:
        if access_code_required and not hmac.compare_digest(access_code_input, access_code_required):
            st.error("展示访问码不正确。")
            return
        if st.session_state.get("managed_analysis_count", 0) >= session_limit:
            st.error(f"当前会话已达到 {session_limit} 次分析上限。请刷新页面开始新会话。")
            return

    try:
        if use_demo:
            material, document_info = extract_document_text(DEMO_FILE.name, DEMO_FILE.read_bytes())
        else:
            extracted_documents = []
            document_infos = []
            if use_files:
                for uploaded_file in uploaded_files:
                    document_text, info = extract_document_text(uploaded_file.name, uploaded_file.getvalue())
                    safe_source_name = uploaded_file.name.replace("\r", " ").replace("\n", " ").replace("]", "")
                    extracted_documents.append(
                        f"[SOURCE DOCUMENT: {safe_source_name}]\n{document_text}\n[/SOURCE DOCUMENT]"
                    )
                    document_infos.append(info)
            if use_wiki:
                with st.spinner("正在读取 Wiki 正文并发现教育相关页面……"):
                    wiki_material, wiki_info = cached_extract_wiki_material(
                        wiki_url,
                        crawl_related,
                        int(max_wiki_pages) if crawl_related else 1,
                    )
                extracted_documents.append(
                    f"[WIKI EVIDENCE COLLECTION]\n{wiki_material}\n[/WIKI EVIDENCE COLLECTION]"
                )
                document_infos.append(wiki_info)
            material = "\n\n".join(extracted_documents)
            if len(document_infos) == 1:
                document_info = document_infos[0]
            else:
                document_info = {
                    "name": f"{len(document_infos)} evidence sources",
                    "extension": "MULTI",
                    "characters": sum(item["characters"] for item in document_infos),
                    "words": sum(item["words"] for item in document_infos),
                    "lines": sum(item["lines"] for item in document_infos),
                    "preview": "\n".join(item["name"] for item in document_infos),
                    "files": [item["name"] for item in document_infos],
                    "source_details": document_infos,
                }

        endpoint = "responses" if "Responses" in endpoint_label else "chat_completions"
        config = LLMConfig(
            api_key=api_key_input.strip() or environment_key,
            model=model,
            base_url=base_url,
            endpoint=endpoint,
            structured_output=structured_output,
            max_output_tokens=max_output_tokens,
            output_language=output_language,
        )
        prompts = replace(
            load_prompt_bundle(),
            benchmark_reference=build_benchmark_reference(selected_benchmark_ids, output_language),
        )
        st.session_state["evaluation_ready"] = False
        with st.spinner("正在提取证据、执行十维评价并生成报告，请稍候……"):
            llm_result = generate_evaluation_report(material, config, prompts)
    except (ValueError, FileNotFoundError, LLMConfigurationError, LLMRequestError) as exc:
        st.error(str(exc))
        return

    st.session_state["evaluation_ready"] = True
    st.session_state["result_mode"] = "live"
    st.session_state["llm_result"] = llm_result
    st.session_state["document_info"] = document_info
    st.session_state["benchmark_ids"] = selected_benchmark_ids or list(DEFAULT_BENCHMARK_IDS)
    st.session_state["demo_mode"] = False
    st.session_state["report_language"] = output_language
    add_history_record(
        "single",
        llm_result.dashboard.get("practice_name") or document_info.get("name", "Education evaluation"),
        f"{document_info.get('name', 'Evidence source')} · {llm_result.model}",
        {
            "llm_result": llm_result,
            "document_info": document_info,
            "benchmark_ids": selected_benchmark_ids or list(DEFAULT_BENCHMARK_IDS),
            "demo_mode": False,
            "report_language": output_language,
        },
    )
    if managed_mode:
        st.session_state["managed_analysis_count"] = st.session_state.get("managed_analysis_count", 0) + 1


def score_card(label: str, value: str, suffix: str, note: str, accent: str) -> None:
    safe_note = html.escape(note).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="score-card score-accent-{accent}">
            <div class="score-label">{html.escape(label)}</div>
            <div class="score-value">{html.escape(value)} <small>{html.escape(suffix)}</small></div>
            <div class="score-note">{safe_note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_header(result: dict, evidence: dict) -> None:
    info = st.session_state.get("document_info", {})
    st.markdown(
        f"""
        <div class="result-head">
            <div class="section-kicker">Evaluation report · Demo data</div>
            <h2>{html.escape(evidence['practice_name'])}</h2>
            <p>{html.escape(result['headline'])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.get("demo_mode", True):
        notice = "当前显示既有 JLU-CP 案例的本地演示结果，用于验证产品流程与界面。"
    else:
        notice = (
            f"已成功读取上传文件「{info.get('name', '')}」，但尚未接入分析引擎；"
            "下方仍使用 JLU-CP 示例结果，不代表对该文件的评价。"
        )
    st.markdown(f'<div class="notice"><strong>原型说明：</strong>{html.escape(notice)}</div>', unsafe_allow_html=True)

    cols = st.columns(4, gap="medium")
    with cols[0]:
        score_card("Education Design Score", f"{result['design_score']:.1f}", "/ 100", "依据十维加权 Rubric 计算", "indigo")
    with cols[1]:
        score_card("Evidence Coverage", f"{result['evidence_coverage']:.0f}%", "", "评价证据的充分程度", "teal")
    with cols[2]:
        score_card("Strongest Dimension", "D2", "5 / 6", "教学设计质量", "amber")
    with cols[3]:
        score_card("Evaluation Confidence", result["confidence"], "", "受当前材料覆盖范围限制", "slate")


def build_bar_chart(dimensions: list[dict], language: OutputLanguage = "zh") -> go.Figure:
    ordered = list(reversed(dimensions))
    colors = ["#6366f1" if item["normalized_score"] >= 60 else "#c7d2fe" for item in ordered]
    fig = go.Figure(
        go.Bar(
            x=[item["normalized_score"] for item in ordered],
            y=[f"{item['id']}  {item['short_name']}" for item in ordered],
            orientation="h",
            marker_color=colors,
            text=[f"{item['score']}/6" for item in ordered],
            textposition="outside",
            hovertemplate=f"%{{y}}<br>{ui_text('标准化得分', 'Normalized score', language)} %{{x:.0f}}%<extra></extra>",
        )
    )
    fig.update_layout(
        height=460,
        margin=dict(l=10, r=45, t=25, b=25),
        xaxis=dict(range=[0, 108], showgrid=True, gridcolor="#edf0f6", ticksuffix="%", fixedrange=True),
        yaxis=dict(fixedrange=True),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Microsoft YaHei, sans-serif", color="#52617a", size=12),
        showlegend=False,
    )
    return fig


def build_radar_chart(dimensions: list[dict]) -> go.Figure:
    labels = [item["id"] for item in dimensions]
    values = [item["normalized_score"] for item in dimensions]
    fig = go.Figure(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            fillcolor="rgba(99,102,241,.18)",
            line=dict(color="#6366f1", width=2.5),
            marker=dict(size=6, color="#4f46e5"),
            hovertemplate="%{theta}: %{r:.0f}%<extra></extra>",
        )
    )
    fig.update_layout(
        height=460,
        margin=dict(l=50, r=50, t=30, b=30),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(range=[0, 100], showticklabels=False, gridcolor="#e3e7f0"),
            angularaxis=dict(gridcolor="#e3e7f0"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Microsoft YaHei, sans-serif", color="#52617a"),
        showlegend=False,
    )
    return fig


def render_overview_tab(result: dict) -> None:
    st.markdown("### 十维评价概览")
    st.caption("1–6 分原始量表已标准化为百分比用于图形展示；总分按各维既定权重计算。")
    chart_col, radar_col = st.columns([1.25, 1], gap="large")
    with chart_col:
        st.plotly_chart(build_bar_chart(result["dimensions"]), width="stretch", config={"displayModeBar": False})
    with radar_col:
        st.plotly_chart(build_radar_chart(result["dimensions"]), width="stretch", config={"displayModeBar": False})

    table_data = [
        {
            "维度": f"{item['id']} {item['name']}",
            "原始分": f"{item['score']} / 6",
            "权重": f"{item['weight']}%",
            "加权贡献": f"{item['contribution']:.1f}",
            "证据": item["evidence"],
        }
        for item in result["dimensions"]
    ]
    st.dataframe(table_data, width="stretch", hide_index=True)

    st.markdown("### 维度诊断")
    for item in result["dimensions"]:
        with st.expander(
            f"{item['id']} · {item['name']}　{item['score']}/6　·　证据 {item['evidence']}"
        ):
            col1, col2 = st.columns(2, gap="large")
            with col1:
                st.markdown("**当前优势**")
                st.write(item["strength"])
            with col2:
                st.markdown("**为什么不能更高**")
                st.write(item["gap"])


def render_evidence_tab(evidence: dict) -> None:
    st.markdown("### Evidence Profile")
    st.write(evidence["summary"])

    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        st.markdown("**教育目标**")
        for item in evidence["goals"]:
            st.markdown(f"- {item}")
    with col2:
        st.markdown("**目标受众**")
        for item in evidence["audiences"]:
            st.markdown(f"- {item}")
    with col3:
        st.markdown("**教育设计**")
        for item in evidence["design"]:
            st.markdown(f"- {item}")

    st.divider()
    strong_col, gap_col = st.columns([1.1, 1], gap="large")
    with strong_col:
        st.markdown("### 有力证据")
        for item in evidence["strong_evidence"]:
            st.markdown(
                f"""
                <div class="evidence-card">
                    <strong>✓ {html.escape(item['title'])}</strong>
                    <p>{html.escape(item['detail'])}</p>
                    <div class="quote">{html.escape(item['source'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with gap_col:
        st.markdown("### 缺失证据")
        for item in evidence["missing_evidence"]:
            st.markdown(
                f'<div class="gap-item"><span class="gap-dot"></span><span>{html.escape(item)}</span></div>',
                unsafe_allow_html=True,
            )
        st.caption(evidence["coverage_note"])


def render_benchmark_tab(benchmark: dict, result: dict | None = None) -> None:
    if result is not None:
        portfolio = analyze_benchmark_portfolio(result, DEFAULT_BENCHMARK_IDS, "zh")
        st.markdown("### 多案例优秀教育基准")
        st.caption("默认汇总四个历年 Best Education 获奖案例；十维画像为 GEM-EduScore 公开证据分析值，不是官方评分。")
        metric_columns = st.columns(3, gap="medium")
        with metric_columns[0]:
            st.metric("基准案例", len(portfolio["cases"]))
        with metric_columns[1]:
            st.metric("组合画像得分", f"{portfolio['portfolio_score']:.1f} / 100")
        with metric_columns[2]:
            st.metric("最相近案例", f"{portfolio['best_match']['case']['team']} {portfolio['best_match']['case']['year']}", f"{portfolio['best_match']['similarity']:.0f}%")
        current_scores = {item["id"]: item["score"] for item in result["dimensions"]}
        demo_chart = go.Figure()
        demo_chart.add_trace(go.Bar(name="当前演示项目", x=list(current_scores), y=list(current_scores.values()), marker_color="#6366F1"))
        demo_chart.add_trace(go.Bar(name="优秀案例均值", x=list(portfolio["average_profile"]), y=list(portfolio["average_profile"].values()), marker_color="#14B8A6"))
        demo_chart.update_layout(barmode="group", height=390, margin=dict(l=10, r=10, t=35, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis=dict(range=[0, 6.4], dtick=1, gridcolor="#E8ECF4"), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(demo_chart, width="stretch", config={"displayModeBar": False})
        st.markdown("#### 案例组合")
        st.markdown("　".join(f"`{case['team']} {case['year']}`" for case in portfolio["cases"]))
        st.divider()

    st.markdown(f"### 单案例诊断示例：{benchmark['benchmark_name']}")
    st.caption(benchmark["disclaimer"])
    st.markdown("**基准实践特征**")
    st.markdown(
        "".join(f'<span class="benchmark-chip">{html.escape(item)}</span>' for item in benchmark["benchmark_features"]),
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown("**共同优势**")
    for item in benchmark["shared_strengths"]:
        st.markdown(f"- {item}")

    st.markdown("### 关键差距")
    for gap in benchmark["gaps"]:
        with st.container(border=True):
            header_col, priority_col = st.columns([5, 1])
            with header_col:
                st.markdown(f"**{gap['dimension']}**")
            with priority_col:
                st.caption(f"优先级：{gap['priority']}")
            current_col, benchmark_col = st.columns(2, gap="large")
            with current_col:
                st.caption("当前实践")
                st.write(gap["current"])
            with benchmark_col:
                st.caption("基准特征")
                st.write(gap["benchmark"])
            st.info(f"改进机会：{gap['opportunity']}")


def render_roadmap_tab(roadmap: list[dict]) -> None:
    st.markdown("### 分阶段改进路线")
    st.caption("建议由证据缺口与基准差异共同推导，优先补齐高收益的评价和反馈环节。")
    cols = st.columns(3, gap="medium")
    for column, stage in zip(cols, roadmap):
        with column:
            with st.container(border=True):
                st.markdown(
                    f'<span class="roadmap-stage" style="color:{stage["accent"]}">{stage["stage"]}</span>'
                    f'<span class="roadmap-time">{stage["timeline"]}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(f'<div class="roadmap-title">{stage["theme"]}</div>', unsafe_allow_html=True)
                for action in stage["actions"]:
                    st.markdown(f"- {action}")
                st.divider()
                st.caption(stage["impact"])

    st.markdown("### 建议的第一步")
    with st.container(border=True):
        action_col, impact_col = st.columns([1.4, 1], gap="large")
        with action_col:
            st.markdown("**为下一次核心活动建立最小评价包**")
            st.write("一份 3–5 题前测、一份对应后测、一张教师观察表，以及一个参与者作品归档目录。")
        with impact_col:
            st.markdown("**为什么优先做这个？**")
            st.write("工作量可控，同时直接补强 D4、D5 和整体证据覆盖率。")


def render_live_overview(dashboard: dict, language: OutputLanguage) -> None:
    t = lambda zh, en: ui_text(zh, en, language)
    chart_col, radar_col = st.columns([1.25, 1], gap="large")
    with chart_col:
        st.markdown(f"#### {t('维度表现', 'Dimension Performance')}")
        st.plotly_chart(build_bar_chart(dashboard["dimensions"], language), width="stretch", config={"displayModeBar": False})
    with radar_col:
        st.markdown(f"#### {t('教育质量画像', 'Education Quality Profile')}")
        st.plotly_chart(build_radar_chart(dashboard["dimensions"]), width="stretch", config={"displayModeBar": False})

    table_data = [
        {
            t("维度", "Dimension"): f"{item['id']} {item['name']}",
            t("得分", "Score"): f"{item['score']} / 6",
            t("权重", "Weight"): f"{item['weight']}%",
            t("加权贡献", "Contribution"): f"{item['contribution']:.1f}",
            t("证据", "Evidence"): item["evidence_strength"],
        }
        for item in dashboard["dimensions"]
    ]
    st.dataframe(table_data, width="stretch", hide_index=True)

    st.markdown(f"### {t('维度诊断', 'Dimension-level Diagnosis')}")
    for item in dashboard["dimensions"]:
        with st.expander(
            f"{item['id']} · {item['name']}　{item['score']}/6　·　{t('证据', 'Evidence')} {item['evidence_strength']}"
        ):
            evidence_col, analysis_col, action_col = st.columns([1.15, 1, 1], gap="large")
            with evidence_col:
                st.markdown(f"**{t('证据原文（保留原始语言）', 'Source evidence excerpts')}**")
                if item["evidence_quotes"]:
                    for quote in item["evidence_quotes"]:
                        st.caption(f"“{quote}”")
                else:
                    st.caption(t("未发现证据", "Not Evidenced"))
            with analysis_col:
                st.markdown(f"**{t('评价', 'Evaluation')}**")
                st.write(item["reason"])
                st.caption(f"{t('为何不能更高', 'Why not higher')}: {item['why_not_higher']}")
            with action_col:
                st.markdown(f"**{t('下一步', 'Next move')}**")
                st.write(item["improvement"])


def render_live_evidence(dashboard: dict, language: OutputLanguage) -> None:
    t = lambda zh, en: ui_text(zh, en, language)
    profile = dashboard["evidence_profile"]
    overview_cols = st.columns(3, gap="medium")
    with overview_cols[0]:
        st.markdown(f"**{t('目标受众', 'Target audiences')}**")
        for item in dashboard["audiences"]:
            st.markdown(f"- {item}")
    with overview_cols[1]:
        st.markdown(f"**{t('教育目标', 'Education goals')}**")
        for item in dashboard["goals"]:
            st.markdown(f"- {item}")
    with overview_cols[2]:
        st.markdown(f"**{t('活动 / 记录', 'Activities / records')}**")
        for item in dashboard["activities"]:
            st.markdown(f"- {item}")

    st.divider()
    strong_col, missing_col = st.columns([1.15, 1], gap="large")
    with strong_col:
        st.markdown(f"### {t('有力证据', 'Evidence we can stand behind')}")
        for item in profile["strong_evidence"]:
            source_url = str(item.get("source_url") or "")
            source_link = (
                f'<div class="source-link"><a href="{html.escape(source_url)}" target="_blank">{t("打开 Wiki 来源", "Open Wiki source")} ↗</a></div>'
                if source_url.startswith(("https://", "http://"))
                else ""
            )
            st.markdown(
                f"""
                <div class="evidence-card">
                    <strong>✓ {html.escape(item['record_id'])} · {html.escape(item['strength'])}</strong>
                    <p>{html.escape(item['statement'])}</p>
                    <div class="quote"><strong>{t('证据原文（原始语言）', 'Source quote')}：</strong><br>“{html.escape(item['source_quote'])}”</div>
                    {source_link}
                </div>
                """,
                unsafe_allow_html=True,
            )
    with missing_col:
        st.markdown(f"### {t('证据缺口', 'Evidence gaps')}")
        for item in profile["missing_evidence"]:
            st.markdown(
                f'<div class="gap-item"><span class="gap-dot"></span><span>{html.escape(item)}</span></div>',
                unsafe_allow_html=True,
            )
        st.info(t("证据不足会降低评价可信度，但不自动等同于活动设计质量差。", "Limited evidence reduces confidence; it does not automatically mean the activity design is weak."))


def render_live_benchmark(dashboard: dict, language: OutputLanguage) -> None:
    t = lambda zh, en: ui_text(zh, en, language)
    benchmark_ids = st.session_state.get("benchmark_ids", list(DEFAULT_BENCHMARK_IDS))
    portfolio = analyze_benchmark_portfolio(dashboard, benchmark_ids, language)
    st.markdown(f"### {t('多案例优秀教育基准', 'Multi-case Education Excellence Benchmark')}")
    st.caption(
        t(
            "获奖身份和来源链接来自 iGEM 官方公开资料；十维画像为 GEM-EduScore 基于 Wiki 证据建立的分析值，不是官方评分或排名。",
            "Award status and source links come from public iGEM records. Ten-dimension profiles are GEM-EduScore analyses of Wiki evidence, not official scores or rankings.",
        )
    )

    metric_cols = st.columns(3, gap="medium")
    with metric_cols[0]:
        st.metric(t("基准案例", "Benchmark cases"), len(portfolio["cases"]))
    with metric_cols[1]:
        st.metric(t("组合画像得分", "Portfolio profile score"), f"{portfolio['portfolio_score']:.1f} / 100")
    with metric_cols[2]:
        match = portfolio["best_match"]
        st.metric(t("最相近案例", "Closest case"), f"{match['case']['team']} {match['case']['year']}", f"{match['similarity']:.0f}%")

    current_scores = {item["id"]: item["score"] for item in dashboard["dimensions"]}
    chart = go.Figure()
    chart.add_trace(
        go.Bar(
            name=t("当前项目", "Current project"),
            x=list(current_scores),
            y=list(current_scores.values()),
            marker_color="#6366F1",
            hovertemplate="%{x}: %{y}/6<extra></extra>",
        )
    )
    chart.add_trace(
        go.Bar(
            name=t("优秀案例均值", "Excellence portfolio average"),
            x=list(portfolio["average_profile"]),
            y=list(portfolio["average_profile"].values()),
            marker_color="#14B8A6",
            hovertemplate="%{x}: %{y:.2f}/6<extra></extra>",
        )
    )
    chart.update_layout(
        barmode="group",
        height=390,
        margin=dict(l=10, r=10, t=25, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(range=[0, 6.35], dtick=1, gridcolor="#E8ECF4", title=t("得分", "Score")),
        xaxis=dict(title=None),
        legend=dict(orientation="h", y=1.12, x=0),
        font=dict(color="#53627D"),
    )
    st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})

    st.markdown(f"#### {t('案例证据卡', 'Benchmark evidence cards')}")
    case_columns = st.columns(2, gap="medium")
    for index, case in enumerate(portfolio["cases"]):
        with case_columns[index % 2]:
            with st.container(border=True):
                award = ui_text(case["award_zh"], case["award_en"], language)
                summary = ui_text(case["summary_zh"], case["summary_en"], language)
                st.markdown(f"**{case['team']} {case['year']}**　`{award}`")
                case_status = t("官方获奖案例", "Official winner") if case["official_winner"] else t("精选组合案例", "Curated portfolio")
                st.caption(f"{case['division']} · {case_status}")
                st.write(summary)
                features = case["features_zh"] if language == "zh" else case["features_en"]
                if language == "bilingual":
                    features = [f"{zh} / {en}" for zh, en in zip(case["features_zh"], case["features_en"])]
                st.markdown(" · ".join(f"`{feature}`" for feature in features))
                st.markdown(f"[{t('查看公开教育页面', 'Open public education page')} ↗]({case['wiki_url']})")

    matrix_rows = []
    for case in portfolio["cases"]:
        matrix_rows.append(
            {
                t("案例", "Case"): f"{case['team']} {case['year']}",
                **{dimension_id: case["profile"][dimension_id] for dimension_id in portfolio["average_profile"]},
            }
        )
    matrix_rows.append(
        {t("案例", "Case"): t("当前项目", "Current project"), **current_scores}
    )
    st.markdown(f"#### {t('十维画像矩阵', 'Ten-dimension profile matrix')}")
    st.dataframe(matrix_rows, width="stretch", hide_index=True)

    st.markdown(f"#### {t('模型识别的共同优势', 'Model-identified shared strengths')}")
    for item in dashboard["benchmark_similarities"]:
        st.markdown(f"- ✓ {item}")

    st.markdown(f"### {t('差距—行动矩阵', 'Gap-to-Action Matrix')}")
    for gap in dashboard["benchmark_gaps"]:
        priority_color = {"High": "#dc2626", "Medium": "#d97706", "Low": "#0f766e"}[gap["priority"]]
        priority_label = {
            "High": t("高", "HIGH"),
            "Medium": t("中", "MEDIUM"),
            "Low": t("低", "LOW"),
        }[gap["priority"]]
        with st.container(border=True):
            heading_col, priority_col = st.columns([5, 1])
            with heading_col:
                st.markdown(f"**{gap['dimension']}**")
                st.caption(gap["gap"])
            with priority_col:
                st.markdown(
                    f'<span style="color:{priority_color};font-weight:800;font-size:.8rem">{priority_label}</span>',
                    unsafe_allow_html=True,
                )
            current_col, arrow_col, benchmark_col = st.columns([1, .12, 1], gap="small")
            with current_col:
                st.caption(t("当前实践", "CURRENT PRACTICE"))
                st.write(gap["current_practice"])
            with arrow_col:
                st.markdown("### →")
            with benchmark_col:
                st.caption(t("基准实践", "BENCHMARK PRACTICE"))
                st.write(gap["benchmark_practice"])
            st.success(f"{t('改进机会', 'Opportunity')} · {gap['opportunity']}")


def render_live_roadmap(dashboard: dict, language: OutputLanguage) -> None:
    t = lambda zh, en: ui_text(zh, en, language)
    recommendations = dashboard["recommendations"]
    stages = [
        (t("短期", "Short term"), t("现在 · 1–3 个月", "NOW · 1–3 MONTHS"), recommendations["short_term"], "#0f9f8f", t("先补证据", "Strengthen evidence first")),
        (t("中期", "Medium term"), t("下一阶段 · 3–12 个月", "NEXT · 3–12 MONTHS"), recommendations["medium_term"], "#6366f1", t("沉淀可复用资产", "Build reusable assets")),
        (t("长期", "Long term"), t("未来 · 1 年以上", "FUTURE · 1 YEAR+"), recommendations["long_term"], "#d97706", t("建立持续教育系统", "Build a lasting education system")),
    ]
    columns = st.columns(3, gap="medium")
    for column, (stage, timeline, actions, color, title) in zip(columns, stages):
        with column:
            with st.container(border=True):
                st.markdown(
                    f'<span class="roadmap-stage" style="color:{color}">{stage}</span>'
                    f'<span class="roadmap-time">{timeline}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(f'<div class="roadmap-title">{title}</div>', unsafe_allow_html=True)
                for index, action in enumerate(actions, 1):
                    st.markdown(f"**{index:02d}**　{action}")

    st.markdown(f"### {t('战略结论', 'Strategic takeaway')}")
    with st.container(border=True):
        st.write(dashboard["conclusion"])


def wiki_pages_from_info(info: dict) -> list[dict]:
    """Collect and deduplicate Wiki source pages from single or combined input metadata."""
    candidates = list(info.get("pages", []))
    for source in info.get("source_details", []):
        candidates.extend(source.get("pages", []))
    pages = []
    seen = set()
    for page in candidates:
        url = str(page.get("url", "")).strip()
        if not url or url in seen:
            continue
        seen.add(url)
        pages.append(page)
    return pages


def append_wiki_sources(report: str, pages: list[dict], language: OutputLanguage) -> str:
    if not pages:
        return report
    heading = ui_text("Wiki 来源页面", "Wiki Source Pages", language)
    source_lines = ["", f"## {heading}", ""]
    for page in pages:
        source_title = str(page.get("title", "Wiki page")).replace("[", "").replace("]", "").replace("\n", " ")
        source_lines.append(f"- [{source_title}]({page['url']})")
    return report + "\n" + "\n".join(source_lines)


def render_live_report() -> None:
    llm_result = st.session_state["llm_result"]
    dashboard = llm_result.dashboard
    language: OutputLanguage = getattr(llm_result, "output_language", "zh")
    t = lambda zh, en: ui_text(zh, en, language)
    info = st.session_state.get("document_info", {})
    file_name = str(info.get("name", "Education Material"))
    safe_stem = Path(file_name).stem or "GEM-EduScore_Report"
    strongest = dashboard["strongest_dimension"]
    priority = dashboard["priority_dimension"]
    wiki_pages = wiki_pages_from_info(info)
    report_for_download = append_wiki_sources(llm_result.report_markdown, wiki_pages, language)
    safe_summary = html.escape(dashboard["summary"]).replace("\n", "<br>")

    st.markdown(
        f"""
        <div class="result-head">
            <div class="live-badge"><span class="live-dot"></span> {t('证据驱动实时分析', 'EVIDENCE-DRIVEN LIVE ANALYSIS')}</div>
            <h2>{html.escape(dashboard['practice_name'])}</h2>
            <p>{safe_summary}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if llm_result.compatibility_repaired:
        if language == "zh":
            repair_notice = (llm_result.compatibility_note or "兼容模式已自动修复模型遗漏的结构字段。") + " 未返回的证据不会被虚构。"
        else:
            repair_notice = t(
                "兼容模式已保守修复模型遗漏或截断的结构字段；未返回的证据不会被虚构。",
                "Compatibility mode conservatively repaired missing or truncated structure; evidence not returned by the model was not invented.",
            )
        st.info(repair_notice)
    if not getattr(llm_result, "language_compliant", True):
        st.warning(
            t(
                "模型仍有少量内容未完全遵循所选语言。英文证据原文与专有名词会保留；其余分析建议重新生成或换用指令遵循能力更强的模型。",
                "A small amount of generated content still does not fully follow the selected language. Source quotations and proper names are retained; consider regenerating with a stronger instruction-following model.",
            )
        )
    elif getattr(llm_result, "language_repaired", False):
        st.caption(
            t(
                "✓ 已自动校正生成内容的语言；证据原文、评分和来源未被改写。",
                "✓ Generated-language consistency was repaired automatically; source quotations, scores and provenance were preserved.",
            )
        )

    score_cols = st.columns(4, gap="medium")
    with score_cols[0]:
        score_card(t("教育设计得分", "Education Design Score"), f"{dashboard['design_score']:.1f}", "/ 100", t("十维加权量规", "Ten-dimension weighted rubric"), "indigo")
    with score_cols[1]:
        score_card(t("证据覆盖率", "Evidence Coverage"), f"{dashboard['evidence_coverage']:.0f}%", "", t("证据强度 × 维度权重", "Evidence strength × dimension weight"), "teal")
    with score_cols[2]:
        score_card(t("最强维度", "Strongest Dimension"), strongest["id"], f"{strongest['score']} / 6", strongest["name"], "amber")
    with score_cols[3]:
        score_card(t("优先改进", "Priority Focus"), priority["id"], f"{priority['score']} / 6", f"{t('可信度', 'Confidence')}: {dashboard['confidence']}", "slate")

    overview_tab, evidence_tab, benchmark_tab, roadmap_tab, report_tab = st.tabs(
        [t("概览", "Dashboard"), t("证据", "Evidence"), t("基准比较", "Benchmark"), t("行动路线", "Action Roadmap"), t("完整报告", "Full Report")]
    )
    with overview_tab:
        render_live_overview(dashboard, language)
    with evidence_tab:
        render_live_evidence(dashboard, language)
    with benchmark_tab:
        render_live_benchmark(dashboard, language)
    with roadmap_tab:
        render_live_roadmap(dashboard, language)
    with report_tab:
        export_language: OutputLanguage = language
        if language == "bilingual" and llm_result.localized_reports:
            st.markdown("#### 下载报告 / Download report")
            language_options = {
                "中英双语 / Bilingual": "bilingual",
                "中文": "zh",
                "English": "en",
            }
            selected_export_label = st.radio(
                "报告语言 / Report language",
                options=list(language_options),
                horizontal=True,
                label_visibility="collapsed",
                key="report_export_language",
            )
            export_language = language_options[selected_export_label]
        else:
            st.markdown(f"#### {t('下载报告', 'Download report')}")

        export_dashboard = llm_result.localized_dashboards.get(export_language, dashboard)
        export_markdown = llm_result.localized_reports.get(export_language, llm_result.report_markdown)
        report_for_download = append_wiki_sources(export_markdown, wiki_pages, export_language)
        language_suffix = {"zh": "ZH", "en": "EN", "bilingual": "Bilingual"}[export_language]
        file_base = f"{safe_stem}_GEM-EduScore_Report_{language_suffix}"

        try:
            pdf_bytes = cached_pdf_report(export_dashboard, export_language, wiki_pages)
            docx_bytes = cached_docx_report(export_dashboard, export_language, wiki_pages)
            download_columns = st.columns(3, gap="small")
            with download_columns[0]:
                st.download_button(
                    ui_text("下载 Markdown", "Download Markdown", export_language),
                    data=report_for_download,
                    file_name=f"{file_base}.md",
                    mime="text/markdown",
                    width="stretch",
                    key=f"download_markdown_{export_language}",
                )
            with download_columns[1]:
                st.download_button(
                    ui_text("下载 PDF", "Download PDF", export_language),
                    data=pdf_bytes,
                    file_name=f"{file_base}.pdf",
                    mime="application/pdf",
                    width="stretch",
                    key=f"download_pdf_{export_language}",
                )
            with download_columns[2]:
                st.download_button(
                    ui_text("下载 Word", "Download Word", export_language),
                    data=docx_bytes,
                    file_name=f"{file_base}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    width="stretch",
                    key=f"download_docx_{export_language}",
                )
        except Exception as exc:
            st.download_button(
                ui_text("下载 Markdown", "Download Markdown", export_language),
                data=report_for_download,
                file_name=f"{file_base}.md",
                mime="text/markdown",
                width="stretch",
                key=f"download_markdown_fallback_{export_language}",
            )
            st.warning(
                t(
                    "PDF / Word 导出组件尚未就绪；请通过桌面入口重新启动，程序会自动补齐依赖。",
                    "PDF / Word export components are not ready. Restart from the desktop launcher to install them automatically.",
                )
            )
            st.caption(str(exc))

        input_tokens = f"{llm_result.input_tokens:,}" if llm_result.input_tokens is not None else "—"
        output_tokens = f"{llm_result.output_tokens:,}" if llm_result.output_tokens is not None else "—"
        st.caption(
            f"{llm_result.model} · {llm_result.duration_seconds:.1f}s · "
            f"{input_tokens} {t('输入', 'input')} / {output_tokens} {t('输出 tokens', 'output tokens')}"
        )
        with st.container(border=True):
            st.markdown(report_for_download)
        with st.expander(t("来源与运行详情", "Source and run details")):
            st.write(f"- {t('文件', 'File')}: {file_name}")
            st.write(f"- {t('字符数', 'Characters')}: {info.get('characters', '—')}")
            st.write(f"- {t('提示词（Prompt）', 'Prompt')}: GEM-EduScore Master Prompt V1.0")
            st.write(f"- {t('比较基准', 'Benchmark')}: {dashboard['benchmark_name']}")
            st.write(f"- {t('输出方式', 'Output method')}: {llm_result.output_method}")
            export_language_label = {"zh": "中文", "en": "English", "bilingual": "中文 / English"}[export_language]
            st.write(f"- {t('报告语言', 'Report language')}: {export_language_label}")
            if wiki_pages:
                st.markdown(f"**{t('已纳入的 Wiki 页面', 'Wiki pages included')}**")
                for page in wiki_pages:
                    source_title = str(page.get("title", "Wiki page")).replace("[", "").replace("]", "").replace("\n", " ")
                    st.markdown(f"- [{source_title}]({page['url']})")
            if llm_result.finish_reason:
                st.write(f"- Finish reason: {llm_result.finish_reason}")
            if llm_result.response_id:
                st.caption(f"Response ID: {llm_result.response_id}")


def render_results() -> None:
    result = evaluate_demo_case()
    evidence = get_demo_evidence_profile()
    benchmark = get_benchmark_comparison()
    roadmap = get_improvement_roadmap()

    render_result_header(result, evidence)
    overview_tab, evidence_tab, benchmark_tab, roadmap_tab = st.tabs(
        ["总览", "证据分析", "基准比较", "改进路线"]
    )
    with overview_tab:
        render_overview_tab(result)
    with evidence_tab:
        render_evidence_tab(evidence)
    with benchmark_tab:
        render_benchmark_tab(benchmark, result)
    with roadmap_tab:
        render_roadmap_tab(roadmap)


def render_comparison_source_input(prefix: str, heading: str) -> dict:
    """Render one side of the file/Wiki comparison input."""
    with st.container(border=True):
        st.markdown(f"### {heading}")
        project_label = st.text_input(
            "项目显示名称（可选）",
            placeholder=f"例如：Team {prefix} Education",
            key=f"comparison_label_{prefix}",
        )
        source_mode = st.radio(
            "材料来源",
            ["上传文件", "分析 Wiki"],
            horizontal=True,
            key=f"comparison_source_mode_{prefix}",
        )
        files = []
        wiki_url = ""
        crawl_related = True
        max_pages = 6
        if source_mode == "上传文件":
            files = st.file_uploader(
                f"{heading} Education material",
                type=["md", "txt", "docx", "pdf", "pptx", "html", "htm", "csv"],
                accept_multiple_files=True,
                label_visibility="collapsed",
                help="最多 5 份文件；支持 MD、TXT、DOCX、PDF、PPTX、HTML 和 CSV。",
                key=f"comparison_files_{prefix}",
            )
        else:
            wiki_url = st.text_input(
                "队伍 Wiki 或 Education 页面",
                placeholder="https://2025.igem.wiki/team-name/education",
                key=f"comparison_wiki_{prefix}",
            )
            crawl_related = st.toggle(
                "自动发现教育相关页面",
                value=True,
                key=f"comparison_crawl_{prefix}",
            )
            max_pages = st.number_input(
                "最多读取页面",
                min_value=1,
                max_value=12,
                value=6,
                step=1,
                disabled=not crawl_related,
                key=f"comparison_pages_{prefix}",
            )
        return {
            "label": project_label.strip(),
            "mode": source_mode,
            "files": files,
            "wiki_url": wiki_url.strip(),
            "crawl_related": crawl_related,
            "max_pages": int(max_pages),
        }


def extract_comparison_source(source: dict, project_marker: str) -> tuple[str, dict]:
    """Extract one comparison side while retaining source boundaries and provenance."""
    if source["mode"] == "分析 Wiki":
        if not source["wiki_url"]:
            raise ValueError(f"请填写项目 {project_marker} 的 Wiki 地址。")
        material, info = cached_extract_wiki_material(
            source["wiki_url"],
            source["crawl_related"],
            source["max_pages"] if source["crawl_related"] else 1,
        )
        return f"[PROJECT {project_marker} · WIKI EVIDENCE]\n{material}\n[/PROJECT {project_marker} · WIKI EVIDENCE]", info

    files = list(source["files"] or [])
    if not files:
        raise ValueError(f"请至少上传一份项目 {project_marker} 的 Education 材料。")
    if len(files) > 5:
        raise ValueError(f"项目 {project_marker} 一次最多上传 5 份材料。")
    materials = []
    infos = []
    for uploaded_file in files:
        document_text, info = extract_document_text(uploaded_file.name, uploaded_file.getvalue())
        safe_name = uploaded_file.name.replace("\r", " ").replace("\n", " ").replace("]", "")
        materials.append(f"[PROJECT {project_marker} · SOURCE DOCUMENT: {safe_name}]\n{document_text}\n[/SOURCE DOCUMENT]")
        infos.append(info)
    if len(infos) == 1:
        info = infos[0]
    else:
        info = {
            "name": f"{len(infos)} evidence files",
            "extension": "MULTI",
            "characters": sum(item["characters"] for item in infos),
            "words": sum(item["words"] for item in infos),
            "lines": sum(item["lines"] for item in infos),
            "preview": "\n".join(item["name"] for item in infos),
            "files": [item["name"] for item in infos],
            "source_details": infos,
        }
    return "\n\n".join(materials), info


def render_comparison_panel() -> None:
    """Run two independent evaluations and prepare a deterministic cross-project comparison."""
    managed_mode = setting_is_true("GEM_EDUSCORE_MANAGED_API")
    environment_key = runtime_setting("OPENAI_API_KEY")
    configured_base_url = runtime_setting("OPENAI_BASE_URL", "https://api.openai.com/v1")
    configured_model = runtime_setting("OPENAI_MODEL", "gpt-5-mini")
    provider = provider_for_base_url(configured_base_url)
    access_code_required = runtime_setting("GEM_EDUSCORE_ACCESS_CODE") if managed_mode else ""
    try:
        session_limit = max(2, int(runtime_setting("GEM_EDUSCORE_SESSION_LIMIT", "4")))
    except ValueError:
        session_limit = 4

    with st.container(border=True):
        st.markdown('<div class="section-kicker">Project comparison laboratory</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">双项目教育实践对比</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">分别评估两个项目，再在同一十维量规和优秀案例组合基准下进行可视化对照。支持文件 ↔ 文件、Wiki ↔ Wiki、文件 ↔ Wiki。</div>',
            unsafe_allow_html=True,
        )

        st.markdown("**对比报告语言 / Comparison language**")
        language_label = st.radio(
            "对比报告语言",
            ["中文", "English", "中英双语 / Bilingual"],
            horizontal=True,
            label_visibility="collapsed",
            key="comparison_language_selector",
        )
        output_language: OutputLanguage = {
            "中文": "zh",
            "English": "en",
            "中英双语 / Bilingual": "bilingual",
        }[language_label]

        source_columns = st.columns(2, gap="large")
        with source_columns[0]:
            source_a = render_comparison_source_input("A", "项目 A / Project A")
        with source_columns[1]:
            source_b = render_comparison_source_input("B", "项目 B / Project B")

        benchmark_options = benchmark_case_options(output_language)
        default_labels = [label for label, case_id in benchmark_options.items() if case_id in DEFAULT_BENCHMARK_IDS]
        selected_labels = st.multiselect(
            "共同优秀案例基准",
            options=list(benchmark_options),
            default=default_labels,
            help="两个项目会使用完全相同的案例组合和十维量规，确保横向比较口径一致。",
            key="comparison_benchmarks",
        )
        benchmark_ids = [benchmark_options[label] for label in selected_labels] or list(DEFAULT_BENCHMARK_IDS)

        api_key_input = ""
        access_code_input = ""
        structured_output = "auto"
        max_output_tokens = 8192
        if managed_mode:
            with st.expander("平台连接状态", expanded=False):
                if environment_key:
                    st.success(f"平台托管模型已就绪 · {configured_model}")
                else:
                    st.error("平台尚未配置 API Key，请联系项目维护者。")
                st.caption("一次双项目对比会调用模型两次。")
            if access_code_required:
                access_code_input = st.text_input("展示访问码", type="password", key="comparison_access_code")
            base_url = configured_base_url
            model = configured_model
            endpoint_label = runtime_setting("OPENAI_ENDPOINT", "responses")
        else:
            with st.expander("对比模型与 API 设置", expanded=True):
                provider_labels = [item.label for item in PROVIDER_PRESETS]
                provider_label = st.selectbox(
                    "API 服务提供商",
                    provider_labels,
                    index=provider_labels.index(provider.label),
                    key="comparison_provider",
                )
                provider = next(item for item in PROVIDER_PRESETS if item.label == provider_label)
                protocol_options = ["OpenAI-compatible Chat（推荐）"]
                if provider.supports_responses:
                    protocol_options.insert(0, "OpenAI Responses（原生结构化）")
                endpoint_label = st.selectbox("调用协议", protocol_options, key=f"comparison_endpoint_{provider.id}")
                base_url = st.text_input(
                    "API 地址",
                    value=configured_base_url if provider.id == "custom" else provider.base_url,
                    key=f"comparison_base_url_{provider.id}",
                )
                model = st.text_input(
                    "模型名称",
                    value=configured_model if provider.id == "custom" else provider.default_model,
                    key=f"comparison_model_{provider.id}",
                )
                api_key_input = st.text_input(
                    "API Key",
                    type="password",
                    placeholder="仅在当前会话中使用",
                    key=f"comparison_api_key_{provider.id}",
                )
                with st.expander("高级兼容设置", expanded=False):
                    strategy_label = st.selectbox(
                        "结构化输出策略",
                        ["自动协商（JSON Schema → JSON → 提示词）", "优先 JSON Schema", "优先 JSON Object", "仅提示词约束"],
                        key=f"comparison_strategy_{provider.id}",
                    )
                    structured_output = {
                        "自动协商（JSON Schema → JSON → 提示词）": "auto",
                        "优先 JSON Schema": "json_schema",
                        "优先 JSON Object": "json_object",
                        "仅提示词约束": "prompt_only",
                    }[strategy_label]
                    max_output_tokens = st.slider(
                        "每个项目最大输出长度",
                        2048,
                        16384,
                        8192,
                        1024,
                        key=f"comparison_max_tokens_{provider.id}",
                    )

        comparison_action_col, comparison_reset_col = st.columns([4, 1], gap="small")
        with comparison_action_col:
            start_comparison = st.button("开始双项目 AI 对比  →", type="primary", width="stretch")
        with comparison_reset_col:
            restart_comparison = st.button(
                "停止 / 重来",
                type="secondary",
                icon=":material/stop_circle:",
                help="清空当前对比输入和结果，历史记录与已计入的托管调用次数会保留。",
                width="stretch",
                key="reset_comparison_evaluation",
            )
        st.caption("两个项目会独立执行完整十维评价；横向差异和互相借鉴建议由本地确定性逻辑计算，不额外消耗第三次 API 调用。")

    if restart_comparison:
        reset_evaluation_session()
        st.rerun()
    if not start_comparison:
        return
    if managed_mode:
        if access_code_required and not hmac.compare_digest(access_code_input, access_code_required):
            st.error("展示访问码不正确。")
            return
        if st.session_state.get("managed_analysis_count", 0) + 2 > session_limit:
            st.error(f"当前会话剩余调用次数不足以完成双项目对比（需要 2 次，限额 {session_limit} 次）。")
            return

    try:
        endpoint = "responses" if "Responses" in endpoint_label or endpoint_label == "responses" else "chat_completions"
        config = LLMConfig(
            api_key=api_key_input.strip() or environment_key,
            model=model,
            base_url=base_url,
            endpoint=endpoint,
            structured_output=structured_output,
            max_output_tokens=max_output_tokens,
            output_language=output_language,
        )
        prompts = replace(
            load_prompt_bundle(),
            benchmark_reference=build_benchmark_reference(benchmark_ids, output_language),
        )
        with st.status("正在建立双项目证据矩阵……", expanded=True) as status:
            st.write("01 · 读取项目 A 材料")
            material_a, info_a = extract_comparison_source(source_a, "A")
            st.write("02 · 读取项目 B 材料")
            material_b, info_b = extract_comparison_source(source_b, "B")
            st.write("03 · 评估项目 A")
            result_a = generate_evaluation_report(material_a, config, prompts)
            st.write("04 · 评估项目 B")
            result_b = generate_evaluation_report(material_b, config, prompts)
            status.update(label="双项目评价完成，正在生成对比视图。", state="complete", expanded=False)
    except (ValueError, FileNotFoundError, LLMConfigurationError, LLMRequestError) as exc:
        st.error(str(exc))
        return

    label_a = source_a["label"] or result_a.dashboard["practice_name"] or str(info_a.get("name", "Project A"))
    label_b = source_b["label"] or result_b.dashboard["practice_name"] or str(info_b.get("name", "Project B"))
    comparison_state = {
        "result_a": result_a,
        "result_b": result_b,
        "info_a": info_a,
        "info_b": info_b,
        "label_a": label_a,
        "label_b": label_b,
        "language": output_language,
        "benchmark_ids": benchmark_ids,
    }
    st.session_state["comparison_results"] = comparison_state
    st.session_state["evaluation_ready"] = True
    st.session_state["result_mode"] = "comparison"
    add_history_record(
        "comparison",
        f"{label_a} vs {label_b}",
        f"{result_a.model} · {result_b.model}",
        {"comparison_results": comparison_state},
    )
    if managed_mode:
        st.session_state["managed_analysis_count"] = st.session_state.get("managed_analysis_count", 0) + 2


def render_project_comparison() -> None:
    """Render the two-project visual comparison workspace."""
    state = st.session_state["comparison_results"]
    result_a = state["result_a"]
    result_b = state["result_b"]
    language: OutputLanguage = state["language"]
    # Always read both sides from the same requested language view. This matters
    # when one provider returned a bilingual payload or needed a language repair.
    dashboard_a = result_a.localized_dashboards.get(language, result_a.dashboard)
    dashboard_b = result_b.localized_dashboards.get(language, result_b.dashboard)
    t = lambda zh, en: ui_text(zh, en, language)
    label_a = state["label_a"]
    label_b = state["label_b"]
    comparison = compare_projects(dashboard_a, dashboard_b, label_a, label_b, language)
    portfolio_a = analyze_benchmark_portfolio(dashboard_a, state["benchmark_ids"], language)
    portfolio_b = analyze_benchmark_portfolio(dashboard_b, state["benchmark_ids"], language)

    st.markdown(
        f"""
        <div class="result-head">
            <div class="live-badge"><span class="live-dot"></span> {t('双项目证据对比已完成', 'PAIRWISE EVIDENCE COMPARISON READY')}</div>
            <h2>{html.escape(label_a)} <span style="color:#7c3aed">vs</span> {html.escape(label_b)}</h2>
            <p>{t('同一量规、同一案例组合、两次独立评价；差异只反映已提供材料中的证据。', 'Same rubric, same benchmark portfolio, two independent evaluations; differences reflect only the supplied evidence.')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    score_columns = st.columns(4, gap="medium")
    with score_columns[0]:
        score_card(label_a, f"{dashboard_a['design_score']:.1f}", "/ 100", t("教育设计得分", "Education design score"), "indigo")
    with score_columns[1]:
        score_card(label_b, f"{dashboard_b['design_score']:.1f}", "/ 100", t("教育设计得分", "Education design score"), "teal")
    with score_columns[2]:
        score_card(t("设计得分差", "Design score delta"), f"{comparison['design_delta']:+.1f}", "A − B", t("正值表示项目 A 更高", "Positive means Project A is higher"), "amber")
    with score_columns[3]:
        evidence_lead = label_a if comparison["evidence_delta"] > 0 else label_b if comparison["evidence_delta"] < 0 else t("持平", "Tie")
        score_card(t("证据覆盖领先", "Evidence coverage lead"), evidence_lead, f"{abs(comparison['evidence_delta']):.1f} pp", t("仅衡量材料证据覆盖", "Evidence coverage only"), "slate")

    overview_tab, dimension_tab, benchmark_tab, learning_tab, report_tab = st.tabs(
        [t("总览", "Overview"), t("十维对照", "Ten Dimensions"), t("优秀案例基准", "Excellence Benchmarks"), t("互相借鉴", "Cross-learning"), t("完整报告", "Full Reports")]
    )
    dimensions_a = {item["id"]: item for item in dashboard_a["dimensions"]}
    dimensions_b = {item["id"]: item for item in dashboard_b["dimensions"]}
    dimension_ids = list(dimensions_a)

    with overview_tab:
        bar = go.Figure()
        bar.add_trace(go.Bar(name=label_a, x=dimension_ids, y=[dimensions_a[item]["score"] for item in dimension_ids], marker_color="#6366F1"))
        bar.add_trace(go.Bar(name=label_b, x=dimension_ids, y=[dimensions_b[item]["score"] for item in dimension_ids], marker_color="#14B8A6"))
        bar.update_layout(
            barmode="group", height=410, margin=dict(l=10, r=10, t=35, b=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[0, 6.4], dtick=1, gridcolor="#E8ECF4"),
            legend=dict(orientation="h", y=1.12), font=dict(color="#53627D"),
        )
        radar = go.Figure()
        closed_ids = dimension_ids + [dimension_ids[0]]
        radar.add_trace(go.Scatterpolar(r=[dimensions_a[item]["score"] for item in closed_ids], theta=closed_ids, fill="toself", name=label_a, line_color="#6366F1", opacity=.72))
        radar.add_trace(go.Scatterpolar(r=[dimensions_b[item]["score"] for item in closed_ids], theta=closed_ids, fill="toself", name=label_b, line_color="#14B8A6", opacity=.55))
        radar.update_layout(height=410, margin=dict(l=35, r=35, t=35, b=25), paper_bgcolor="rgba(0,0,0,0)", polar=dict(radialaxis=dict(range=[0, 6], dtick=1)), legend=dict(orientation="h", y=1.12))
        chart_columns = st.columns([1.25, 1], gap="large")
        with chart_columns[0]:
            st.markdown(f"#### {t('维度得分并列图', 'Side-by-side dimension scores')}")
            st.plotly_chart(bar, width="stretch", config={"displayModeBar": False})
        with chart_columns[1]:
            st.markdown(f"#### {t('教育质量叠加画像', 'Overlay quality profile')}")
            st.plotly_chart(radar, width="stretch", config={"displayModeBar": False})

    with dimension_tab:
        table_rows = [
            {
                t("维度", "Dimension"): f"{row['id']} {row['name_a']}",
                label_a: f"{row['score_a']} / 6 · {row['evidence_a']}",
                label_b: f"{row['score_b']} / 6 · {row['evidence_b']}",
                "Δ A−B": row["delta"],
                t("领先", "Lead"): row["lead"],
            }
            for row in comparison["rows"]
        ]
        st.dataframe(table_rows, width="stretch", hide_index=True)
        delta_chart = go.Figure(go.Bar(
            x=[row["delta"] for row in comparison["rows"]],
            y=[row["id"] for row in comparison["rows"]],
            orientation="h",
            marker_color=["#6366F1" if row["delta"] > 0 else "#14B8A6" if row["delta"] < 0 else "#CBD5E1" for row in comparison["rows"]],
            text=[f"{row['delta']:+d}" for row in comparison["rows"]],
        ))
        delta_chart.update_layout(height=390, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(range=[-5.5, 5.5], zeroline=True, zerolinecolor="#17233D", gridcolor="#E8ECF4"), yaxis=dict(autorange="reversed"))
        st.plotly_chart(delta_chart, width="stretch", config={"displayModeBar": False})
        for row in comparison["rows"]:
            with st.expander(f"{row['id']} · {row['name_a']}　{label_a} {row['score_a']}/6 ↔ {label_b} {row['score_b']}/6"):
                a_col, b_col = st.columns(2, gap="large")
                with a_col:
                    st.markdown(f"**{label_a} · {t('下一步', 'Next move')}**")
                    st.write(row["improvement_a"])
                with b_col:
                    st.markdown(f"**{label_b} · {t('下一步', 'Next move')}**")
                    st.write(row["improvement_b"])

    with benchmark_tab:
        benchmark_chart = go.Figure()
        benchmark_chart.add_trace(go.Bar(name=label_a, x=dimension_ids, y=[dimensions_a[item]["score"] for item in dimension_ids], marker_color="#6366F1"))
        benchmark_chart.add_trace(go.Bar(name=label_b, x=dimension_ids, y=[dimensions_b[item]["score"] for item in dimension_ids], marker_color="#14B8A6"))
        benchmark_chart.add_trace(go.Scatter(name=t("优秀案例均值", "Excellence average"), x=dimension_ids, y=list(portfolio_a["average_profile"].values()), mode="lines+markers", line=dict(color="#F59E0B", width=3, dash="dot")))
        benchmark_chart.update_layout(barmode="group", height=430, margin=dict(l=10, r=10, t=35, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis=dict(range=[0, 6.4], dtick=1, gridcolor="#E8ECF4"), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(benchmark_chart, width="stretch", config={"displayModeBar": False})
        match_columns = st.columns(3, gap="medium")
        with match_columns[0]:
            st.metric(t("基准案例数", "Benchmark cases"), len(portfolio_a["cases"]))
        with match_columns[1]:
            st.metric(f"{label_a} · {t('最相近', 'Closest')}", f"{portfolio_a['best_match']['case']['team']} {portfolio_a['best_match']['case']['year']}", f"{portfolio_a['best_match']['similarity']:.0f}%")
        with match_columns[2]:
            st.metric(f"{label_b} · {t('最相近', 'Closest')}", f"{portfolio_b['best_match']['case']['team']} {portfolio_b['best_match']['case']['year']}", f"{portfolio_b['best_match']['similarity']:.0f}%")
        st.caption(t("案例十维画像是 GEM-EduScore 基于公开 Wiki 证据建立的分析值，不是 iGEM 官方评分。", "Case profiles are GEM-EduScore analyses of public Wiki evidence, not official iGEM scores."))

    with learning_tab:
        st.markdown(f"### {t('互相借鉴路线', 'Cross-learning roadmap')}")
        for index, recommendation in enumerate(comparison["recommendations"], 1):
            with st.container(border=True):
                st.markdown(f"**{index:02d}**　{recommendation}")
        evidence_columns = st.columns(2, gap="large")
        for column, label, dashboard in ((evidence_columns[0], label_a, dashboard_a), (evidence_columns[1], label_b, dashboard_b)):
            with column:
                st.markdown(f"#### {label}")
                st.write(dashboard["summary"])
                st.markdown(f"**{t('主要证据缺口', 'Key evidence gaps')}**")
                for item in dashboard["evidence_profile"]["missing_evidence"][:5]:
                    st.markdown(f"- {item}")

    with report_tab:
        comparison_markdown = format_comparison_markdown(comparison, dashboard_a, dashboard_b, language)
        sources_a = wiki_pages_from_info(state["info_a"])
        sources_b = wiki_pages_from_info(state["info_b"])
        language_suffix = {"zh": "ZH", "en": "EN", "bilingual": "Bilingual"}[language]
        file_base = f"GEM-EduScore_Project_Comparison_{language_suffix}"
        try:
            pdf_bytes = cached_comparison_pdf(comparison, dashboard_a, dashboard_b, language, sources_a, sources_b)
            docx_bytes = cached_comparison_docx(comparison, dashboard_a, dashboard_b, language, sources_a, sources_b)
            download_columns = st.columns(3, gap="small")
            with download_columns[0]:
                st.download_button(
                    t("下载对比报告 Markdown", "Download comparison Markdown"),
                    data=comparison_markdown,
                    file_name=f"{file_base}.md",
                    mime="text/markdown",
                    width="stretch",
                    key=f"comparison_download_markdown_{language}",
                )
            with download_columns[1]:
                st.download_button(
                    t("下载对比报告 PDF", "Download comparison PDF"),
                    data=pdf_bytes,
                    file_name=f"{file_base}.pdf",
                    mime="application/pdf",
                    width="stretch",
                    key=f"comparison_download_pdf_{language}",
                )
            with download_columns[2]:
                st.download_button(
                    t("下载对比报告 Word", "Download comparison Word"),
                    data=docx_bytes,
                    file_name=f"{file_base}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    width="stretch",
                    key=f"comparison_download_docx_{language}",
                )
        except Exception as exc:
            st.download_button(
                t("下载对比报告 Markdown", "Download comparison Markdown"),
                data=comparison_markdown,
                file_name=f"{file_base}.md",
                mime="text/markdown",
                width="stretch",
                key=f"comparison_download_markdown_fallback_{language}",
            )
            st.warning(t("PDF / Word 对比报告暂时无法生成，请重新启动桌面入口后再试。", "PDF / Word comparison exports are temporarily unavailable. Restart the desktop launcher and try again."))
            st.caption(str(exc))

        report_a_base = result_a.localized_reports.get(language, result_a.report_markdown)
        report_b_base = result_b.localized_reports.get(language, result_b.report_markdown)
        report_a = append_wiki_sources(report_a_base, sources_a, language)
        report_b = append_wiki_sources(report_b_base, sources_b, language)
        with st.expander(f"{label_a} · {t('完整评估报告', 'Full evaluation report')}", expanded=True):
            st.markdown(report_a)
        with st.expander(f"{label_b} · {t('完整评估报告', 'Full evaluation report')}"):
            st.markdown(report_b)
        with st.expander(t("来源与运行详情", "Source and run details")):
            for label, info, result in (
                (label_a, state["info_a"], result_a),
                (label_b, state["info_b"], result_b),
            ):
                st.markdown(f"**{label}**")
                st.write(f"- {t('来源', 'Source')}: {info.get('name', '—')}")
                st.write(f"- {t('字符数', 'Characters')}: {info.get('characters', '—')}")
                st.write(f"- {t('模型', 'Model')}: {result.model}")
                for page in wiki_pages_from_info(info):
                    st.markdown(f"  - [{page.get('title', 'Wiki page')}]({page.get('url', '')})")


def main() -> None:
    inject_styles()
    render_brand()
    render_hero()
    if st.session_state.pop("evaluation_reset_notice", False):
        st.toast("本次评估已停止，输入与结果已清空。", icon=":material/check_circle:")
    restored_title = st.session_state.pop("history_restored_notice", None)
    if restored_title:
        st.toast(f"已重新打开：{restored_title}", icon=":material/history:")
    workspace_column, tutorial_column, history_column = st.columns(
        [4.15, 1.05, 1.2], gap="small", vertical_alignment="center"
    )
    with history_column:
        render_history_popover()
    with tutorial_column:
        if st.button(
            "使用教程",
            icon=":material/play_circle:",
            width="stretch",
            key="open_tutorial_video",
            help="打开视频教程；播放器支持拖动进度。",
        ):
            render_tutorial_dialog()
    with workspace_column:
        workspace = st.radio(
            "分析工作台",
            ["单项目深度评估", "双项目对比分析"],
            horizontal=True,
            label_visibility="collapsed",
            key="analysis_workspace",
        )
    if workspace == "双项目对比分析":
        render_comparison_panel()
        if st.session_state.get("evaluation_ready") and st.session_state.get("result_mode") == "comparison":
            render_project_comparison()
    else:
        render_input_panel()
        if st.session_state.get("evaluation_ready") and st.session_state.get("result_mode") != "comparison":
            if st.session_state.get("result_mode") == "live":
                render_live_report()
            else:
                render_results()
    st.markdown(
        '<div class="footer-note">GEM-EduScore is a self-built diagnostic prototype, not an official iGEM scoring system.</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
