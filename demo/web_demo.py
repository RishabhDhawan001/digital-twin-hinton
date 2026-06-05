"""
Geoffrey Hinton Digital Twin — Gradio Web UI
Includes: chat interface, memory dashboard, voice output (pyttsx3), timeline awareness
Run: python demo/web_demo.py
"""

import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

from agent import FeynmanAgent
from tts import HintonTTS


# Global agent and TTS (initialized on first use)
_agent = None
_user_id = "web_user"
_tts = HintonTTS(rate=155, volume=1.0)
_tts_enabled = _tts._available   # gracefully disabled if pyttsx3 not installed


def get_agent() -> FeynmanAgent:
    global _agent
    if _agent is None:
        _agent = FeynmanAgent(user_id=_user_id)
    return _agent


def chat_fn(message: str, history: list, user_id_input: str, tts_on: bool):
    global _agent, _user_id, _tts_enabled

    if not message.strip():
        return history, ""

    # Re-init agent if user_id changed
    if user_id_input and user_id_input != _user_id:
        _user_id = user_id_input
        _agent = FeynmanAgent(user_id=_user_id)

    agent = get_agent()

    try:
        response = agent.chat(message)
    except Exception as e:
        response = f"[Error connecting to Gemini: {e}]"

    history.append((message, response))

    # Speak the response (non-blocking — user can keep typing while it reads)
    if tts_on and _tts._available:
        _tts.speak(response)

    return history, ""


def toggle_tts(tts_on: bool):
    """Stop any ongoing speech when user turns TTS off."""
    if not tts_on:
        _tts.stop()
    status = "🔊 Voice ON" if tts_on else "🔇 Voice OFF"
    return status


def get_memory_dashboard():
    """Build memory visualization using Plotly."""
    try:
        agent = get_agent()
        data = agent.get_memory_data()
        memories = data.get("memories", [])
        sessions = data.get("sessions", [])
    except Exception:
        return go.Figure(), "<p>Initialize a conversation first.</p>"

    if not memories:
        fig = go.Figure()
        fig.update_layout(title="No memories yet — start a conversation!", template="plotly_dark")
        return fig, "<p>No memories stored yet.</p>"

    # Memory type breakdown
    type_counts = {}
    for m in memories:
        t = m["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    colors = {
        "fact": "#FFD700",
        "interest": "#87CEEB",
        "prior_knowledge": "#98FB98",
        "question": "#DDA0DD",
        "breakthrough": "#FFA07A"
    }

    fig = go.Figure(data=[go.Pie(
        labels=list(type_counts.keys()),
        values=list(type_counts.values()),
        marker_colors=[colors.get(k, "#cccccc") for k in type_counts.keys()],
        hole=0.4,
        textinfo="label+percent"
    )])
    fig.update_layout(
        title="Memory Type Distribution",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white")
    )

    # Memory table HTML
    rows = ""
    for m in memories[:20]:
        rows += f"<tr><td><b>{m['type']}</b></td><td>{m['content']}</td><td>{m['date'][:10]}</td></tr>"

    table_html = f"""
    <div style="max-height:300px; overflow-y:auto; background:#1a1a1a; border-radius:8px; padding:12px;">
        <table style="width:100%; color:white; border-collapse:collapse; font-size:13px;">
            <thead>
                <tr style="border-bottom:1px solid #444;">
                    <th style="text-align:left;padding:6px;">Type</th>
                    <th style="text-align:left;padding:6px;">Memory</th>
                    <th style="text-align:left;padding:6px;">Date</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    <p style="color:#aaa;font-size:12px;margin-top:8px;">Sessions: {len(sessions)} total</p>
    """

    return fig, table_html


def clear_chat():
    global _agent
    if _agent:
        _agent.end_session()
        _agent = None
    _tts.stop()
    return [], ""


