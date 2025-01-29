from flask import Flask, render_template, jsonify, send_from_directory
import os
import psutil

app = Flask(__name__)

# Chemins des fichiers et dossiers
LOG_FILE = "/home/foxink/logs/usb_scan_results.log"
HISTORY_DIR = "/home/foxink/logs/scans"

# Fonction : Renvoie les statistiques système
def get_system_stats():
    return {
        "cpu": psutil.cpu_percent(interval=1),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }

# Fonction : Renvoie les logs du scan en cours
def get_scan_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as log:
            return [line.strip() for line in log.readlines()[-10:]]
    return ["Aucun scan en cours."]

# Fonction : Renvoie la liste des dossiers d'historique
def get_scan_history():
    try:
        if os.path.exists(HISTORY_DIR):
            return sorted(os.listdir(HISTORY_DIR))
        return []
    except Exception as e:
        return [f"Erreur : {e}"]

# Route principale : Affiche la page HTML
@app.route("/")
def index():
    return render_template("index.html")

# Route principale : affiche le css
@app.route('/style.css')
def style():
    return send_from_directory('/usr/local/bin/templates', 'style.css')

# Route principale : affiche le favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        '/usr/local/bin/templates',
        'favicon.png',
        mimetype='image/png'
    )

#Route principale : affiche l'image vinci-autoroutes
@app.route('/logo_vinci.png')
def vinci_logo():
    return send_from_directory('/usr/local/bin/templates', 'logo_vinci.png')

# API : Informations système
@app.route("/api/system")
def api_system():
    return jsonify(get_system_stats())

# API : Logs en direct
@app.route("/api/logs")
def api_logs():
    return jsonify(get_scan_logs())

# API : Historique des scans
@app.route("/api/history")
def api_history():
    return jsonify(get_scan_history())

# API : Afficher un fichier d'historique spécifique
@app.route("/api/history/<filename>")
def api_view_history(filename):
    try:
        file_path = os.path.join(HISTORY_DIR, filename)
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                return jsonify(file.readlines())
        else:
            return jsonify({"error": "Fichier introuvable."})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
