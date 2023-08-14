from flask import Flask, request, jsonify, send_from_directory
import subprocess
import whisper
from pdf2image import convert_from_path
import pytesseract
import os

app = Flask(__name__)
model = whisper.load_model("base")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    try:
        audio_file = request.files['audio']
        audio_path = 'Dr_Muhmad_ali.m4a'
        audio_file.save(audio_path)
        
        audio_out = 'audio_output.mp3'
        ffmpeg_cmd = f"/opt/homebrew/bin/ffmpeg -y -i {audio_path} -vn -c:a libmp3lame -b:a 192k {audio_out}"
        subprocess.run(ffmpeg_cmd, shell=True)
                
        result = model.transcribe(audio_out)
        
        return jsonify({'transcription': result['text']})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

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
