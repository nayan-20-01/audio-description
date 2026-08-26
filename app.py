"""app.py — Streamlit frontend for the NPTEL Audio Description tool."""

import time
import requests
import streamlit as st

st.set_page_config(
    page_title="NPTEL Audio Description",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(160deg, #F7F9FC 0%, #FAFAF8 50%, #F5F7FA 100%);
        }
        html, body, p, span, div, label {
            color: #1F2A3C;
        }
        div.block-container {
            padding-top: 3rem;
            max-width: 1200px;
        }
        header[data-testid="stHeader"] { background: transparent; }

        .badge-pill {
            display: inline-block;
            background: rgba(245, 130, 31, 0.10);
            border: 1px solid rgba(245, 130, 31, 0.45);
            color: #C9660F;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            padding: 0.3rem 0.9rem;
            border-radius: 999px;
            margin-bottom: 1.2rem;
        }

        .pitch h1 {
            color: #12233F;
            font-size: 2.7rem;
            font-weight: 700;
            line-height: 1.2;
            margin: 0 0 1rem 0;
        }
        .pitch h1 .highlight { color: #F5821F; }
        .pitch p.subtitle {
            color: #5C6B7A;
            font-size: 1.05rem;
            line-height: 1.6;
            max-width: 480px;
            margin-bottom: 1rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #FFFFFF;
            border: 1px solid #E3E7EE !important;
            border-radius: 16px !important;
            padding: 0.5rem 0.5rem;
            box-shadow: 0 8px 24px rgba(18, 35, 63, 0.07);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] h3 {
            color: #12233F;
            margin-top: 0.5rem;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] .caption-text {
            color: #5C6B7A;
            font-size: 0.85rem;
        }

        div[data-testid="stFileUploaderDropzone"] {
            background-color: #FAFAF8;
            border: 1.5px dashed #C9D2DE;
            border-radius: 10px;
        }
        div[data-testid="stFileUploaderDropzone"] span,
        div[data-testid="stFileUploaderDropzone"] small,
        div[data-testid="stFileUploaderDropzone"] p {
            color: #5C6B7A !important;
        }

        .stButton>button, .stDownloadButton>button {
            background-color: #1B3A5C;
            color: #FFFFFF;
            border-radius: 6px;
            border: none;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
        }
        .stButton>button:hover, .stDownloadButton>button:hover {
            background-color: #F5821F;
            color: #FFFFFF;
        }
        .stButton>button:disabled, .stDownloadButton>button:disabled {
            background-color: #EDEFF3;
            color: #A6AEBB;
        }

        div[data-testid="stProgress"] > div > div > div {
            background-color: #F5821F;
        }

        div[data-testid="stMetricValue"] { color: #12233F; }
        div[data-testid="stMetricLabel"] { color: #5C6B7A; }

        div[data-testid="stAlert"] {
            background-color: rgba(46, 125, 79, 0.10);
            color: #1F7A47;
        }

        .how-header {
            text-align: center;
            margin: 4rem 0 2.5rem 0;
        }
        .how-header .badge-pill { margin-bottom: 1rem; }
        .how-header h2 {
            color: #12233F;
            font-size: 2.2rem;
            font-weight: 700;
            margin: 0 0 0.7rem 0;
        }
        .how-header h2 .highlight { color: #F5821F; }
        .how-header p {
            color: #5C6B7A;
            font-size: 1rem;
            max-width: 480px;
            margin: 0 auto;
            line-height: 1.5;
        }

        .how-card {
            position: relative;
            background: #FFFFFF;
            border: 1px solid #E3E7EE;
            border-radius: 14px;
            padding: 1.8rem 1.2rem;
            text-align: center;
            height: 100%;
            box-shadow: 0 6px 18px rgba(18, 35, 63, 0.06);
        }
        .how-card .circle {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 52px; height: 52px;
            border-radius: 50%;
            background: #F5821F;
            color: #FFFFFF;
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 1rem;
            box-shadow: 0 0 0 6px rgba(245, 130, 31, 0.12);
        }
        .how-card .how-title {
            color: #12233F;
            font-weight: 700;
            font-size: 1.05rem;
            margin-bottom: 0.5rem;
        }
        .how-card .how-desc {
            color: #5C6B7A;
            font-size: 0.88rem;
            line-height: 1.5;
        }
        .how-card.connected::before {
            content: '';
            position: absolute;
            top: 46px;
            left: -1.6rem;
            width: 1.6rem;
            height: 2px;
            background: linear-gradient(to right, rgba(245,130,31,0.05), rgba(245,130,31,0.55));
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Pull the URL from Streamlit Secrets. If it doesn't exist, default to localhost.
if "API_BASE_URL" in st.secrets:
    API_BASE_URL = st.secrets["API_BASE_URL"]
else:
    API_BASE_URL = "http://localhost:8000"

STAGE_LABELS = {
    "queued": "Queued",
    "extracting_audio": "Extracting audio",
    "detecting_silence": "Detecting silence",
    "detecting_scenes": "Detecting board changes",
    "reading_board": "Reading board content",
    "generating_descriptions": "Generating descriptions",
    "synthesizing_audio": "Synthesizing audio",
    "assembling_video": "Assembling video",
}
STAGE_ORDER = list(STAGE_LABELS.keys())


def upload_video(file) -> str:
    response = requests.post(
        f"{API_BASE_URL}/upload",
        files={"file": (file.name, file.getvalue())},
    )
    
    # If the tunnel rejects it, print the exact error on the screen!
    if response.status_code != 200:
        st.error(f"Tunnel rejected the file! Status Code: {response.status_code}")
        st.error(f"Message from tunnel: {response.text}")
        st.stop()
        
    return response.json()["job_id"]

def poll_job(job_id, status_placeholder, progress_bar):
    while True:
        response = requests.get(f"{API_BASE_URL}/status/{job_id}")
        response.raise_for_status()
        data = response.json()

        stage = data.get("stage")
        if stage in STAGE_ORDER:
            status_placeholder.markdown(f"**{STAGE_LABELS[stage]}...**")
            progress_bar.progress((STAGE_ORDER.index(stage) + 1) / len(STAGE_ORDER))

        if data["status"] == "complete":
            return data
        if data["status"] == "failed":
            raise RuntimeError(data.get("error", "Processing failed"))

        time.sleep(1.5)


if "job_state" not in st.session_state:
    st.session_state.job_state = "idle"  # idle | processing | complete
if "job_summary" not in st.session_state:
    st.session_state.job_summary = None

col_left, col_right = st.columns([1.2, 1], gap="large")

with col_left:
    st.markdown(
        """
        <div class="pitch">
            <span class="badge-pill">● CDAC · NPTEL ACCESSIBILITY</span>
            <h1>NPTEL <span class="highlight">Audio Description</span></h1>
            <p class="subtitle">
                Automatically narrates board equations during silent pauses in NPTEL
                lecture videos — so visually impaired and auditory learners never miss
                what's written on the board.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_right:
    with st.container(border=True):
        if st.session_state.job_state == "idle":
            st.markdown("### Upload a lecture video")
            st.markdown(
                '<p class="caption-text">MP4, MKV, or AVI — up to 200MB per file.</p>',
                unsafe_allow_html=True,
            )
            uploaded_file = st.file_uploader(
                "Upload a lecture video",
                type=["mp4", "mkv", "avi"],
                label_visibility="collapsed",
            )

            if uploaded_file is not None:
                st.write("")
                if st.button("Process video"):
                    st.session_state.job_id = upload_video(uploaded_file)
                    st.session_state.job_state = "processing"
                    st.session_state.uploaded_filename = uploaded_file.name
                    st.rerun()

        elif st.session_state.job_state == "processing":
            st.markdown("### Processing")
            st.markdown(f"**File:** {st.session_state.uploaded_filename}")
            st.write("")

            progress_bar = st.progress(0)
            status_placeholder = st.empty()

            try:
                summary = poll_job(st.session_state.job_id, status_placeholder, progress_bar)
                st.session_state.job_summary = summary
                st.session_state.job_state = "complete"
            except Exception as exc:
                st.session_state.job_error = str(exc)
                st.session_state.job_state = "failed"
            st.rerun()

        elif st.session_state.job_state == "failed":
            st.error(st.session_state.get("job_error", "Processing failed."))
            if st.button("Try again"):
                st.session_state.job_state = "idle"
                st.rerun()

        elif st.session_state.job_state == "complete":
            st.markdown("### Done")
            st.success("Descriptions have been added to the video.")
            st.write("")

            summary = st.session_state.job_summary
            m1, m2 = st.columns(2)
            m1.metric("Descriptions generated", summary["segments_generated"])
            m2.metric(
                "Audio added",
                f"{summary['audio_added_seconds'] // 60}m "
                f"{summary['audio_added_seconds'] % 60}s",
            )

            st.write("")

            file_response = requests.get(f"{API_BASE_URL}/download/{st.session_state.job_id}")
            st.download_button(
                "Download accessible video",
                data=file_response.content,
                file_name="accessible_" + st.session_state.get("uploaded_filename", "video.mp4"),
            )

            st.write("")
            if st.button("Process another video"):
                st.session_state.job_state = "idle"
                st.session_state.job_summary = None
                st.rerun()

st.markdown(
    """
    <div class="how-header">
        <span class="badge-pill">HOW IT WORKS</span>
        <h2>From Upload to <span class="highlight">Accessible</span> in 3 Steps</h2>
        <p>Simple, fast, and fully automated — no technical knowledge required.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

how_col1, how_col2, how_col3 = st.columns(3, gap="medium")

with how_col1:
    st.markdown(
        """
        <div class="how-card">
            <div class="circle">1</div>
            <div class="how-title">Upload Your Video</div>
            <div class="how-desc">Drop in an MP4, MKV, or AVI lecture file — up to 200MB.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with how_col2:
    st.markdown(
        """
        <div class="how-card connected">
            <div class="circle">2</div>
            <div class="how-title">We Process It Automatically</div>
            <div class="how-desc">Silence is detected, the board is read, and descriptions are generated — no setup needed.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with how_col3:
    st.markdown(
        """
        <div class="how-card connected">
            <div class="circle">3</div>
            <div class="how-title">Download & Share</div>
            <div class="how-desc">Get back the same video with spoken descriptions added during silent pauses.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
