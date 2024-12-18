import os
from flask import Flask, render_template, request, send_file
from pydub import AudioSegment
import numpy as np
from scipy.io.wavfile import write

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    if file.filename == "":
        return "No file selected", 400

    # Sauvegarde du fichier uploadé
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)

    # Transformation en square wave
    output_filename = os.path.splitext(file.filename)[0] + "_square_wave.wav"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    convert_to_square_wave(input_path, output_path)

    return send_file(output_path, as_attachment=True)

def convert_to_square_wave(input_file, output_file):
    # Convertir MP3 en WAV
    audio = AudioSegment.from_mp3(input_file)
    audio = audio.set_channels(1)  # Mono pour simplifier
    audio = audio.set_frame_rate(44100)
    samples = np.array(audio.get_array_of_samples())

    # Normaliser les échantillons entre -1 et 1
    samples = samples / np.max(np.abs(samples), axis=0)

    # Transformer en square wave
    square_wave = np.sign(samples)

    # Convertir en entier 16 bits pour WAV
    square_wave = np.int16(square_wave * 32767)

    # Sauvegarder en WAV
    write(output_file, 44100, square_wave)

if __name__ == "__main__":
    app.run(debug=True)
