from flask import Flask, request, jsonify
import asyncio
from deepgram import Deepgram
import aiohttp
import time

app = Flask(__name__)

# Your personal Deepgram API key
DEEPGRAM_API_KEY = 'd60c00514729244e27d97f343003520cdb9404ef'

# Global variable for the URL
stream_url = 'http://stream.live.vc.bbcmedia.co.uk/bbc_world_service'

# Deepgram parameters
PARAMS = {
    "punctuate": True,
    "numerals": True,
    "model": "general",
    "language": "en-US",
    "tier": "nova"
}

TIME_LIMIT = 30
TRANSCRIPT_ONLY = True
transcription_text = ""

def print_transcript(json_data):
    global transcription_text
    try:
        transcription_text = json_data['channel']['alternatives'][0]['transcript']
    except KeyError:
        transcription_text = "No transcript available."

@app.route('/start_transcription', methods=['GET'])
def start_transcription():
    # Start the transcription process when the API is called
    asyncio.run(main())
    return jsonify({"message": "Transcription started."}), 200

@app.route('/update_stream_url', methods=['POST'])
def update_stream_url():
    global stream_url
    new_url = request.json.get("url")
    if not new_url:
        return jsonify({"error": "URL is required"}), 400
    stream_url = new_url
    return jsonify({"message": f"Stream URL updated to: {new_url}"}), 200

@app.route('/get_transcription', methods=['GET'])
def get_transcription():
    global transcription_text
    return jsonify({"transcription": transcription_text}), 200

async def main():
    start = time.time()
    deepgram = Deepgram(DEEPGRAM_API_KEY)

    try:
        deepgramLive = await deepgram.transcription.live(PARAMS)
    except Exception as e:
        print(f'Could not open socket: {e}')
        return

    deepgramLive.registerHandler(deepgramLive.event.CLOSE, lambda _: print('✅ Transcription complete! Connection closed. ✅'))

    if TRANSCRIPT_ONLY:
        deepgramLive.registerHandler(deepgramLive.event.TRANSCRIPT_RECEIVED, print_transcript)
    else:
        deepgramLive.registerHandler(deepgramLive.event.TRANSCRIPT_RECEIVED, print)

    async with aiohttp.ClientSession() as session:
        async with session.get(stream_url) as audio:
            while time.time() - start < TIME_LIMIT:
                data = await audio.content.readany()
                if data:
                    deepgramLive.send(data)
                else:
                    break

    await deepgramLive.finish()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
