#!/usr/bin/env python3
"""
Enkelt skript för att testa prompter mot OpenRouter API.

Usage:
    python test_prompt.py <system_prompt_file> <user_prompt_file> <output_file>

Environment:
    OPENROUTER_API_KEY: Din OpenRouter API-nyckel
"""

import os
import sys
import json
import requests


def read_file(filepath):
    """Läs innehållet från en fil."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Kunde inte hitta filen: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Kunde inte läsa {filepath}: {e}")
        sys.exit(1)


# def call_openrouter(system_prompt, user_prompt, model="anthropic/claude-haiku-4.5"):
def call_openrouter(system_prompt, user_prompt, model="x-ai/grok-4-fast"):
# def call_openrouter(system_prompt, user_prompt, model="x-ai/grok-4.1-fast:free"):
    """Anropa OpenRouter API med system och user prompts."""
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY miljövariabel saknas")
        sys.exit(1)

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    print(f"Skickar request till OpenRouter ({model})...")
    print(f"System prompt: {len(system_prompt)} tecken")
    print(f"User prompt: {len(user_prompt)} tecken")
    print()

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: API-anrop misslyckades: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response body: {e.response.text}")
        sys.exit(1)


def save_and_display(content, output_file):
    """Spara innehåll till fil och visa i terminalen."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Svaret sparat till: {output_file}")
        print()
        print("=" * 80)
        print("SVAR FRÅN LLM:")
        print("=" * 80)
        print()
        print(content)
        print()
        print("=" * 80)
    except Exception as e:
        print(f"Error: Kunde inte spara till {output_file}: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) != 4:
        print("Usage: python test_prompt.py <system_prompt_file> <user_prompt_file> <output_file>")
        sys.exit(1)

    system_prompt_file = sys.argv[1]
    user_prompt_file = sys.argv[2]
    output_file = sys.argv[3]

    # Läs prompter
    system_prompt = read_file(system_prompt_file)
    user_prompt = read_file(user_prompt_file)

    # Anropa API
    response_data = call_openrouter(system_prompt, user_prompt)

    # Extrahera svaret
    try:
        assistant_message = response_data['choices'][0]['message']['content']
    except (KeyError, IndexError) as e:
        print(f"Error: Oväntat response-format: {e}")
        print(f"Response: {json.dumps(response_data, indent=2)}")
        sys.exit(1)

    # Spara och visa
    save_and_display(assistant_message, output_file)


if __name__ == "__main__":
    main()
