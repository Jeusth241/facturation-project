# Application de Facturation - Django & DocxTPL

Application web Django permettant la création, le calcul et la génération automatique de factures (Services et Ventes de produits) au format Word (`.docx`) et PDF.

---

## Fonctionnalités

- **Gestion des factures** : Formulaire dynamique pour la création de factures de prestation de services ou de vente de produits.
- **Calculs automatiques** : Montants HT, TTC, prélèvements, avances, régulations et conversion du net à payer en lettres (`num2words`).
- **Génération Word & PDF** :
  - Génération de documents `.docx` propres via `docxtpl` et `python-docx`.
  - Conversion automatique en PDF.
- **Script de réinitialisation des modèles** : Génération automatique de templates `.docx` simples et valides (sans risquer d'erreurs de syntaxe XML/Jinja2).

---

## Prérequis

1. **Python 3.10+**
2. **LibreOffice** ou **Microsoft Word** (nécessaire sur le système pour la conversion automatique des fichiers `.docx` en `.pdf`).

---

## Installation

### 1. Cloner le projet et créer un environnement virtuel
```bash
python -m venv venv
# Sur Windows :
venv\Scripts\activate
# Sur Linux/Mac :
source venv/bin/activate
```

### 2. Installer les dépendances Python
```bash
pip install -r requirements.txt
```

### 3. Appliquer les migrations Django
```bash
python manage.py migrate
```

---

##  Génération des modèles Word de base

Avant de lancer la création de documents, exécutez le script de réinitialisation pour générer les templates `.docx` neutres (sans fioritures de mise en page) :

```bash
python reset_templates.py
```

Ce script va créer deux fichiers simples dans `templates/docx/` :
- `Facture_Atelier_Mobile.docx` (Modèle Prestation / Service)
- `Facture_Vente_Atelier_Mobile.docx` (Modèle Produit / Vente)

---

## Lancement de l'application

Lancez le serveur de développement Django :

```bash
python manage.py runserver
```

Accédez à l'application dans votre navigateur : [http://127.0.0.1:8000/documents/nouveau/](http://127.0.0.1:8000/documents/nouveau/)

---

## 📁 Structure du projet

```text
facturation_project/
├── documents/
│   ├── models.py
│   ├── views.py
│   ├── utils.py          # Logique de remplissage docxtpl & conversion PDF
│   └── forms.py
├── templates/
│   └── docx/            # Emplacement des fichiers .docx générés
├── reset_templates.py   # Script de génération des modèles simples
├── requirements.txt
└── README.md
```