def build_ui():
    tts_default = _tts._available   # checkbox starts checked only if pyttsx3 loaded OK

    css = """
    .feynman-header { text-align: center; color: #FFD700; }
    .chat-container { border-radius: 12px; }
    """

    with gr.Blocks(title="Geoffrey Hinton Digital Twin", theme=gr.themes.Soft(), css=css) as demo:

        gr.HTML("""
        <div style="text-align:center; padding:20px 0 10px;">
            <h1 style="color:#FFD700; font-size:2em; margin:0;">🧠 Geoffrey Hinton</h1>
            <p style="color:#aaa; margin:4px 0 0;">Digital Twin · "Godfather of AI" · Turing Award 2018 · Nobel Prize in Physics 2024</p>
        </div>
        """)

        with gr.Tabs():

            # --- Chat Tab ---
            with gr.Tab("💬 Chat with Hinton"):
                with gr.Row():
                    with gr.Column(scale=4):
                        chatbot = gr.Chatbot(
                            value=[(None, _get_greeting())],
                            height=520,
                            label="Conversation",
                            bubble_full_width=False,
                            avatar_images=None
                        )
                        with gr.Row():
                            msg_input = gr.Textbox(
                                placeholder="Ask Hinton anything — deep learning, the brain, AI safety...",
                                show_label=False,
                                scale=5
                            )
                            send_btn = gr.Button("Send", variant="primary", scale=1)

                    with gr.Column(scale=1):
                        gr.HTML("<h3 style='color:#FFD700'>⚙️ Settings</h3>")
                        user_id_input = gr.Textbox(
                            value="web_user",
                            label="Your User ID",
                            info="Used for persistent memory across sessions"
                        )

                        # ── TTS controls ──────────────────────────────
                        gr.HTML("<hr style='border-color:#333; margin:12px 0;'>")
                        tts_checkbox = gr.Checkbox(
                            value=tts_default,
                            label="🔊 Speak replies aloud",
                            info="Uses Windows built-in voice (pyttsx3 / SAPI5). "
                                 "No extra installs needed." if _tts._available
                                 else "pyttsx3 not installed — run: pip install pyttsx3"
                        )
                        tts_status = gr.Textbox(
                            value="🔊 Voice ON" if tts_default else "⚠ pyttsx3 unavailable",
                            label="Voice status",
                            interactive=False,
                            max_lines=1
                        )
                        tts_checkbox.change(
                            toggle_tts,
                            inputs=[tts_checkbox],
                            outputs=[tts_status]
                        )
                        # ─────────────────────────────────────────────

                        clear_btn = gr.Button("🗑️ New Session", variant="secondary")

                        gr.HTML("""
                        <div style='margin-top:16px; padding:12px; background:#1a1a1a; border-radius:8px;'>
                            <h4 style='color:#FFD700; margin:0 0 8px;'>💡 Sample Questions</h4>
                            <p style='color:#ccc; font-size:13px; margin:4px 0;'>• How does backpropagation work?</p>
                            <p style='color:#ccc; font-size:13px; margin:4px 0;'>• Do language models really understand?</p>
                            <p style='color:#ccc; font-size:13px; margin:4px 0;'>• Why did you leave Google?</p>
                            <p style='color:#ccc; font-size:13px; margin:4px 0;'>• What worries you most about AI?</p>
                            <p style='color:#ccc; font-size:13px; margin:4px 0;'>• Does the brain use backpropagation?</p>
                        </div>
                        """)

                # Event handlers
                send_btn.click(
                    chat_fn,
                    inputs=[msg_input, chatbot, user_id_input, tts_checkbox],
                    outputs=[chatbot, msg_input]
                )
                msg_input.submit(
                    chat_fn,
                    inputs=[msg_input, chatbot, user_id_input, tts_checkbox],
                    outputs=[chatbot, msg_input]
                )
                clear_btn.click(clear_chat, outputs=[chatbot, msg_input])

            # --- Memory Dashboard Tab ---
            with gr.Tab("🧠 Memory Dashboard"):
                gr.HTML("<h3 style='color:#FFD700'>What Hinton Remembers About You</h3>")

                refresh_btn = gr.Button("🔄 Refresh Memory Dashboard", variant="secondary")

                with gr.Row():
                    memory_chart = gr.Plot(label="Memory Breakdown")

                memory_table = gr.HTML("<p style='color:#aaa'>Click refresh to load memories.</p>")

                refresh_btn.click(
                    get_memory_dashboard,
                    outputs=[memory_chart, memory_table]
                )

            # --- About Tab ---
            with gr.Tab("ℹ️ About"):
                gr.Markdown("""
                ## Geoffrey Hinton Digital Twin

                This is an AI agent that emulates **Geoffrey Hinton** (b. 1947), the "Godfather of AI" —
                Turing Award (2018) and Nobel Prize in Physics (2024) laureate for foundational work on
                neural networks.

                ### How It Works

                **Three core pillars:**

                1. **RAG Pipeline** — Answers are grounded in Hinton's actual work:
                   - Backpropagation (Rumelhart, Hinton & Williams, 1986)
                   - ImageNet / AlexNet (Krizhevsky, Sutskever & Hinton, 2012)
                   - Dropout and knowledge distillation papers
                   - Boltzmann machines and capsule networks
                   - Post-Google interviews on AI risk and AI safety

                2. **Memory System**
                   - **Short-term**: Full conversation buffer within a session
                   - **Long-term**: SQLite database — stores facts about you across sessions
                   - **Memory extraction**: Gemini automatically extracts memorable facts

                3. **Persona Layer** — Carefully crafted system prompt capturing:
                   - Hinton's thoughtful, measured voice and dry British wit
                   - His teaching style (intuition first, vivid analogies, honesty about the unknown)
                   - His real biography (left Google 2023, Nobel Prize 2024)
                   - His genuine concern about AI safety and existential risk

                ### Tech Stack
                - **LLM**: Google Gemini 2.5 Flash
                - **Vector DB**: ChromaDB with sentence-transformers embeddings
                - **Memory**: SQLite (long-term) + in-memory buffer (short-term)
                - **UI**: Gradio
                - **TTS**: pyttsx3 (Windows SAPI5 — no extra installs needed)

                *AIMS DTU Summer Project 2026*
                """)

    return demo


def _get_greeting():
    try:
        agent = get_agent()
        return agent.get_greeting()
    except Exception:
        return "Initialize with your GEMINI_API_KEY to start!"


if __name__ == "__main__":
    print("Starting Hinton Digital Twin Web UI...")
    if _tts._available:
        print("[TTS] pyttsx3 loaded — spoken voice is ON by default.")
    else:
        print("[TTS] pyttsx3 unavailable — running text-only. Run: pip install pyttsx3")
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
