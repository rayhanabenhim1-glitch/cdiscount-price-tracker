# -*- coding: utf-8 -*-
"""
PROJET SEMESTRE - ANALYSEUR CDISCOUNT
Version: AVEC ALERTES MAIL - Surveille les baisses de prix automatiquement!
"""

import sys
import os
import subprocess
import importlib.util
import json

# ====================================
# AUTO-INSTALLATION
# ====================================
def auto_install():
    """Installe tout automatiquement"""
    print("🔧 Installation automatique...")
    
    packages = [
        "selenium",
        "webdriver-manager",
        "requests",
        "beautifulsoup4"
    ]
    
    for package in packages:
        try:
            if importlib.util.find_spec(package.replace("-", "_")) is None:
                print(f"📦 Installation de {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ {package} installé")
        except:
            print(f"⚠️ Problème avec {package}")
    
    print("✅ Installation terminée!\n")

auto_install()

# ====================================
# IMPORTS
# ====================================
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import tkinter as tk
from tkinter import messagebox, simpledialog
import csv
import re
import time
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from urllib.parse import urlparse
import urllib.robotparser
import logging
import argparse
import platform
import tempfile

# ====================================
# CONFIGURATION
# ====================================
def get_data_dir():
    """Crée un dossier 'data' là où se trouve le script"""
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(directory, exist_ok=True)
    return directory

DATA_DIR = get_data_dir()
FICHIER_HISTO = os.path.join(DATA_DIR, "historique_prix.csv")
FICHIER_LOG = os.path.join(DATA_DIR, "scraper.log")
FICHIER_CONFIG = os.path.join(DATA_DIR, "config.json")

