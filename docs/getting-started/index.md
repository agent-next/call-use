# Getting Started

This guide walks you through installing call-use, configuring your environment, and making your first outbound phone call with an AI agent.

## Prerequisites

Before you begin, you need accounts with:

- **[LiveKit Cloud](https://livekit.io)** (or a self-hosted LiveKit server) -- real-time communication infrastructure
- **[Twilio](https://twilio.com)** -- SIP trunk for PSTN connectivity
- **[Deepgram](https://deepgram.com)** -- speech-to-text
- **[OpenAI](https://platform.openai.com)** -- LLM (GPT-4o) and text-to-speech (GPT-4o-mini TTS)

You also need:

- Python 3.11 or later
- A US or Canada phone number to call (NANP E.164 format)

## Overview

The getting-started guide is split into three pages:

1. **[Installation](installation.md)** -- Install the package and system dependencies
2. **[Configuration](configuration.md)** -- Set up environment variables for LiveKit, Twilio, Deepgram, and OpenAI
3. **[First Call](first-call.md)** -- Make your first outbound call step by step

## How it works (30-second version)

call-use runs two processes:

1. **Your code** (SDK, CLI, REST API, or MCP) creates a LiveKit room and dispatches an agent
2. **The call-use worker** joins the room, dials via SIP, runs the conversation, and publishes a structured outcome

The worker handles IVR navigation, hold/transfer detection, voicemail detection, and conversation -- your code just sets the goal and reads the result.

## Next steps

[:octicons-arrow-right-24: Install call-use](installation.md)
