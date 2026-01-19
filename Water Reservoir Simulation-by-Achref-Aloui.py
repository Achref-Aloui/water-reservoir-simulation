import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import random
from datetime import datetime

# LOGIQUE ET BASE DE DONNÉES

class DatabaseHandler:
    """Gère la persistance des données avec SQLite."""

    def __init__(self, db_name="reservoir_data.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS historique (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_heure TEXT,
                action TEXT,
                volume REAL,
                niveau_resultat REAL
            )
        ''')
        self.conn.commit()

    def ajouter_entree(self, action, volume, niveau):
        maintenant = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO historique (date_heure, action, volume, niveau_resultat)
            VALUES (?, ?, ?, ?)
        ''', (maintenant, action, volume, niveau))
        self.conn.commit()

    def recuperer_historique(self):
        self.cursor.execute("SELECT * FROM historique ORDER BY id DESC LIMIT 20")
        return self.cursor.fetchall()

# PARTIE 2 : INTERFACE GRAPHIQUE (GUI)

class ReservoirApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulateur de Réservoir d'Eau - iTeam Project")
        self.root.geometry("600x700")

        # Données du réservoir
        self.capacite_max = 1000.0
        self.niveau_actuel = 500.0
        self.seuil_min = 200.0
        self.seuil_max = 800.0

        # Stats
        self.vol_entre = 0.0
        self.vol_sorti = 0.0
        self.alertes_count = 0
        self.en_pause = True

        self.db = DatabaseHandler()

        self.setup_ui()
        self.update_display()

    def setup_ui(self):
        """Configuration de l'interface utilisateur."""
        # Titre
        tk.Label(self.root, text="Gestion du Réservoir", font=("Arial", 18, "bold")).pack(pady=10)

        # Zone de la Jauge
        self.canvas = tk.Canvas(self.root, width=150, height=300, bg="white", highlightthickness=2)
        self.canvas.pack(pady=10)
        self.water_rect = self.canvas.create_rectangle(2, 300, 148, 300, fill="#3498db", outline="")

        # Seuils visuels sur la jauge
        self.canvas.create_line(0, 300 - (self.seuil_max / self.capacite_max * 300), 150,
                                300 - (self.seuil_max / self.capacite_max * 300), fill="red", dash=(4, 4))
        self.canvas.create_line(0, 300 - (self.seuil_min / self.capacite_max * 300), 150,
                                300 - (self.seuil_min / self.capacite_max * 300), fill="orange", dash=(4, 4))

        # Étiquette de pourcentage
        self.lbl_percent = tk.Label(self.root, text="0%", font=("Arial", 14, "bold"))
        self.lbl_percent.pack()

        # Informations détaillées
        self.info_frame = tk.Frame(self.root)
        self.info_frame.pack(pady=10)

        self.lbl_niveau = tk.Label(self.info_frame, text="Niveau: 0 L", font=("Arial", 11))
        self.lbl_niveau.grid(row=0, column=0, padx=20)

        self.lbl_alertes = tk.Label(self.info_frame, text="Alertes: 0", fg="red", font=("Arial", 11))
        self.lbl_alertes.grid(row=0, column=1, padx=20)

        # Boutons de contrôle
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.btn_start = tk.Button(btn_frame, text="Démarrer Simulation", command=self.toggle_sim, bg="#2ecc71",
                                   fg="white", width=20)
        self.btn_start.grid(row=0, column=0, padx=5)

        tk.Button(btn_frame, text="Réinitialiser", command=self.reset_sim, width=15).grid(row=0, column=1, padx=5)

        # Historique 
        tk.Label(self.root, text="Historique (Dernières actions) :").pack(pady=(10, 0))
        self.tree = ttk.Treeview(self.root, columns=("Action", "Volume", "Niveau"), show="headings", height=5)
        self.tree.heading("Action", text="Action")
        self.tree.heading("Volume", text="Volume (L)")
        self.tree.heading("Niveau", text="Niveau Final (L)")
        self.tree.column("Action", width=100)
        self.tree.column("Volume", width=100)
        self.tree.column("Niveau", width=100)
        self.tree.pack(pady=5, padx=10, fill=tk.X)

    def update_display(self):
        """Met à jour les éléments visuels."""
        pourcentage = (self.niveau_actuel / self.capacite_max) * 100
        height = (self.niveau_actuel / self.capacite_max) * 300

        # Mise à jour jauge
        self.canvas.coords(self.water_rect, 2, 300 - height, 148, 300)
        self.lbl_percent.config(text=f"{pourcentage:.1f} %")
        self.lbl_niveau.config(text=f"Niveau: {self.niveau_actuel:.2f} L / {self.capacite_max} L")
        self.lbl_alertes.config(text=f"Alertes: {self.alertes_count}")

    def verifier_seuils(self):
        """Vérifie les seuils et affiche des popups."""
        if self.niveau_actuel > self.seuil_max:
            self.alertes_count += 1
            messagebox.showwarning("ALERTE", f"Risque de débordement !\nNiveau: {self.niveau_actuel:.1f}L")
        elif self.niveau_actuel < self.seuil_min:
            self.alertes_count += 1
            messagebox.showwarning("ALERTE", f"Niveau critique bas !\nNiveau: {self.niveau_actuel:.1f}L")

    def appliquer_flux(self):
        """Simule une étape de flux aléatoire."""
        if self.en_pause: return

        type_f = random.choice(["entrée", "sortie"])
        debit = random.uniform(20, 80)  # Litres par minute
        duree = 1  # On simule minute par minute
        volume_tentative = debit * duree

        if type_f == "entrée":
            # Gestion débordement physique
            volume_reel = min(volume_tentative, self.capacite_max - self.niveau_actuel)
            self.niveau_actuel += volume_reel
            self.vol_entre += volume_reel
        else:
            # Gestion vidange physique
            volume_reel = min(volume_tentative, self.niveau_actuel)
            self.niveau_actuel -= volume_reel
            self.vol_sorti += volume_reel

        # Journalisation
        if volume_reel > 0:
            self.db.ajouter_entree(type_f, volume_reel, self.niveau_actuel)
            self.tree.insert("", 0, values=(type_f, f"{volume_reel:.1f}", f"{self.niveau_actuel:.1f}"))

        self.update_display()
        self.verifier_seuils()

        # Prochaine étape dans 2 secondes
        self.root.after(2000, self.appliquer_flux)

    def toggle_sim(self):
        if self.en_pause:
            self.en_pause = False
            self.btn_start.config(text="Pause", bg="#e67e22")
            self.appliquer_flux()
        else:
            self.en_pause = True
            self.btn_start.config(text="Reprendre", bg="#2ecc71")

    def reset_sim(self):
        self.en_pause = True
        self.niveau_actuel = 500.0
        self.alertes_count = 0
        self.btn_start.config(text="Démarrer Simulation", bg="#2ecc71")
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.update_display()
        messagebox.showinfo("Reset", "Simulateur réinitialisé.")

# LANCEMENT
if __name__ == "__main__":
    root = tk.Tk()
    app = ReservoirApp(root)
    root.mainloop()