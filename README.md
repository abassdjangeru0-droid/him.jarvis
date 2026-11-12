# HIM

A personal Jarvis-style AI assistant powered by Claude.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key-here"   # Windows: setx ANTHROPIC_API_KEY "your-key-here"
```

Get a key at https://console.anthropic.com

## Run

```bash
python him.py           # type to HIM, he replies in text
python him.py --speak   # type to HIM, he talks back
python him.py --voice   # say "HIM, what time is it?" and he talks back
```

## Changing his voice

HIM uses Microsoft's free neural voices (needs internet). Default is `en-GB-RyanNeural`.
Pick another with an environment variable, e.g. `HIM_VOICE=en-US-GuyNeural`.
List all voices with `edge-tts --list-voices`.
If the neural voice fails, he falls back to an offline robotic voice.

## Add your own abilities

Write a function in `him.py`, then register it in `TOOL_FUNCTIONS` and `TOOLS`.

## Never commit your API key
Keep it in an environment variable. `.gitignore` already excludes `.env`.
