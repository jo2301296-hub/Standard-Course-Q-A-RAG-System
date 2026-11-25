import streamlit as st
import rag

st.set_page_config(page_title="Course Q&A Assistant", page_icon="🎓", layout="centered")

# ---------- Styling ----------
st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; max-width: 820px; }

    .hero {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 55%, #db2777 100%);
        padding: 1.6rem 1.8rem;
        border-radius: 18px;
        color: white;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 24px rgba(79, 70, 229, 0.25);
    }
    .hero h1 { margin: 0; font-size: 1.9rem; color: white; padding: 0; }
    .hero p  { margin: 0.4rem 0 0 0; opacity: 0.92; font-size: 1rem; }

    .welcome {
        border: 1px dashed rgba(124, 58, 237, 0.45);
        border-radius: 14px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .welcome h3 { margin: 0 0 0.3rem 0; }

    [data-testid="stChatMessage"] {
        border-radius: 14px;
        padding: 0.8rem 1rem;
    }

    .src-badge {
        display: inline-block;
        font-size: 0.78rem;
        padding: 0.1rem 0.55rem;
        border-radius: 999px;
        background: rgba(124, 58, 237, 0.14);
        color: #7c3aed;
        margin-right: 0.3rem;
    }

    div.stButton > button {
        border-radius: 10px;
        text-align: left;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown(
    """
    <div class="hero">
        <h1>🎓 Course Q&A Assistant</h1>
        <p>Ask questions about your course materials. Answers come only from your files, with sources.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- Sidebar ----------
courses = rag.list_courses()

with st.sidebar:
    st.header("⚙️ Settings")
    course = st.selectbox("Course", ["All"] + courses)
    k = st.slider("Passages to retrieve (Top-K)", 2, 8, 4)
    show_sources = st.toggle("Show sources", value=True)

    st.divider()
    st.caption(f"📚 {len(courses)} courses indexed")
    n_questions = sum(1 for m in st.session_state.messages if m["role"] == "user")
    st.caption(f"💬 {n_questions} questions asked")

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


def render_sources(chunks):
    st.markdown("**📎 Sources**")
    for i, c in enumerate(chunks, 1):
        m = c["meta"]
        page = f" · Page {m['page']}" if m["page"] else ""
        relevance = max(0.0, 1 - c["distance"]) * 100
        label = f"[{i}] {m['course']} / {m['file']}{page}  ·  {relevance:.0f}% match"
        with st.expander(label):
            st.caption(f"Distance: {c['distance']:.3f}")
            st.write(c["text"])


def ask_example(q: str):
    st.session_state.pending = q


# ---------- Input (read first so the welcome screen can hide right away) ----------
typed = st.chat_input("Ask a question about your courses...")
question = typed or st.session_state.pop("pending", None)

if question:
    st.session_state.messages.append({"role": "user", "content": question})

# ---------- Welcome screen ----------
if not st.session_state.messages:
    st.markdown(
        """
        <div class="welcome">
            <h3>👋 Welcome!</h3>
            Pick an example below or type your own question.
        </div>
        """,
        unsafe_allow_html=True,
    )
    examples = [
        "What is overfitting?",
        "Explain the ACID properties",
        "What is third normal form?",
        "How do I handle exceptions in Python?",
    ]
    cols = st.columns(2)
    for i, q in enumerate(examples):
        cols[i % 2].button(q, key=f"ex{i}", on_click=ask_example, args=(q,), use_container_width=True)

# ---------- Conversation ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍🎓" if msg["role"] == "user" else "🎓"):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and show_sources and msg.get("sources"):
            render_sources(msg["sources"])

# ---------- Answer the new question ----------
if question:
    with st.chat_message("assistant", avatar="🎓"):
        with st.spinner("Searching course materials..."):
            try:
                text, chunks = rag.answer(question, course, k)
            except Exception as e:
                text, chunks = "Something went wrong while contacting the LLM. Please try again in a moment.", []
                st.caption(str(e)[:300])

        st.markdown(text)
        if show_sources and chunks:
            render_sources(chunks)

    st.session_state.messages.append({"role": "assistant", "content": text, "sources": chunks})
    st.rerun()