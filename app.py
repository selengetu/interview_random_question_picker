import json
import random
from datetime import datetime
from pathlib import Path

import streamlit as st

QUESTIONS_FILE = Path("questions.json")
DEFAULT_QUESTIONS_FILE = Path("default_questions.json")


def load_questions() -> dict:
    if not QUESTIONS_FILE.exists():
        defaults = json.loads(DEFAULT_QUESTIONS_FILE.read_text()) if DEFAULT_QUESTIONS_FILE.exists() else {}
        QUESTIONS_FILE.write_text(json.dumps(defaults, indent=2))
    return json.loads(QUESTIONS_FILE.read_text())


def save_questions(data: dict):
    QUESTIONS_FILE.write_text(json.dumps(data, indent=2))


# --- Session state init ---
if "history" not in st.session_state:
    st.session_state.history = []
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "current_category" not in st.session_state:
    st.session_state.current_category = None
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None

# --- App layout ---
st.set_page_config(page_title="Interview Question Picker", page_icon="🎯", layout="centered")
st.title("🎯 Interview Question Picker")

practice_tab, manage_tab, history_tab = st.tabs(["Practice", "Manage Questions", "History"])

# ── Practice tab ─────────────────────────────────────────────────────────────
with practice_tab:
    questions = load_questions()
    categories = list(questions.keys())

    col_select, col_surprise = st.columns([3, 1])

    with col_select:
        options = ["Any category"] + categories
        selected = st.selectbox("Category", options, label_visibility="collapsed")

    with col_surprise:
        surprise = st.button("🎲 Surprise me", use_container_width=True)

    get_q = st.button("Get question", type="primary", use_container_width=True)

    if surprise:
        cat = random.choice(categories)
        pool = questions[cat]
        if pool:
            q = random.choice(pool)
            st.session_state.current_question = q
            st.session_state.current_category = cat
            st.session_state.history.append(
                {"category": cat, "question": q, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")}
            )

    elif get_q:
        if selected == "Any category":
            cat = random.choice(categories)
            pool = questions[cat]
        else:
            cat = selected
            pool = questions[cat]

        if pool:
            q = random.choice(pool)
            st.session_state.current_question = q
            st.session_state.current_category = cat
            st.session_state.history.append(
                {"category": cat, "question": q, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")}
            )
        else:
            st.warning("That category has no questions yet. Add some in the Manage tab.")

    if st.session_state.current_question:
        cat = st.session_state.current_category
        pool_size = len(questions.get(cat, []))
        st.caption(f"**{cat}** · {pool_size} question{'s' if pool_size != 1 else ''} in pool")
        st.info(st.session_state.current_question)

# ── Manage Questions tab ──────────────────────────────────────────────────────
with manage_tab:
    questions = load_questions()

    st.subheader("Edit questions by category")
    st.caption("One question per line. Save after editing.")

    for cat in list(questions.keys()):
        with st.expander(cat, expanded=False):
            new_text = st.text_area(
                "Questions",
                value="\n".join(questions[cat]),
                height=200,
                key=f"textarea_{cat}",
                label_visibility="collapsed",
            )

            col_save, col_delete = st.columns([1, 1])

            with col_save:
                if st.button("Save", key=f"save_{cat}", use_container_width=True):
                    updated = [line.strip() for line in new_text.splitlines() if line.strip()]
                    questions[cat] = updated
                    save_questions(questions)
                    st.success("Saved.")

            with col_delete:
                if st.session_state.confirm_delete == cat:
                    st.warning(f"Delete **{cat}**?")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("Yes, delete", key=f"confirm_yes_{cat}", use_container_width=True):
                            del questions[cat]
                            save_questions(questions)
                            st.session_state.confirm_delete = None
                            st.rerun()
                    with col_no:
                        if st.button("Cancel", key=f"confirm_no_{cat}", use_container_width=True):
                            st.session_state.confirm_delete = None
                            st.rerun()
                else:
                    if st.button("Delete category", key=f"delete_{cat}", use_container_width=True):
                        st.session_state.confirm_delete = cat
                        st.rerun()

    st.divider()
    st.subheader("Add new category")
    new_cat = st.text_input("Category name", placeholder="e.g. Statistics")
    if st.button("Add category", type="primary"):
        name = new_cat.strip()
        if not name:
            st.warning("Please enter a category name.")
        elif name in questions:
            st.warning("That category already exists.")
        else:
            questions[name] = []
            save_questions(questions)
            st.success(f"Category **{name}** added. Open it above to add questions.")
            st.rerun()

# ── History tab ───────────────────────────────────────────────────────────────
with history_tab:
    if not st.session_state.history:
        st.info("No questions shown yet this session. Head to the Practice tab to get started.")
    else:
        if st.button("Clear history"):
            st.session_state.history = []
            st.rerun()

        for entry in reversed(st.session_state.history):
            st.markdown(
                f"**[{entry['category']}]** &nbsp; <span style='color:gray;font-size:0.85em'>{entry['timestamp']}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(entry["question"])
            st.divider()
