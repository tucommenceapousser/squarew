import os
import zipfile
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from pydub import AudioSegment
import numpy as np
from scipy.io.wavfile import write
from scipy.signal import butter, lfilter

app = Flask(__name__)
app.secret_key = "tesla_secret_key"  # Pour gérer les messages flash

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

# Créez les dossiers pour stocker les fichiers uploadés et les fichiers de sortie
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def home():
    """Route principale pour afficher le formulaire."""
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_files():
    """Gestion de l'upload et conversion des fichiers MP3 en square wave."""
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
            # Sauvegarde le fichier uploadé
            input_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(input_path)

            # Convertit le fichier MP3 en square wave
            output_filename = os.path.splitext(file.filename)[0] + "_square_wave.wav"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            convert_to_square_wave(input_path, output_path)
            output_files.append(output_path)
        except Exception as e:
            flash(f"Erreur lors du traitement du fichier {file.filename} : {e}", "error")

    if not output_files:
        flash("Aucun fichier n'a pu être traité.", "error")
        return redirect(url_for("home"))

    # Création d'une archive ZIP contenant tous les fichiers convertis
    zip_path = os.path.join(OUTPUT_FOLDER, "square_wave_files.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for output_file in output_files:
            zipf.write(output_file, os.path.basename(output_file))

    flash("Fichiers convertis avec succès ! Vous pouvez les télécharger ci-dessous.", "success")
    return send_file(zip_path, as_attachment=True)

def low_pass_filter(data, cutoff, fs, order=5):
    """
    Applique un filtre passe-bas pour réduire les hautes fréquences indésirables.
    - data : Les échantillons audio à filtrer.
    - cutoff : Fréquence de coupure du filtre (en Hz).
    - fs : Fréquence d'échantillonnage (en Hz).
    - order : Ordre du filtre.
    """
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return lfilter(b, a, data)

def smooth_square_wave(samples, threshold=0.1):
    """
    Transforme un signal audio en square wave avec un lissage.
    - samples : Les échantillons audio normalisés.
    - threshold : Niveau de transition pour lisser les discontinuités.
    """
    return np.where(samples > threshold, 1, np.where(samples < -threshold, -1, 0))

def convert_to_square_wave(input_file, output_file):
    """Convertit un fichier MP3 en square wave et sauvegarde en WAV."""
    # Charge le fichier MP3 et le convertit en mono WAV
    audio = AudioSegment.from_mp3(input_file)
    audio = audio.set_channels(1)  # Mono
    audio = audio.set_frame_rate(44100)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

    # Normalise les échantillons entre -1 et 1
    samples = samples / np.max(np.abs(samples), axis=0)

    # Filtrage passe-bas pour réduire les hautes fréquences
    filtered_samples = low_pass_filter(samples, cutoff=3000, fs=44100)

    # Transformation en square wave avec lissage
    square_wave = smooth_square_wave(filtered_samples, threshold=0.1)

    # Convertit en entier 16 bits pour le format WAV
    square_wave = np.int16(square_wave * 32767)

    # Sauvegarde en WAV
    write(output_file, 44100, square_wave)

if __name__ == "__main__":
    # Lance l'application Flask
    app.run(debug=False, host="0.0.0.0", port=8080)
