"""
HIM - a personal Jarvis-style assistant.

Modes:
  python him.py           -> type to HIM, he replies in text
  python him.py --speak   -> type to HIM, he talks back out loud
  python him.py --voice   -> say "HIM" to wake him, speak your request, he talks back
"""

import os
import sys
import json
import datetime
import webbrowser

import anthropic

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
VOICE = os.getenv("HIM_VOICE", "en-GB-RyanNeural")  # deep British male, very Jarvis

MODEL = os.getenv("HIM_MODEL", "claude-sonnet-5-5")
NAME = "HIM"

SYSTEM_PROMPT = (
    f"You are {NAME}, a personal AI assistant in the style of Jarvis. "
    "You are loyal, witty, concise and efficient. Keep replies short "
    "(1-3 sentences) unless asked for detail, since they may be spoken aloud. "
    "Use your tools when they help. Never use markdown, lists or emojis; "
    "write plain sentences that sound natural when spoken."
)

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment


# ---------------------------------------------------------------- tools ----
def get_time() -> str:
    return datetime.datetime.now().strftime("%A, %B %d %Y, %I:%M %p")


def open_website(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"


def search_google(query: str) -> str:
    webbrowser.open("https://www.google.com/search?q=" + query.replace(" ", "+"))
    return f"Searching Google for {query}"


TOOL_FUNCTIONS = {
    "get_time": lambda **_: get_time(),
    "open_website": lambda url, **_: open_website(url),
    "search_google": lambda query, **_: search_google(query),
}

TOOLS = [
    {
        "name": "get_time",
        "description": "Get the current local date and time.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "open_website",
        "description": "Open a website in the user's browser.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "search_google",
        "description": "Search Google in the user's browser.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]
# Add your own tools: write a function, add it to TOOL_FUNCTIONS and TOOLS.


# ---------------------------------------------------------------- brain ----
history = []


def think(user_text: str) -> str:
    """Send a message to Claude, run any tools it asks for, return the reply."""
    history.append({"role": "user", "content": user_text})

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=history,
        )
        history.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        results = []
        for block in response.content:
            if block.type == "tool_use":
                try:
                    out = TOOL_FUNCTIONS[block.name](**block.input)
                except Exception as e:
                    out = f"Error: {e}"
                results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": str(out)}
                )
        history.append({"role": "user", "content": results})


# ---------------------------------------------------------------- speech ----
def _speak_neural(text: str):
    """Natural-sounding voice using Microsoft Edge's free neural voices."""
    import asyncio
    import tempfile
    import edge_tts
    import pygame

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    asyncio.run(edge_tts.Communicate(text, VOICE).save(tmp.name))

    pygame.mixer.init()
    pygame.mixer.music.load(tmp.name)
    pygame.mixer.music.play()
    clock = pygame.time.Clock()
    while pygame.mixer.music.get_busy():
        clock.tick(10)
    pygame.mixer.music.unload()
    os.remove(tmp.name)


def _speak_basic(text: str):
    """Offline fallback (robotic, but works with no internet)."""
    import pyttsx3

    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def speak(text: str):
    print(f"{NAME}: {text}")
    try:
        _speak_neural(text)
    except Exception:
        try:
            _speak_basic(text)
        except Exception as e:
            print(f"(couldn't speak: {e})")


# ---------------------------------------------------------------- voice ----
def run_voice():
    import speech_recognition as sr

    rec = sr.Recognizer()

    def listen():
        with sr.Microphone() as mic:
            rec.adjust_for_ambient_noise(mic, duration=0.5)
            audio = rec.listen(mic, phrase_time_limit=8)
        try:
            return rec.recognize_google(audio).lower()
        except (sr.UnknownValueError, sr.RequestError):
            return ""

    speak("Online and ready.")
    while True:
        heard = listen()
        if NAME.lower() in heard:
            request = heard.split(NAME.lower(), 1)[1].strip()
            if not request:
                speak("Yes?")
                request = listen()
            if request in ("quit", "exit", "shut down", "goodbye"):
                speak("Shutting down. Goodbye.")
                break
            if request:
                speak(think(request))


# ----------------------------------------------------------------- text ----
def run_text(talk: bool = False):
    print(f"{NAME} online. Type 'quit' to exit.\n")
    while True:
        text = input("You: ").strip()
        if text.lower() in ("quit", "exit"):
            break
        if text:
            reply = think(text)
            if talk:
                speak(reply)
            else:
                print(f"{NAME}: {reply}")
            print()


if __name__ == "__main__":
    if "--voice" in sys.argv:
        run_voice()
    else:
        run_text(talk="--speak" in sys.argv)
