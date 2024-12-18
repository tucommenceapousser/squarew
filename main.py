import os
import zipfile
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from pydub import AudioSegment
import numpy as np
from scipy.io.wavfile import write

app = Flask(__name__)
app.secret_key = "tesla_secret_key"  # Pour gérer les messages flash

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_files():
    # Vérifier si des fichiers sont uploadés
    if "files" not in request.files:
        flash("Aucun fichier sélectionné !", "error")
        return redirect(url_for("home"))

    files = request.files.getlist("files")
    if not files or files[0].filename == "":
        flash("Aucun fichier valide sélectionné !", "error")
        return redirect(url_for("home"))

    output_files = []
    for file in files:
        try:
            # Sauvegarder le fichier uploadé
            input_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(input_path)

            # Convertir en square wave
            output_filename = os.path.splitext(file.filename)[0] + "_square_wave.wav"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            convert_to_square_wave(input_path, output_path)
            output_files.append(output_path)
        except Exception as e:
            flash(f"Erreur lors du traitement du fichier {file.filename} : {e}", "error")

    if not output_files:
        flash("Aucun fichier n'a pu être traité.", "error")
        return redirect(url_for("home"))

    # Créer une archive ZIP
    zip_path = os.path.join(OUTPUT_FOLDER, "square_wave_files.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for output_file in output_files:
            zipf.write(output_file, os.path.basename(output_file))

    flash("Fichiers convertis avec succès ! Vous pouvez les télécharger ci-dessous.", "success")
    return send_file(zip_path, as_attachment=True)

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
    app.run(debug=, host="0.0.0.0", port=8080)
