import asyncio
import base64
import json
import os
import pyaudio
import shutil
import sys
import websockets

events_to_send = [
    # Send only this event and everything works as expected.
    {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Tell me a joke."}],
        },
    },
    # Continue sending these events and all subsequent assistant responses will be text (not audio).
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


class AudioStreamer:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.ws = None

    async def send_history(self):
        for item in events_to_send:
            await self.ws.send(json.dumps(item))
            # sleep to make it easy to see message sequences
            await asyncio.sleep(1)
        if events_to_send[-1]["item"]["role"] == "user":
            await self.ws.send(json.dumps({"type": "response.create"}))
        else:
            await self.send_text_input()

    async def send_text_input(self):
        msg = input("! Enter a message: ")
        await self.ws.send(
            json.dumps(
                {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": msg}],
                    },
                }
            )
        )
        await self.ws.send(json.dumps({"type": "response.create"}))

    async def ws_receive_worker(self):
        async for m in self.ws:
            # print as much of the raw event as will fit on the terminal
            columns, rows = shutil.get_terminal_size()
            maxl = columns - 5
            print(m if len(m) <= maxl else (m[:maxl] + " ..."))
            # handle a few events specially
            evt = json.loads(m)
            if evt["type"] == "session.created":
                print(json.dumps(evt, indent=2))
                asyncio.create_task(self.send_history())
            elif evt["type"] == "response.done":
                await self.send_text_input()
            elif evt["type"] == "conversation.created":
                # docs say we should get this event, but it doesn't seem to be sent
                pass
            elif evt["type"] == "response.audio.delta":
                # audio to play
                audio = base64.b64decode(evt["delta"])
                self.speaker_audio_out.write(audio)
            elif evt["type"] == "response.text":
                # this event does not seem to be sent
                print(f"> {evt['text']}")
            elif evt["type"] == "response.output_item.done":
                print(json.dumps(evt, indent=2))
            elif evt["type"] == "error":
                print(json.dumps(evt, indent=2))

    async def run(self):
        self.speaker_audio_out = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=24000,
            output=True,
        )

        self.ws = await websockets.connect(
            uri="wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01",
            extra_headers={
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "OpenAI-Beta": "realtime=v1",
            },
        )

        asyncio.create_task(self.ws_receive_worker())

        await asyncio.sleep(15 * 60)


def load_json_data(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{file_path}'.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(AudioStreamer().run())
