
## Test cases for adding conversation history via the realtime API


### Install

```
python3.12 -m venv venv                                                       
source venv/bin/activate
pip install asyncio pyaudio websockets
export OPENAI_API_KEY=...
```

### Sanity check that things are working

* Note: use headphones. There's no echo cancellation. *

Also no error handling, etc. This is a tiny command-line voice-to-voice client.

```
python minimal-voice-to-voice.py
```

### Test case 1

Loading a conversation starting with an `input_text` item.

```
python test-case-1.py 
```

If we create a single "user" item, then interact with the model, everything works as expected.

But if add an "assistant" item, the model will no longer produce any audio items for the remainder of the session.

This works as expected.

```
[
    {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Tell me a joke."}],
        },
    },
]
```

This produces only text content output.

```
[
    {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Tell me a joke."}],
        },
    },
    {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Why don't skeletons fight each other? They don't have the guts!",
                }
            ],
        },
    },
    {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Another one, please."}],
        },
    },
]
```

### Test case 2

Loading a conversation starting with an "audio" message, as shown in the Realtime API Integration Guide.

```
python test-case-2.py 
```

Starting with an audio message and continuing with one full text turn works as expected. But continuing with subsequent text turns again puts the model in a text-only mode.

This works as expected.

```
[
    {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_audio", "audio": audio_clip}],
        },
    },
    {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Why don't skeletons fight each other? They don't have the guts!",
                }
            ],
        },
    },
    {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Tell me another joke."}],
        },
    },
]
```

This message sequence results in no audio being produced for the session.

```
[
    {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_audio", "audio": audio_clip}],
        },
    },
    {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Why don't skeletons fight each other? They don't have the guts!",
                }
            ],
        },
    },
    {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Tell me another joke."}],
        },
    },
    # Send only the events above and everything works as expected. But continue with the events below
    # and all subsequent responses will be type "text" (not "audio").
    {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Why did the scarecrow win an award? Because he was outstanding in his field!",
                }
            ],
        },
    },
    {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "That was hilarious. One more, please."}],
        },
    },
]
```