import streamlit as st
import json
import base64
import os
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


def save_letters(letters):
    with open(DATA_PATH, "w") as f:
        json.dump({"letters": letters}, f, indent=2)


def image_to_data_uri(uploaded_file, max_size=900):
    img = Image.open(uploaded_file).convert("RGB")
    img.thumbnail((max_size, max_size))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


if "letters" not in st.session_state:
    st.session_state.letters = load_letters()
if "selected" not in st.session_state:
    st.session_state.selected = None
if "edit_unlocked" not in st.session_state:
    st.session_state.edit_unlocked = False

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;1,9..144,500;1,9..144,600&family=Literata:ital,opsz@0,16..30;1,16..30&family=Caveat:wght@500;600;700&display=swap" rel="stylesheet">
    <style>
        html, body, [class*="css"]  { font-family: 'Literata', serif; }
        .stApp {
            background-color: #F7EFE4;
            background-image:
                repeating-linear-gradient(0deg, rgba(140,75,86,0.09) 0px, rgba(140,75,86,0.09) 2px, transparent 2px, transparent 38px),
                repeating-linear-gradient(90deg, rgba(140,75,86,0.09) 0px, rgba(140,75,86,0.09) 2px, transparent 2px, transparent 38px);
        }
        .lfyh-eyebrow {
            font-family: 'Caveat', cursive; font-size: 24px; color: #8C4B56;
            display:block; text-align:center; transform: rotate(-1.5deg);
        }
        .lfyh-title {
            font-family: 'Fraunces', serif; font-style: italic; font-weight: 600;
            font-size: 52px; text-align:center; color:#2E2130; margin: 4px 0 4px;
        }
        .lfyh-title .heart { color:#BE6A74; font-style:normal; }
        .lfyh-lede {
            text-align:center; max-width:560px; margin:0 auto 8px; color:rgba(46,33,48,0.72);
            font-size:16px; line-height:1.7;
        }
        .lfyh-prompt {
            text-align:center; font-family:'Fraunces', serif; font-style:italic; font-weight:600;
            font-size:22px; color:#2E2130; margin: 24px 0 22px;
        }
        div.stButton > button {
            background: #FFFCF6;
            border: 1px solid rgba(46,33,48,0.12);
            border-radius: 14px;
            padding: 22px 8px 16px;
            font-family: 'Fraunces', serif;
            font-weight: 600;
            font-size: 15px;
            color: #2E2130;
            width: 100%;
            box-shadow: 0 12px 24px -14px rgba(46,33,48,0.35);
            transition: transform 0.15s ease;
        }
        div.stButton > button:hover { border-color:#BE6A74; color:#8C4B56; transform: translateY(-3px); }
        .back-link button {
            background: transparent !important; box-shadow:none !important; border:none !important;
            font-family:'Caveat', cursive !important; font-size:20px !important; color:#8C4B56 !important;
            width:auto !important; padding: 0 !important;
        }
        .letter-paper {
            background:#FFFCF8;
            background-image: linear-gradient(rgba(46,33,48,0.06) 1px, transparent 1px);
            background-size: 100% 32px;
            border-radius: 6px;
            padding: 40px 44px;
            box-shadow: 0 24px 50px -20px rgba(20,10,20,0.35);
            position: relative;
        }
        .letter-paper::before {
            content:""; position:absolute; top:-10px; left:calc(50% - 45px);
            width:90px; height:26px; background: rgba(196,168,120,0.55);
            box-shadow: 0 1px 3px rgba(0,0,0,0.12); transform: rotate(-1.5deg);
        }
        .letter-eyebrow { font-family:'Caveat', cursive; font-size:20px; color:#8C4B56; }
        .letter-title { font-family:'Fraunces', serif; font-style:italic; font-weight:600; font-size:32px; color:#2E2130; margin: 2px 0 18px; }
        .letter-body p { font-size:16px; line-height:1.9; color:rgba(46,33,48,0.86); }
        .letter-sign { font-family:'Caveat', cursive; font-size:24px; color:#8C4B56; margin-top:18px; }
        .taped-photo {
            position:relative; background:#fff; padding:12px 12px 30px;
            box-shadow: 0 20px 40px -18px rgba(20,10,20,0.45);
            transform: rotate(-2.5deg); max-width: 300px; margin: 26px auto 10px;
        }
        .taped-photo::before, .taped-photo::after {
            content:""; position:absolute; top:-12px; width:64px; height:22px;
            background: rgba(232,216,182,0.85); box-shadow: 0 1px 3px rgba(0,0,0,0.15);
        }
        .taped-photo::before { left:-16px; transform: rotate(-10deg); }
        .taped-photo::after { right:-16px; transform: rotate(10deg); }
        .taped-photo img { width:100%; display:block; }
        .empty-photo {
            border: 1.5px dashed rgba(46,33,48,0.2); border-radius: 6px;
            aspect-ratio: 4/5; display:flex; align-items:center; justify-content:center;
            color: rgba(46,33,48,0.35); font-size: 13px; max-width: 300px; margin: 26px auto 10px;
        }
        .mood-emoji { font-size: 30px; display:block; margin-bottom: 4px; }
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
    'the one who needs to hear it again. Open whichever one finds you today.</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# VIEW MODE
# ---------------------------------------------------------------------------

def render_reader():
    letters = st.session_state.letters
    available = [l for l in letters if l["title"].strip()]

    st.markdown("<p style='text-align:center;color:#8C4B56;letter-spacing:0.1em;text-transform:uppercase;font-size:13px;'>— choose a letter —</p>", unsafe_allow_html=True)

    cols = st.columns(4)
    for i, letter in enumerate(available):
        with cols[i % 4]:
            label = f"{letter['seal']}\n\n{letter['title']}"
            if st.button(label, key=f"open_{letter['key']}"):
                st.session_state.selected = letter["key"]

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.selected:
        letter = next((l for l in available if l["key"] == st.session_state.selected), None)
        if letter:
            left, right = st.columns([1, 1.6], gap="large")
            with left:
                if letter.get("photo"):
                    st.markdown(f'<div class="polaroid"><img src="{letter["photo"]}"></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="empty-photo">no photo added</div>', unsafe_allow_html=True)
            with right:
                body_html = "".join(f"<p>{p}</p>" for p in letter["body"]) or "<p style='opacity:0.5;font-style:italic;'>This letter hasn't been written yet.</p>"
                st.markdown(
                    f"""
                    <div class="letter-paper">
                        <span class="letter-eyebrow">{letter['when']} {letter['title'].lower()} …</span>
                        <div class="letter-title">{letter['title']}</div>
                        <div class="letter-body">{body_html}</div>
                        <div class="letter-sign">{letter['sign']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    elif not available:
        st.info("No letters have been written yet. The owner can unlock editing from the sidebar.")


# ---------------------------------------------------------------------------
# EDIT MODE
# ---------------------------------------------------------------------------

def render_editor():
    letters = st.session_state.letters
    st.markdown("### Write your letters")
    st.caption("Changes save when you press **Save this letter**. Readers with the link only ever see this in view mode.")

    for idx, letter in enumerate(letters):
        with st.expander(f"{letter['seal'] or '?'}  {letter['title'] or 'Untitled mood'}", expanded=False):
            c1, c2 = st.columns([3, 1])
            with c1:
                title = st.text_input("Mood title", value=letter["title"], key=f"title_{idx}")
            with c2:
                seal = st.text_input("Seal letter", value=letter["seal"], max_chars=2, key=f"seal_{idx}")
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
                uploaded = st.file_uploader("Photo for this letter", type=["png", "jpg", "jpeg"], key=f"upload_{idx}")
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
    "<div style='text-align:center;color:rgba(46,33,48,0.5);font-size:13px;padding:40px 0 10px;'>"
    "<span style='font-family:Caveat,cursive;font-size:18px;color:#8C4B56;'>with all my love</span><br>"
    "a quiet little corner of the internet, made for one heart in particular.</div>",
    unsafe_allow_html=True,
)
