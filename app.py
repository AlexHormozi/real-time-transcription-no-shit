from flask import Flask, request, jsonify
from deepgram import Deepgram
import asyncio
import aiohttp
import time
import threading

# Your Deepgram API key
DEEPGRAM_API_KEY = 'd60c00514729244e27d97f343003520cdb9404ef'

# URL for the real-time streaming audio you would like to transcribe
URL = 'http://stream.live.vc.bbcmedia.co.uk/bbc_world_service'

# Fill in these parameters to adjust the output as you wish!
PARAMS = {
    "punctuate": True,
    "numerals": True,
    "model": "general",
    "language": "en-US",
    "tier": "nova"
}

# Set the app
app = Flask(__name__)

# Function to handle live transcription in a separate thread
def start_transcription():
    async def main():
        start = time.time()
        # Initializes the Deepgram SDK
        deepgram = Deepgram(DEEPGRAM_API_KEY)
        # Create a websocket connection to Deepgram
        try:
            deepgramLive = await deepgram.transcription.live(PARAMS)
        except Exception as e:
            print(f'Could not open socket: {e}')
            return

        # Listen for the connection to close
        deepgramLive.registerHandler(deepgramLive.event.CLOSE,
                                     lambda _: print('✅ Transcription complete! Connection closed. ✅'))

        # Listen for any transcripts received from Deepgram & write them to the console
        def print_transcript(json_data):
            try:
                print(json_data['channel']['alternatives'][0]['transcript'])
            except KeyError:
                print()

        deepgramLive.registerHandler(deepgramLive.event.TRANSCRIPT_RECEIVED, print_transcript)

        # Listen for the connection to open and send streaming audio from the URL to Deepgram
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as audio:
                while time.time() - start < 30:  # Change 30 to your desired time limit
                    data = await audio.content.readany()
                    if data:
                        deepgramLive.send(data)
                    else:
                        break

        # Finish the transcription process
        await deepgramLive.finish()

    # Run the async function in a separate thread
    asyncio.run(main())

@app.route('/start_transcription', methods=['GET'])
def start_transcription_api():
    threading.Thread(target=start_transcription).start()
    return jsonify({"message": "Transcription started!"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)  # Port 5000 or change as needed
