from flask import Flask, request, jsonify
from deepgram import Deepgram
import asyncio

# Deepgram API key
DEEPGRAM_API_KEY = "d60c00514729244e27d97f343003520cdb9404ef"

# Initialize Flask app
app = Flask(__name__)

# Initialize Deepgram SDK (Version 2)
dg_client = Deepgram(DEEPGRAM_API_KEY)

@app.route('/transcribe', methods=['POST'])
async def transcribe_audio():
    audio_url = request.json.get('audio_url')
    
    if not audio_url:
        return jsonify({"error": "No audio_url provided"}), 400

    try:
        # Send request to Deepgram API for transcription
        response = await dg_client.transcription.pre_recorded(audio_url, {
            "punctuate": True,
            "diarize": True
        })

        # Parse response and return transcription result
        transcription = response['results']['channels'][0]['alternatives'][0]['transcript']
        return jsonify({"transcription": transcription})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
