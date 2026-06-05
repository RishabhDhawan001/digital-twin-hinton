"""
Geoffrey Hinton Digital Twin — Interactive CLI Demo
Run: python demo/cli_demo.py

Text-to-speech: Hinton's replies are read aloud via pyttsx3 (Windows SAPI5).
Use /tts on|off to toggle speech at any time.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.rule import Rule
from rich.markdown import Markdown
from rich import print as rprint

from agent import FeynmanAgent
from tts import HintonTTS

console = Console()

FEYNMAN_COLOR = "yellow"
USER_COLOR = "cyan"
SYSTEM_COLOR = "dim"


def print_banner():
    banner = r"""
  _   _ ___ _   _ _____ ___  _   _
 | | | |_ _| \ | |_   _/ _ \| \ | |
 | |_| || ||  \| | | || | | |  \| |
 |  _  || || |\  | | || |_| | |\  |
 |_| |_|___|_| \_| |_| \___/|_| \_|

    Digital Twin of Geoffrey Hinton (b. 1947)
    "Godfather of AI" - Turing Award 2018 - Nobel Prize in Physics 2024
    """
    console.print(banner, style="bold yellow")


def run_cli():
    print_banner()

    console.print(Panel(
        "[dim]Commands:[/dim]\n"
        "  [cyan]quit[/cyan] or [cyan]exit[/cyan] — end session\n"
        "  [cyan]/memory[/cyan] — show what Hinton remembers about you\n"
        "  [cyan]/stats[/cyan]  — show RAG database stats\n"
        "  [cyan]/user <id>[/cyan] — set user ID (for persistent memory)\n"
        "  [cyan]/tts on|off[/cyan] — toggle spoken voice on or off",
        title="[bold]Geoffrey Hinton Digital Twin[/bold]",
        border_style="yellow"
    ))

    # Get user ID for persistent memory
    user_id = Prompt.ask(
        "\n[dim]Enter your user ID for persistent memory (press Enter for anonymous)[/dim]",
        default="anonymous"
    )

    console.print(Rule(style="yellow dim"))

    # Initialise TTS (always on by default)
    tts = HintonTTS(rate=155, volume=1.0)
    tts_enabled = tts._available   # gracefully off if pyttsx3 failed to init

    if tts._available:
        console.print("[dim]🔊 Text-to-speech active. Type [cyan]/tts off[/cyan] to silence.[/dim]")
    else:
        console.print("[dim]⚠ pyttsx3 unavailable — running text-only.[/dim]")

    try:
        with console.status("[yellow]Initializing Hinton twin (loading RAG, memory)...[/yellow]"):
            agent = FeynmanAgent(user_id=user_id)
    except ValueError as e:
        console.print(f"\n[red]Error:[/red] {e}\n")
        console.print("[dim]Create a .env file with:[/dim]")
        console.print("[bold]GEMINI_API_KEY=your_key_here[/bold]\n")
        sys.exit(1)

    # Print and speak the greeting
    console.print(Rule(style="yellow"))
    greeting = agent.get_greeting()
    console.print(Panel(
        Markdown(greeting),
        title="[bold yellow]Geoffrey Hinton[/bold yellow]",
        border_style="yellow",
        padding=(1, 2)
    ))
    if tts_enabled:
        tts.speak(greeting)

    # Main conversation loop
    while True:
        console.print()
        try:
            user_input = Prompt.ask(f"[{USER_COLOR}]You[/{USER_COLOR}]")
        except (KeyboardInterrupt, EOFError):
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        # ── Built-in commands ────────────────────────────────────────────
        if user_input.lower() in ("quit", "exit", "q"):
            break

        if user_input.lower().startswith("/tts"):
            parts = user_input.split()
            if len(parts) == 2 and parts[1].lower() == "off":
                tts_enabled = False
                tts.stop()
                console.print("[dim]🔇 Text-to-speech off.[/dim]")
            elif len(parts) == 2 and parts[1].lower() == "on":
                if tts._available:
                    tts_enabled = True
                    console.print("[dim]🔊 Text-to-speech on.[/dim]")
                else:
                    console.print("[dim]⚠ pyttsx3 is not available.[/dim]")
            else:
                console.print("[dim]Usage: /tts on  or  /tts off[/dim]")
            continue

        if user_input.lower() == "/memory":
            data = agent.get_memory_data()
            memories = data.get("memories", [])
            sessions = data.get("sessions", [])

            if not memories and not sessions:
                console.print("[dim]No memories stored yet for this user.[/dim]")
            else:
                console.print(Panel(
                    f"[bold]Memories ({len(memories)} facts)[/bold]\n" +
                    "\n".join([f"  [{m['type']}] {m['content']}" for m in memories[:10]]) +
                    f"\n\n[bold]Past sessions ({len(sessions)})[/bold]\n" +
                    "\n".join([f"  {s['start'][:10]}: {s['summary']}" for s in sessions[:5]]),
                    title="Memory Dashboard",
                    border_style="cyan"
                ))
            continue

        if user_input.lower() == "/stats":
            stats = agent.get_rag_stats()
            console.print(f"[dim]RAG Database: {stats['total_chunks']} chunks indexed from Hinton's works[/dim]")
            continue

        # ── Get Hinton's response ────────────────────────────────────────
        with console.status("[yellow]Hinton is thinking...[/yellow]"):
            try:
                response = agent.chat(user_input)
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
                continue

        console.print()
        console.print(Panel(
            Markdown(response),
            title="[bold yellow]Geoffrey Hinton[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        ))

        # Speak the reply (non-blocking — user can type next question while it reads)
        if tts_enabled:
            tts.speak(response)

    # ── End session ──────────────────────────────────────────────────────
    tts.stop()
    console.print(Rule(style="yellow dim"))
    farewell = "It's been a real pleasure. Keep questioning the assumptions everyone else takes for granted."
    console.print(f"[yellow]Hinton:[/yellow] {farewell}")
    if tts_enabled:
        tts.speak(farewell, block=True)   # speak farewell synchronously before exit

    with console.status("[dim]Saving session to long-term memory...[/dim]"):
        agent.end_session()

    console.print("[dim]Session saved. See you next time![/dim]\n")


if __name__ == "__main__":
    run_cli()