logging.basicConfig(level=logging.INFO, filename=FICHIER_LOG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ====================================
# GESTIONNAIRE DE CONFIGURATION EMAIL
# ====================================
class EmailConfig:
    """Gère la configuration email de façon persistante"""
    
    @staticmethod
    def load():
        """Charge la configuration sauvegardée"""
        if os.path.exists(FICHIER_CONFIG):
            try:
                with open(FICHIER_CONFIG, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    @staticmethod
    def save(config):
        """Sauvegarde la configuration"""
        try:
            with open(FICHIER_CONFIG, 'w') as f:
                json.dump(config, f)
            return True
        except:
            return False
    
    @staticmethod
    def ask_email_config():
        """Demande la configuration email à l'utilisateur"""
        config = {}
        
        # Créer une fenêtre de dialogue personnalisée
        dialog = tk.Toplevel()
        dialog.title("Configuration Email")
        dialog.geometry("400x300")
        dialog.transient()  # Fenêtre modale
        dialog.grab_set()
        
        tk.Label(dialog, text="🔐 CONFIGURATION EMAIL", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(dialog, text="Pour recevoir les alertes de baisse de prix", font=("Arial", 10)).pack()
        
        tk.Label(dialog, text="Email expéditeur (Gmail):").pack(pady=5)
        entry_email = tk.Entry(dialog, width=40)
        entry_email.pack()
        entry_email.insert(0, "votre.email@gmail.com")
        
        tk.Label(dialog, text="Mot de passe d'application:", font=("Arial", 9)).pack(pady=5)
        tk.Label(dialog, text="(Généré depuis https://myaccount.google.com/apppasswords)", 
                font=("Arial", 8), fg="gray").pack()
        entry_password = tk.Entry(dialog, width=40, show="*")
        entry_password.pack()
        
        tk.Label(dialog, text="Email destinataire (pour les alertes):").pack(pady=5)
        entry_dest = tk.Entry(dialog, width=40)
        entry_dest.pack()
        entry_dest.insert(0, "destinataire@gmail.com")
        
        result = []
        
        def save_config():
            config['email_expediteur'] = entry_email.get()
            config['mot_de_passe'] = entry_password.get()
            config['email_destinataire'] = entry_dest.get()
            result.append(config)
            dialog.destroy()
        
        def skip_config():
            result.append(None)
            dialog.destroy()
        
        tk.Button(dialog, text="💾 Sauvegarder", command=save_config, 
                 bg="green", fg="white", width=15).pack(pady=10)
        tk.Button(dialog, text="⏭️ Ignorer (pas d'alertes)", command=skip_config, 
                 bg="gray", fg="white", width=15).pack()
        
        dialog.wait_window()
        
        return result[0] if result else None

# ====================================
# GESTIONNAIRE CHROME
# ====================================
def get_chrome_driver():
    """
    Lance Chrome de façon portable (Mac / Windows / Linux)
    Fallback automatique vers Edge sur Windows
    """

    # === OPTIONS COMMUNES ===
    options = Options()
    options.add_argument("--headless=new")  # Nouveau mode headless plus stable
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # === ESSAYER CHROME D'ABORD ===
    try:
        print("🔄 Tentative avec Chrome...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ Chrome lancé avec succès")
        return driver

    except Exception as chrome_error:
        print(f"⚠️ Chrome non disponible: {str(chrome_error)[:50]}...")
        print("🔄 Tentative avec Edge...")

    # === FALLBACK VERS EDGE (POUR WINDOWS) ===
    try:
        from selenium.webdriver.edge.service import Service as EdgeService
        from selenium.webdriver.edge.options import Options as EdgeOptions
        
        edge_options = EdgeOptions()
        edge_options.add_argument("--headless=new")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--window-size=1920,1080")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--disable-blink-features=AutomationControlled")
        edge_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0')
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        edge_service = EdgeService(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=edge_service, options=edge_options)
        
        print("✅ Edge lancé avec succès")
        return driver

    except Exception as edge_error:
        logger.error(f"Erreur Edge: {edge_error}")
        
        # === DERNIÈRE TENTATIVE: CHROME SANS WEBDRIVER MANAGER ===
        try:
            print("🔄 Dernière tentative: Chrome sans WebDriver Manager...")
            driver = webdriver.Chrome(options=options)
            print("✅ Chrome lancé sans WebDriver Manager")
            return driver
        except Exception as final_error:
            logger.error(f"Erreur finale: {final_error}")
            messagebox.showerror(
                "Erreur navigateur",
                "Aucun navigateur compatible trouvé.\n\n"
                "Installez Google Chrome ou Microsoft Edge.\n"
                "Ou vérifiez votre connexion internet (besoin de télécharger les drivers)."
            )
            sys.exit(1)

# ====================================
# ROBOTS.TXT PARSER
# ====================================
class RobotsChecker:
    def __init__(self):
        self.rp = urllib.robotparser.RobotFileParser()
        self.crawl_delay = 2

    def check_robots(self, url):
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            robots_url = f"{base_url}/robots.txt"
            
            self.rp.set_url(robots_url)
            self.rp.read()
            allowed = self.rp.can_fetch("*", url)
            
            try:
                delay = self.rp.crawl_delay("*")
                if delay:
                    self.crawl_delay = delay
            except:
                pass
            
            return allowed
        except Exception as e:
            logger.error(f"Erreur robots.txt: {e}")
            return True

# ====================================
# CLASSE PRODUIT
# ====================================
class Product:
    def __init__(self, title, price, note=0, livraison="Non spécifié", url=""):
        self.title = title
        self.price = price
        self.note = note
        self.livraison = livraison
        self.url = url
        self.score = 0
        self.rank = 0
        self.recommendation = ""
        self.scraped_at = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.calculer_score()
    
    def calculer_score(self):
        score = 0
        
        if self.price < 200:
            score += 5
        elif self.price < 300:
            score += 4
        elif self.price < 400:
            score += 3
        elif self.price < 500:
            score += 2
        else:
            score += 1
        
        if self.note >= 4.5:
            score += 3
        elif self.note >= 4:
            score += 2.5
        elif self.note >= 3:
            score += 2
        elif self.note >= 2:
            score += 1
        elif self.note > 0:
            score += 0.5
        
        livraison_lower = self.livraison.lower()
        if "gratuite" in livraison_lower or "free" in livraison_lower:
            score += 2
        elif "express" in livraison_lower or "24h" in livraison_lower:
            score += 1
        
        self.score = round(score, 1)
        
        if self.score >= 8:
            self.recommendation = "🔥 EXCELLENTE AFFAIRE"
        elif self.score >= 6:
            self.recommendation = "👍 BONNE AFFAIRE"
        elif self.score >= 4:
            self.recommendation = "⚖️ Offre correcte"
        else:
            self.recommendation = "⚠️ Offre peu attractive"
        
        return self.score

# ====================================
# SCRAPER
# ====================================
class CdiscountScraper:
    def __init__(self):
        self.robots = RobotsChecker()
        self.products = []
        
        try:
            self.driver = get_chrome_driver()
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            logger.error(f"Erreur initialisation: {e}")
            messagebox.showerror("Erreur", 
                f"Impossible de démarrer Chrome.\n"
                f"Vérifie que Google Chrome est installé!")
            sys.exit(1)

    def search_products(self, query, max_pages=2):
        self.products = []
        titres_deja_vus = []
        
        url_base = f"https://www.cdiscount.com/search/10/{query}.html"
        if not self.robots.check_robots(url_base):
            return []
        
        try:
            for page in range(1, max_pages + 1):
                url = f"https://www.cdiscount.com/search/10/{query.replace(' ', '+')}.html?page={page}"
                
                self.driver.get(url)
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(self.robots.crawl_delay)
                
                links = []
                elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/f-']")
                for el in elements[:10]:
                    href = el.get_attribute("href")
                    if href and href not in links:
                        links.append(href)
                
                for link in links:
                    if len(self.products) >= 5:
                        break
                    
                    time.sleep(self.robots.crawl_delay)
                    product = self.analyze_product(link)
                    
                    if product and product.title not in titres_deja_vus:
                        titres_deja_vus.append(product.title)
                        self.products.append(product)
                
                if len(self.products) >= 5:
                    break
                    
        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
        
        return self.products

    def analyze_product(self, url):
        try:
            if not self.robots.check_robots(url):
                return None
            
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            
            try:
                titre = self.driver.find_element(By.TAG_NAME, "h1").text
            except:
                return None
            
            prix = 0
            selecteurs_prix = ["span[itemprop='price']", ".price", ".prdtPrice", "span.sc-e4stwg-1"]
            
            for selecteur in selecteurs_prix:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selecteur)
                    for el in elements:
                        texte = el.text
                        if texte and any(c.isdigit() for c in texte):
                            texte_propre = re.sub(r'[^\d,.]', '', texte)
                            texte_propre = texte_propre.replace(',', '.')
                            match = re.search(r'(\d+\.?\d*)', texte_propre)
                            if match:
                                prix = float(match.group(1))
                                break
                    if prix > 0:
                        break
                except:
                    continue
            
            if prix == 0:
                return None
            
            note = 0
            try:
                note_elem = self.driver.find_element(By.CSS_SELECTOR, "span.ratingValue, .ac_rating")
                note_text = note_elem.text.replace(',', '.')
                note_match = re.search(r'(\d+\.?\d*)', note_text)
                if note_match:
                    note = float(note_match.group(1))
            except:
                pass
            
            livraison = "Standard"
            try:
                livraison_elem = self.driver.find_element(By.XPATH, "//*[contains(text(),'Livraison')]")
                livraison = livraison_elem.text[:50]
            except:
                pass
            
            return Product(titre, prix, note, livraison, url)
            
        except Exception as e:
            logger.error(f"Erreur analyse produit: {e}")
            return None

    def get_top_3(self):
        if not self.products:
            return []
        
        sorted_products = sorted(self.products, key=lambda x: x.score, reverse=True)
        
        for i, p in enumerate(sorted_products[:3], 1):
            p.rank = i
            
        return sorted_products[:3]

    def close(self):
        try:
            self.driver.quit()
        except:
            pass

# ====================================
# FONCTIONS DE GESTION (avec alertes mail)
# ====================================
def sauvegarder_historique(produits):
    """Sauvegarde et détecte les baisses de prix"""
    try:
        historique = {}
        
        # Charger l'historique existant
        if os.path.exists(FICHIER_HISTO):
            with open(FICHIER_HISTO, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) >= 2:
                        try:
                            historique[row[0]] = float(row[1])
                        except:
                            pass
        
        # Détecter les baisses de prix
        alertes = []
        for p in produits:
            if p.title in historique and p.price < historique[p.title]:
                alertes.append({
                    'titre': p.title,
                    'ancien_prix': historique[p.title],
                    'nouveau_prix': p.price,
                    'url': p.url
                })
        
        # Sauvegarder les nouveaux prix
        with open(FICHIER_HISTO, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Produit", "Prix", "Date"])
            for p in produits:
                writer.writerow([p.title, p.price, p.scraped_at])
        
        return alertes
        
    except Exception as e:
        logger.error(f"Erreur historique: {e}")
        return []

def envoyer_alerte_email(alertes, config_email):
    """Envoie un email pour chaque baisse de prix détectée"""
    if not alertes or not config_email:
        return False
    
    try:
        expediteur = config_email.get('email_expediteur')
        mot_de_passe = config_email.get('mot_de_passe')
        destinataire = config_email.get('email_destinataire')
        
        if not all([expediteur, mot_de_passe, destinataire]):
            return False
        
        # Créer le message
        msg = MIMEMultipart()
        msg['Subject'] = f"🔔 ALERTE PRIX CDISCOUNT - {len(alertes)} baisse(s) détectée(s) !"
        msg['From'] = expediteur
        msg['To'] = destinataire
        
        # Corps du message en HTML
        corps = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .alerte { border: 1px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .titre { font-size: 16px; font-weight: bold; color: #333; }
                .prix { font-size: 14px; }
                .ancien { color: red; text-decoration: line-through; }
                .nouveau { color: green; font-weight: bold; font-size: 18px; }
                .economie { color: #CC0000; font-weight: bold; }
                .lien { background-color: #CC0000; color: white; padding: 5px 10px; 
                        text-decoration: none; border-radius: 3px; display: inline-block; }
            </style>
        </head>
        <body>
            <h2>🛍️ Alertes de baisse de prix sur Cdiscount</h2>
        """
        
        for a in alertes:
            economie = a['ancien_prix'] - a['nouveau_prix']
            pourcentage = (economie / a['ancien_prix']) * 100
            
            corps += f"""
            <div class='alerte'>
                <div class='titre'>{a['titre'][:100]}</div>
                <div class='prix'>
                    Ancien prix: <span class='ancien'>{a['ancien_prix']:.2f}€</span><br>
                    Nouveau prix: <span class='nouveau'>{a['nouveau_prix']:.2f}€</span><br>
                    <span class='economie'>Économie: {economie:.2f}€ (-{pourcentage:.1f}%)</span>
                </div>
                <p><a href='{a['url']}' class='lien'>VOIR LE PRODUIT</a></p>
            </div>
            """
        
        corps += """
            <hr>
            <p style='color: gray; font-size: 12px;'>
                Email envoyé automatiquement par l'Analyseur Cdiscount<br>
                Pour vous désabonner, ignorez simplement ces emails.
            </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(corps, 'html'))
        
        # Envoyer l'email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(expediteur, mot_de_passe)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email d'alerte envoyé à {destinataire}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur envoi email: {e}")
        return False

# ====================================
# INTERFACE GRAPHIQUE
# ====================================
class Application:
    def __init__(self):
        self.config_email = EmailConfig.load()
        self.setup_gui()
    
    def setup_gui(self):
        self.fenetre = tk.Tk()
        self.fenetre.title("Analyseur Cdiscount")
        self.fenetre.geometry("850x750")
        
        # Menu
        menubar = tk.Menu(self.fenetre)
        self.fenetre.config(menu=menubar)
        
        config_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="⚙️ Configuration", menu=config_menu)
        config_menu.add_command(label="📧 Configurer Email", command=self.configurer_email)
        config_menu.add_command(label="📂 Ouvrir dossier données", command=self.ouvrir_dossier)
        
        # Titre
        tk.Label(self.fenetre, text="🛍️ ANALYSEUR CDISCOUNT", 
                font=("Arial", 20, "bold")).pack(pady=20)
        
        # État email
        self.email_status = tk.Label(self.fenetre, 
                                     text="✓ Alertes email actives" if self.config_email else "✗ Alertes email non configurées",
                                     fg="green" if self.config_email else "red",
                                     font=("Arial", 9))
        self.email_status.pack()
        
        # Input
        tk.Label(self.fenetre, text="Produit à rechercher:").pack()
        self.entry_produit = tk.Entry(self.fenetre, width=50, font=("Arial", 11))
        self.entry_produit.pack(pady=5)
        self.entry_produit.insert(0, "iphone")
        
        # Bouton
        self.bouton = tk.Button(self.fenetre, text="🚀 LANCER L'ANALYSE", 
                               command=self.lancer_analyse,
                               bg="#CC0000", fg="white", font=("Arial", 12, "bold"), 
                               height=2, width=20)
        self.bouton.pack(pady=20)
        
        # Résultats
        tk.Label(self.fenetre, text="Résultats:").pack()
        
        self.text_resultat = tk.Text(self.fenetre, height=20, width=80, font=("Courier", 10))
        self.text_resultat.pack(pady=10)
        self.text_resultat.config(state="disabled")
        
        # Info dossier
        tk.Label(self.fenetre, text=f"📁 Données: {DATA_DIR}", 
                font=("Arial", 8), fg="gray").pack()
        
        # Vérifier si besoin de config email au premier lancement
        if not self.config_email:
            self.fenetre.after(1000, self.demander_config_email)
    
    def demander_config_email(self):
        """Propose de configurer l'email au premier lancement"""
        reponse = messagebox.askyesno(
            "Configuration Email",
            "Voulez-vous configurer les alertes email pour être prévenu des baisses de prix ?\n\n"
            "(Vous pourrez toujours le faire plus tard depuis le menu Configuration)"
        )
        if reponse:
            self.configurer_email()
    
    def configurer_email(self):
        """Ouvre la fenêtre de configuration email"""
        config = EmailConfig.ask_email_config()
        if config:
            self.config_email = config
            EmailConfig.save(config)
            self.email_status.config(text="✓ Alertes email actives", fg="green")
            messagebox.showinfo("Succès", "Configuration email sauvegardée !")
    
    def ouvrir_dossier(self):
        """Ouvre le dossier des données"""
        try:
            if platform.system() == "Windows":
                os.startfile(DATA_DIR)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", DATA_DIR])
            else:  # Linux
                subprocess.run(["xdg-open", DATA_DIR])
        except:
            messagebox.showinfo("Dossier", f"Les données sont dans:\n{DATA_DIR}")
    
    def lancer_analyse(self):
        produit = self.entry_produit.get()
        
        if not produit:
            messagebox.showwarning("", "Veuillez entrer un produit!")
            return
        
        self.bouton.config(state="disabled", text="Analyse en cours...")
        self.fenetre.update()
        
        self.text_resultat.config(state="normal")
        self.text_resultat.delete("1.0", tk.END)
        
        scraper = None
        try:
            scraper = CdiscountScraper()
            scraper.search_products(produit)
            top_3 = scraper.get_top_3()
            
            if top_3:
                # Sauvegarder et vérifier les alertes
                alertes = sauvegarder_historique(top_3)
                
                # Afficher les résultats
                self.text_resultat.insert(tk.END, f"TOP 3 POUR: {produit}\n")
                self.text_resultat.insert(tk.END, "="*40 + "\n\n")
                
                for p in top_3:
                    self.text_resultat.insert(tk.END, f"{p.rank}. {p.recommendation}\n")
                    self.text_resultat.insert(tk.END, f"📦 {p.title[:70]}\n")
                    self.text_resultat.insert(tk.END, f"💰 {p.price}€")
                    if p.note > 0:
                        self.text_resultat.insert(tk.END, f" | ⭐ {p.note}/5")
                    self.text_resultat.insert(tk.END, f"\n📦 {p.livraison}\n")
                    self.text_resultat.insert(tk.END, f"📊 Score: {p.score}/10\n")
                    self.text_resultat.insert(tk.END, "-"*30 + "\n\n")
                
                # Gérer les alertes
                if alertes:
                    self.text_resultat.insert(tk.END, "📉 BAISSES DE PRIX DÉTECTÉES !\n")
                    for a in alertes:
                        economie = a['ancien_prix'] - a['nouveau_prix']
                        self.text_resultat.insert(tk.END, 
                            f"   {a['titre'][:50]}...\n"
                            f"   {a['ancien_prix']}€ -> {a['nouveau_prix']}€ "
                            f"(économies: {economie:.2f}€)\n\n"
                        )
                    
                    # Envoyer les alertes par email si configuré
                    if self.config_email:
                        if envoyer_alerte_email(alertes, self.config_email):
                            self.text_resultat.insert(tk.END, "📧 ALERTES EMAIL ENVOYÉES !\n\n")
                        else:
                            self.text_resultat.insert(tk.END, "⚠️ Échec envoi email\n\n")
                    else:
                        self.text_resultat.insert(tk.END, 
                            "ℹ️ Configurez l'email dans le menu pour recevoir des alertes\n\n")
                
                messagebox.showinfo("", f"Terminé! {len(top_3)} produits trouvés.")
            else:
                self.text_resultat.insert(tk.END, "Aucun produit trouvé.\n")
                messagebox.showwarning("", "Aucun produit trouvé!")
                
        except Exception as e:
            logger.error(f"Erreur: {e}")
            self.text_resultat.insert(tk.END, f"❌ Erreur: {str(e)[:200]}\n")
        finally:
            if scraper:
                scraper.close()
            
            self.bouton.config(state="normal", text="🚀 LANCER L'ANALYSE")
            self.text_resultat.config(state="disabled")
    
    def run(self):
        self.fenetre.mainloop()

# ====================================
# POINT D'ENTRÉE
# ====================================
if __name__ == "__main__":
    print("="*50)
    print("🛍️ ANALYSEUR CDISCOUNT - AVEC ALERTES EMAIL")
    print("="*50)
    print(f"📁 Dossier de travail: {DATA_DIR}")
    print("="*50 + "\n")
    
    app = Application()
    app.run()