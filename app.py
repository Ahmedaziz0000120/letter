import streamlit as st
import json
import base64
import requests
from pathlib import Path
from io import BytesIO
from PIL import Image

DATA_PATH = Path(__file__).parent / "letters.json"

st.set_page_config(page_title="Letters for your Heart", page_icon="💌", layout="wide")

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_letters():
    with open(DATA_PATH, "r") as f:
        return json.load(f)["letters"]


def push_to_github(content_str):
    """Commit the current letters.json back to the GitHub repo so it survives
    app restarts/redeploys, which wipe anything only saved to local disk."""
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")          # e.g. "ahmedaziz0000120/letter"
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    path = st.secrets.get("GITHUB_FILE_PATH", "letters.json")
    if not token or not repo:
        return None  # sync not configured — silently skip, local save still works this session

    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    try:
        r = requests.get(api_url, headers=headers, params={"ref": branch}, timeout=10)
        sha = r.json().get("sha") if r.status_code == 200 else None
        payload = {
            "message": "Update letters.json from the app",
            "content": base64.b64encode(content_str.encode()).decode(),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha
        r2 = requests.put(api_url, headers=headers, json=payload, timeout=10)
        return r2.status_code in (200, 201)
    except Exception:
        return False


def save_letters(letters):
    content = json.dumps({"letters": letters}, indent=2, ensure_ascii=False)
    with open(DATA_PATH, "w") as f:
        f.write(content)
    synced = push_to_github(content)
    if synced is True:
        st.toast("Saved and backed up to GitHub ✓", icon="💾")
    elif synced is False:
        st.toast("Saved locally, but GitHub backup failed — check your secrets", icon="⚠️")
    # synced is None => GitHub sync not configured, say nothing (expected for local dev)


def image_to_data_uri(uploaded_file, max_size=900):
    img = Image.open(uploaded_file).convert("RGB")
    img.thumbnail((max_size, max_size))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


# Big expressive emoji per mood, with a few sensible fallbacks so new moods
# the owner adds later still get *something* cute instead of a blank.
MOOD_EMOJI = {
    "happy": "😊💕",
    "sad": "😔",
    "lonely": "🥺",
    "exhausted": "😮\u200d💨",
    "angry": "😡",
    "overwhelmed": "😵\u200d💫",
    "missing_me": "🫂",
    "just_because": "🤍",
}
FALLBACK_EMOJI = ["💌", "🌷", "✨", "🎀"]


def emoji_for(letter):
    if letter.get("seal") and not letter["seal"].strip().isalnum():
        return letter["seal"]
    key = letter.get("key", "")
    if key in MOOD_EMOJI:
        return MOOD_EMOJI[key]
    return FALLBACK_EMOJI[hash(key) % len(FALLBACK_EMOJI)]


try:
    st.session_state.letters = load_letters()
except Exception:
    if "letters" not in st.session_state:
        st.session_state.letters = []
if "selected" not in st.session_state:
    st.session_state.selected = None
if "edit_unlocked" not in st.session_state:
    st.session_state.edit_unlocked = False

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

TILT = [-3, -1.5, 1.5, 3, -2, 2, -1, 1]

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;1,9..144,600&family=Literata:ital,opsz@0,16..30;1,16..30&family=Caveat:wght@500;600;700&family=Shadows+Into+Light&family=Baloo+2:wght@600;700&display=swap" rel="stylesheet">
    <style>
        :root { color-scheme: light only; }
        html, body, [class*="css"]  { font-family: 'Literata', serif; }
        [data-testid="stSidebar"] { background: #FFF6EF !important; }
        [data-testid="stSidebar"] * { color: #3B1F2B !important; }

        /* ---------- gingham backdrop ---------- */
        .stApp {
            background-color: #FFF3F6;
            background-image:
                repeating-linear-gradient(0deg,  rgba(255,255,255,0.75) 0px, rgba(255,255,255,0.75) 20px, transparent 20px, transparent 40px),
                repeating-linear-gradient(90deg, rgba(255,255,255,0.75) 0px, rgba(255,255,255,0.75) 20px, transparent 20px, transparent 40px),
                repeating-linear-gradient(0deg,  rgba(222,120,150,0.28) 0px, rgba(222,120,150,0.28) 20px, transparent 20px, transparent 40px),
                repeating-linear-gradient(90deg, rgba(222,120,150,0.28) 0px, rgba(222,120,150,0.28) 20px, transparent 20px, transparent 40px);
        }

        /* ---------- motion ---------- */
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(16px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes popIn {
            0%   { opacity: 0; transform: scale(0.65) rotate(-6deg); }
            70%  { opacity: 1; transform: scale(1.06) rotate(1deg); }
            100% { opacity: 1; transform: scale(1) rotate(0deg); }
        }
        @keyframes floatIn {
            from { opacity: 0; transform: translateY(24px) rotate(var(--tilt, 0deg)); }
            to   { opacity: 1; transform: translateY(0) rotate(var(--tilt, 0deg)); }
        }
        @keyframes wiggle {
            0%, 100% { transform: rotate(-3deg) scale(1.08); }
            50%      { transform: rotate(3deg) scale(1.08); }
        }
        @keyframes tapeShimmer {
            from { opacity: 0; transform: translateY(-6px) rotate(var(--taperot, -8deg)); }
            to   { opacity: 1; transform: translateY(0) rotate(var(--taperot, -8deg)); }
        }

        .lfyh-eyebrow {
            font-family: 'Caveat', cursive; font-size: 26px; color: #C24E70;
            display:block; text-align:center; transform: rotate(-1.5deg);
            animation: fadeInUp 0.6s ease both;
        }
        .lfyh-title {
            font-family: 'Fraunces', serif; font-style: italic; font-weight: 600;
            font-size: 54px; text-align:center; color:#3B1F2B; margin: 4px 0 4px;
            animation: fadeInUp 0.7s ease both;
        }
        .lfyh-title .heart { color:#E8607E; font-style:normal; display:inline-block; animation: wiggle 1.8s ease-in-out infinite; animation-delay: 1s; }
        .lfyh-lede {
            text-align:center; max-width:560px; margin:0 auto 8px; color:rgba(59,31,43,0.75);
            font-size:16px; line-height:1.7; animation: fadeInUp 0.8s ease both;
        }

        /* ---------- mood picker ---------- */
        .mood-grid-wrap {
            background-color: #EEF3E2;
            background-image:
                repeating-linear-gradient(0deg,  rgba(255,255,255,0.8) 0px, rgba(255,255,255,0.8) 20px, transparent 20px, transparent 40px),
                repeating-linear-gradient(90deg, rgba(255,255,255,0.8) 0px, rgba(255,255,255,0.8) 20px, transparent 20px, transparent 40px),
                repeating-linear-gradient(0deg,  rgba(150,181,110,0.4) 0px, rgba(150,181,110,0.4) 20px, transparent 20px, transparent 40px),
                repeating-linear-gradient(90deg, rgba(150,181,110,0.4) 0px, rgba(150,181,110,0.4) 20px, transparent 20px, transparent 40px);
            border-radius: 22px;
            padding: 34px 20px 26px;
            box-shadow: 0 26px 50px -28px rgba(59,20,35,0.35);
            margin: 10px 0 28px;
            animation: fadeInUp 0.6s ease both;
        }
        .mood-label {
            text-align:center; color:#2E2130; font-family:'Baloo 2', cursive;
            font-size:32px; font-weight:700; margin: 0 0 20px;
        }
        header[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
        .main .block-container { padding-top: 1.2rem !important; }

        div[data-testid="stButton"] { width: 100%; }
        div.stButton > button {
            min-height: 128px;
            display: flex !important;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .mood-grid-wrap div.stButton > button {
            min-height: 150px;
        }

        .mood-grid-wrap div.stButton > button {
            background: transparent;
            border: none;
            box-shadow: none;
            border-radius: 16px;
            padding: 26px 8px 14px;
            font-family: 'Baloo 2', cursive;
            font-weight: 600;
            font-size: 21px;
            color: #2E2130;
            width: 100%;
            position: relative;
            transition: transform 0.2s cubic-bezier(.34,1.56,.64,1);
            animation: popIn 0.5s cubic-bezier(.34,1.56,.64,1) both;
        }
        .mood-grid-wrap div.stButton > button p::first-line { font-size: 60px; line-height: 1.3; }
        .mood-grid-wrap div.stButton > button:hover {
            transform: translateY(-6px) scale(1.06);
            color: #2E2130;
        }
        .mood-grid-wrap div.stButton > button:active { transform: translateY(-2px) scale(0.98); }
        div.stButton > button {
            background: #FFFDFB;
            border: 2px solid rgba(226,110,140,0.35);
            border-radius: 20px;
            padding: 30px 10px 20px;
            font-family: 'Fraunces', serif;
            font-weight: 700;
            font-size: 16px;
            color: #3B1F2B;
            width: 100%;
            box-shadow: 0 14px 22px -14px rgba(200,60,100,0.45);
            transition: transform 0.2s cubic-bezier(.34,1.56,.64,1), box-shadow 0.2s ease, border-color 0.2s ease;
            animation: popIn 0.5s cubic-bezier(.34,1.56,.64,1) both;
            white-space: pre-line;
            gap: 8px;
        }
        div.stButton > button p { font-size: 16px !important; white-space: pre-line; line-height: 1.4; }
        div.stButton > button p::first-line { font-size: 42px; line-height: 1.6; }
        div.stButton > button:hover {
            border-color:#E8607E;
            color:#C24E70;
            transform: translateY(-6px) scale(1.04) rotate(-1deg);
            box-shadow: 0 20px 30px -14px rgba(200,60,100,0.55);
        }
        div.stButton > button:active { transform: translateY(-2px) scale(0.98); }

        .nav-link button {
            background: transparent !important; box-shadow:none !important; border:none !important;
            font-family:'Caveat', cursive !important; font-size:22px !important; color:#C24E70 !important;
            width:auto !important; padding: 4px 10px !important; animation: none !important;
        }
        .nav-link button:hover { color:#E8607E !important; transform: translateY(-1px) !important; text-decoration: underline; }

        /* ---------- editor readability (labels/expanders default to a pale grey) ---------- */
        [data-testid="stExpander"] summary, [data-testid="stExpander"] * { color: #3B1F2B !important; }
        [data-testid="stExpander"] { background: rgba(255,255,255,0.55); border-radius: 12px; }

        /* force light, readable form fields regardless of system/browser dark mode */
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stColorPicker"] input,
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea,
        [data-baseweb="base-input"] {
            background: #FFFDFB !important;
            color: #3B1F2B !important;
            border: 1px solid rgba(59,31,43,0.25) !important;
            -webkit-text-fill-color: #3B1F2B !important;
            caret-color: #3B1F2B !important;
        }
        [data-testid="stTextInput"] input::placeholder,
        [data-testid="stTextArea"] textarea::placeholder {
            color: rgba(59,31,43,0.4) !important;
            -webkit-text-fill-color: rgba(59,31,43,0.4) !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            background: rgba(255,255,255,0.6) !important;
            color: #3B1F2B !important;
        }
        [data-testid="stFileUploaderDropzone"] * { color: #3B1F2B !important; }
        [data-testid="stFileUploaderDropzoneInstructions"] span { color: rgba(59,31,43,0.6) !important; }
        .stTextInput label, .stTextArea label, .stFileUploader label,
        .stColorPicker label, .stForm label { color: #3B1F2B !important; font-weight: 600; }
        [data-testid="stCaptionContainer"] { color: rgba(59,31,43,0.7) !important; }
        h1, h2, h3, h4 { color: #3B1F2B !important; }

        /* ---------- letter paper, stamp edge ---------- */
        .letter-paper {
            background:#FFFCF8;
            background-image: linear-gradient(rgba(59,31,43,0.06) 1px, transparent 1px);
            background-size: 100% 32px;
            padding: 46px 46px 40px;
            border-radius: 10px;
            box-shadow: 0 26px 55px -22px rgba(59,20,35,0.4);
            position: relative;
            animation: fadeInUp 0.55s ease both;
            clip-path: polygon(
                0% 2.5%,3% 0%,6% 2.5%,9% 0%,12% 2.5%,15% 0%,18% 2.5%,21% 0%,24% 2.5%,27% 0%,30% 2.5%,33% 0%,36% 2.5%,39% 0%,42% 2.5%,45% 0%,48% 2.5%,51% 0%,54% 2.5%,57% 0%,60% 2.5%,63% 0%,66% 2.5%,69% 0%,72% 2.5%,75% 0%,78% 2.5%,81% 0%,84% 2.5%,87% 0%,90% 2.5%,93% 0%,96% 2.5%,99% 0%,100% 2.5%,
                100% 97.5%,97% 100%,94% 97.5%,91% 100%,88% 97.5%,85% 100%,82% 97.5%,79% 100%,76% 97.5%,73% 100%,70% 97.5%,67% 100%,64% 97.5%,61% 100%,58% 97.5%,55% 100%,52% 97.5%,49% 100%,46% 97.5%,43% 100%,40% 97.5%,37% 100%,34% 97.5%,31% 100%,28% 97.5%,25% 100%,22% 97.5%,19% 100%,16% 97.5%,13% 100%,10% 97.5%,7% 100%,4% 97.5%,1% 100%,0% 97.5%
            );
        }
        .letter-eyebrow { font-family:'Shadows Into Light', cursive; font-size:20px; color:#C24E70; }
        .letter-title { font-family:'Fraunces', serif; font-style:italic; font-weight:600; font-size:34px; color:#3B1F2B; margin: 2px 0 18px; }
        .letter-body p { font-size:16.5px; line-height:1.95; color:rgba(59,31,43,0.88); }
        .letter-sign { font-family:'Shadows Into Light', cursive; font-size:26px; color:#C24E70; margin-top:18px; }

        /* ---------- taped polaroid ---------- */
        .taped-photo {
            --tilt: -3deg; --taperot: -9deg;
            position:relative; background:#fff; padding:14px 14px 34px;
            box-shadow: 0 22px 44px -18px rgba(59,20,35,0.5);
            transform: rotate(var(--tilt));
            max-width: 300px; margin: 26px auto 10px;
            animation: floatIn 0.6s ease both;
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }
        .taped-photo:hover {
            transform: rotate(0deg) scale(1.03) translateY(-4px);
            box-shadow: 0 28px 50px -18px rgba(59,20,35,0.55);
        }
        .taped-photo::before {
            content:""; position:absolute; top:-14px; left:calc(50% - 46px);
            width:92px; height:26px;
            background: repeating-linear-gradient(45deg, rgba(232,207,163,0.85), rgba(232,207,163,0.85) 4px, rgba(216,186,138,0.85) 4px, rgba(216,186,138,0.85) 8px);
            box-shadow: 0 1px 3px rgba(0,0,0,0.15);
            transform: rotate(var(--taperot));
            animation: tapeShimmer 0.5s ease both;
            animation-delay: 0.15s;
            opacity: 0.9;
        }
        .taped-photo img { width:100%; display:block; cursor: zoom-in; }
        .taped-photo a { display:block; }
        .empty-photo {
            --tilt: -2deg;
            border: 2px dashed rgba(226,110,140,0.45); border-radius: 10px; background: rgba(255,255,255,0.5);
            aspect-ratio: 4/5; display:flex; align-items:center; justify-content:center; flex-direction: column; gap: 6px;
            color: rgba(59,31,43,0.4); font-size: 13px; max-width: 300px; margin: 26px auto 10px;
            transform: rotate(var(--tilt)); animation: floatIn 0.6s ease both; font-family:'Caveat', cursive; font-size: 18px;
        }

        /* mood grid emoji-forward buttons get a slight stagger via order in DOM already */

        /* ---------- final override: guarantee uniform mood-card sizing ----------
           (placed last so it always wins the cascade over earlier duplicate rules) */
        div.stButton > button {
            width: 100% !important;
            box-sizing: border-box !important;
            min-height: 150px !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            white-space: normal !important;
            text-align: center !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — edit access (only visible affordance for the owner)
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ✎ Owner access")
    if not st.session_state.edit_unlocked:
        pw = st.text_input("Edit password", type="password")
        if st.button("Unlock editing"):
            correct = st.secrets.get("EDIT_PASSWORD", "301205")
            if pw == correct:
                st.session_state.edit_unlocked = True
                st.rerun()
            else:
                st.error("That's not it.")
    else:
        st.success("Editing unlocked")
        if st.button("Lock & switch to reader view"):
            st.session_state.edit_unlocked = False
            st.rerun()

mode = "edit" if st.session_state.edit_unlocked else "view"

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown('<span class="lfyh-eyebrow">a small archive, just for you</span>', unsafe_allow_html=True)
st.markdown('<div class="lfyh-title">Letters for your <span class="heart">Heart</span> ♡</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="lfyh-lede">Every version of you deserves a letter — the happy one, the tired one, '
    'the one who needs to hear it again. Tell me how your heart feels today.</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# VIEW MODE
# ---------------------------------------------------------------------------

def render_reader():
    letters = st.session_state.letters
    available = [l for l in letters if l["title"].strip()]

    if st.session_state.selected:
        letter = next((l for l in available if l["key"] == st.session_state.selected), None)
    else:
        letter = None

    if letter:
        idx = available.index(letter)

        nav1, nav2, nav3 = st.columns([1, 6, 1])
        with nav1:
            st.markdown('<div class="nav-link">', unsafe_allow_html=True)
            if st.button("‹‹ back", key="restart_link"):
                st.session_state.selected = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with nav3:
            st.markdown('<div class="nav-link" style="text-align:right;">', unsafe_allow_html=True)
            if st.button("next ››", key="next_link"):
                nxt = available[(idx + 1) % len(available)]
                st.session_state.selected = nxt["key"]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        left, right = st.columns([1, 1.6], gap="large")
        tilt = TILT[idx % len(TILT)]
        with left:
            if letter.get("photo"):
                st.markdown(
                    f'<div class="taped-photo" style="--tilt:{tilt}deg;">'
                    f'<a href="{letter["photo"]}" target="_blank" title="Click to view full size">'
                    f'<img src="{letter["photo"]}"></a></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="empty-photo" style="--tilt:{tilt}deg;">🎞️<br>no photo added</div>',
                    unsafe_allow_html=True,
                )
        with right:
            body_html = "".join(f"<p>{p}</p>" for p in letter["body"]) or "<p style='opacity:0.5;font-style:italic;'>This letter hasn't been written yet.</p>"
            st.markdown(
                f"""
                <div class="letter-paper">
                    <span class="letter-eyebrow">{letter['when']} {letter['title'].lower()} …</span>
                    <div class="letter-title">{emoji_for(letter)}&nbsp; {letter['title']}</div>
                    <div class="letter-body">{body_html}</div>
                    <div class="letter-sign">{letter['sign']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        return

    st.markdown('<div class="mood-grid-wrap">', unsafe_allow_html=True)
    st.markdown('<p class="mood-label">Tell me how your heart feels.</p>', unsafe_allow_html=True)

    if not available:
        st.info("No letters have been written yet. The owner can unlock editing from the sidebar.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    cols = st.columns(4)
    for i, l in enumerate(available):
        with cols[i % 4]:
            st.markdown(f'<div class="mood-btn-{i}">', unsafe_allow_html=True)
            label = f"{emoji_for(l)}\n\n{l['title']}"
            if st.button(label, key=f"open_{l['key']}"):
                st.session_state.selected = l["key"]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# EDIT MODE
# ---------------------------------------------------------------------------

def render_editor():
    letters = st.session_state.letters
    st.markdown("### Write your letters")
    st.caption("Changes save when you press **Save this letter**. Readers with the link only ever see the reader view.")

    for idx, letter in enumerate(letters):
        with st.expander(f"{emoji_for(letter)}  {letter['title'] or 'Untitled mood'}", expanded=False):
            c1, c2 = st.columns([3, 1])
            with c1:
                title = st.text_input("Mood title", value=letter["title"], key=f"title_{idx}")
            with c2:
                seal = st.text_input("Seal / emoji", value=letter["seal"], max_chars=4, key=f"seal_{idx}")
            when = st.text_input("Opens with", value=letter["when"], key=f"when_{idx}")
            body_text = st.text_area(
                "Letter — one paragraph per line",
                value="\n".join(letter["body"]),
                height=180,
                key=f"body_{idx}",
            )
            sign = st.text_input("Sign-off", value=letter["sign"], key=f"sign_{idx}")

            photo_col1, photo_col2 = st.columns([1, 1])
            with photo_col1:
                uploaded = st.file_uploader("Photo for this letter", type=["png", "jpg", "jpeg", "webp"], key=f"upload_{idx}")
            with photo_col2:
                if letter.get("photo"):
                    st.image(letter["photo"], width=140)
                    if st.button("Remove photo", key=f"remove_photo_{idx}"):
                        letters[idx]["photo"] = None
                        save_letters(letters)
                        st.rerun()

            bcol1, bcol2 = st.columns([1, 1])
            with bcol1:
                if st.button("Save this letter", key=f"save_{idx}"):
                    letters[idx]["title"] = title
                    letters[idx]["seal"] = seal
                    letters[idx]["when"] = when
                    letters[idx]["body"] = [p for p in body_text.split("\n") if p.strip()]
                    letters[idx]["sign"] = sign
                    if uploaded is not None:
                        letters[idx]["photo"] = image_to_data_uri(uploaded)
                    save_letters(letters)
                    st.success("Saved.")
                    st.rerun()
            with bcol2:
                if st.button("Delete this letter", key=f"delete_{idx}"):
                    letters.pop(idx)
                    save_letters(letters)
                    st.rerun()

    st.markdown("---")
    with st.form("new_letter_form"):
        st.write("Add a new mood")
        new_title = st.text_input("Mood title", key="new_title")
        submitted = st.form_submit_button("Add letter")
        if submitted and new_title.strip():
            letters.append({
                "key": new_title.lower().replace(" ", "_"),
                "title": new_title,
                "when": "open this when you're",
                "seal": new_title[0].upper(),
                "body": [],
                "sign": "",
                "photo": None,
            })
            save_letters(letters)
            st.rerun()


if mode == "edit":
    render_editor()
else:
    render_reader()

st.markdown(
    "<div style='text-align:center;color:rgba(59,31,43,0.5);font-size:13px;padding:40px 0 10px;'>"
    "<span style='font-family:Caveat,cursive;font-size:18px;color:#C24E70;'>with all my love</span><br>"
    "a quiet little corner of the internet, made for one heart in particular.</div>",
    unsafe_allow_html=True,
)
