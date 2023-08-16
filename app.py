from flask import Flask, request, jsonify, send_from_directory
import subprocess
import whisper
import pyaudio
import wave
import tempfile
import os
import pytesseract
from pdf2image import convert_from_path

app = Flask(__name__)
model = whisper.load_model("base")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    try:
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        RECORD_SECONDS = 600

        audio_dir = '/Users/ahsan/Downloads/project_directory/recordings'
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)

        audio_file = request.files['audio']
        audio_wav_path = os.path.join(audio_dir, 'temp_audio.wav')
        audio_file.save(audio_wav_path)

        audio_mp3_path = os.path.join(audio_dir, 'output_audio.mp3')

        ffmpeg_cmd = f"/opt/homebrew/bin/ffmpeg -y -i {audio_wav_path} -vn -c:a libmp3lame -b:a 192k {audio_mp3_path}"
        subprocess.run(ffmpeg_cmd, shell=True)
        print(f"Converted to MP3: {audio_mp3_path}")

        result = model.transcribe(audio_mp3_path)
    
        # Optionally delete temp WAV file
        os.remove(audio_wav_path)

        audio_mp3_url = f"/get_audio/{os.path.basename(audio_mp3_path)}"

        return jsonify({'transcription': result['text'], 'audio_url': audio_mp3_url})
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/get_audio/<filename>')
def get_audio(filename):
    audio_dir = '/Users/ahsan/Downloads/project_directory/recordings'
    return send_from_directory(audio_dir, filename)

@app.route('/pdf_to_text', methods=['POST'])
def pdf_to_text():
    try:
        pdf_file = request.files['file']
        pdf_path = 'output.pdf'
        pdf_file.save(pdf_path)

        images = convert_from_path(pdf_path, dpi=300)

        text = ''
        for image in images:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            num_words = len(data['text'])
            for i in range(num_words):
                word = data['text'][i]
                if word.strip():
                    text += ' ' + word
                    if i < num_words - 1 and data['block_num'][i] != data['block_num'][i + 1]:
                        text += '\n' # Add newline at the end of a block (sentence)

        return text.strip() #  Remove leading and trailing spaces
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
