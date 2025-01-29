import os
import time
import subprocess
import shutil
from datetime import datetime

# Chemins des logs et des montages
MOUNT_BASE_PATH = "/media"
LOG_FILE = "/home/foxink/logs/usb_scan_results.log"
HISTORY_DIR = "/home/foxink/logs/scans"
SCAN_LOCK_FILE = "/tmp/usb_scan.lock"

# Fonction : Vérifie que les dossiers nécessaires existent
def ensure_directories():
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)
        print(f"[INFO] Création du dossier d'historique : {HISTORY_DIR}")
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as log:
            log.write("")
            print("[INFO] Fichier de logs créé : usb_scan_results.log")

# Fonction : Réinitialise les logs
def reset_logs():
    try:
        with open(LOG_FILE, "w") as log:
            log.write("")  # Vide le fichier de logs
        print("[INFO] Fichier de logs vidé (reset).")
    except Exception as e:
        print(f"[ERREUR] Impossible de vider les logs : {e}")

# Fonction : Mise à jour des messages dans les logs
def update_message(message):
    print(f"[LOG] {message}")
    try:
        with open(LOG_FILE, "a") as log:
            log.write(message + "\n")
    except Exception as e:
        print(f"[ERREUR] Impossible d'écrire dans les logs : {e}")

# Fonction : Récupérer les informations de la clé USB
def get_usb_info(mount_path):
    try:
        total_size = subprocess.check_output(["du", "-sh", mount_path]).decode().split()[0]
        label = os.path.basename(mount_path)
        return f"Nom: {label}, Taille: {total_size}"
    except Exception as e:
        return f"Erreur lors de la récupération des informations de la clé USB : {e}"

# Fonction : Archiver les logs
def archive_logs():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_file = os.path.join(HISTORY_DIR, f"{timestamp}_scan.log")
    try:
        # Copie les logs existants vers l'archive sans supprimer usb_scan_results.log
        shutil.copy(LOG_FILE, archive_file)
        print(f"[INFO] Logs archivés dans : {archive_file}")
    except Exception as e:
        print(f"[ERREUR] Impossible d'archiver les logs : {e}")

# Fonction : Scan de la clé USB
def scan_usb(mount_path):
    # Vérifie si un scan est déjà en cours
    if os.path.exists(SCAN_LOCK_FILE):
        with open(SCAN_LOCK_FILE, "r") as lock:
            if lock.read().strip() == mount_path:
                update_message(f"Un scan est déjà en cours pour : {mount_path}")
                return

    try:
        # Verrouille le fichier pour empêcher d'autres scans
        with open(SCAN_LOCK_FILE, "w") as lock:
            lock.write(mount_path)

        # Réinitialiser les logs pour une nouvelle analyse
        reset_logs()

        # Informations sur la clé USB
        usb_info = get_usb_info(mount_path)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_message(f"Clé USB détectée à {timestamp}")
        update_message(f"Informations de la clé USB : {usb_info}")

        # Lancer ClamAV pour scanner les fichiers
        update_message(f"Début de l'analyse de la clé USB montée sur {mount_path}...")
        result = subprocess.run(["clamscan", "-r", mount_path, "--stdout"], capture_output=True, text=True)
        scanned_lines = result.stdout.splitlines()

        # Analyser les fichiers infectés
        infected_files = [
            line for line in scanned_lines if "FOUND" in line and not line.startswith("-----------")
        ]

        # Ajouter les fichiers infectés aux logs
        if infected_files:
            update_message("Fichiers infectés détectés :")
            for file in infected_files:
                update_message(f"!!! {file.strip()} !!!")
        else:
            update_message("Aucune menace détectée. La clé USB est sûre.")

        # Résumé du scan
        update_message("\n".join(scanned_lines))

        if infected_files:
            update_message("Menace détectée ! La clé USB est infectée.")
            update_message("Clé USB infectée. Accès bloqué.")

        # Démontage de la clé USB après le scan
        update_message(f"Démontage de la clé USB montée sur {mount_path}...")
        subprocess.run(["umount", mount_path])
        update_message("Clé USB démontée.")

        # Archiver les logs après un scan réussi
        archive_logs()
        reset_logs()

    except Exception as e:
        update_message(f"Erreur lors de l'analyse : {e}")
    finally:
        # Supprime le verrou après le scan
        if os.path.exists(SCAN_LOCK_FILE):
            os.remove(SCAN_LOCK_FILE)

# Fonction : Surveiller les clés USB
def monitor_usb():
    mounted_devices = set()
    while True:
        time.sleep(2)
        current_mounts = {os.path.join(MOUNT_BASE_PATH, d) for d in os.listdir(MOUNT_BASE_PATH) if os.path.ismount(os.path.join(MOUNT_BASE_PATH, d))}
        new_mounts = current_mounts - mounted_devices
        removed_mounts = mounted_devices - current_mounts

        # Traiter les nouvelles clés USB
        for mount_path in new_mounts:
            update_message(f"Clé USB détectée sur {mount_path}. Début de l'analyse...")
            scan_usb(mount_path)

        # Ignorer les clés USB retirées mais vider les logs
        for mount_path in removed_mounts:
            reset_logs()  # Vide simplement les logs sans supprimer le fichier

        # Mettre à jour les montages actuellement surveillés
        mounted_devices = current_mounts

if __name__ == "__main__":
    ensure_directories()
    reset_logs()
    update_message("Démarrage du moniteur USB...")
    monitor_usb()
