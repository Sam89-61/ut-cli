# Useful Tool — `ut`

CLI hybride PowerShell + Python pour automatiser les tâches du quotidien : système, fichiers, réseau, développement.

---

## ⚡ Installation

### Windows

**Option 1 — Une ligne (recommandé)**

Ouvre PowerShell et colle :

```powershell
irm https://raw.githubusercontent.com/Sam89-61/ut-cli/main/install.ps1 | iex
```



### Linux / macOS

> Requiert [PowerShell Core](https://github.com/PowerShell/PowerShell). Python 3 est installé automatiquement si absent.

**Option 1 — Une ligne (recommandé)**

```bash
curl -fsSL https://raw.githubusercontent.com/Sam89-61/ut-cli/main/install.sh | bash
```


> **Note Windows :** Python 3 est installé automatiquement via `winget` s'il est absent.
> Si `winget` n'est pas disponible sur ton système, installe Python manuellement : [python.org](https://www.python.org/downloads/) — coche **"Add Python to PATH"**.

---

## Commandes

### Système

| Commande | Description |
|---|---|
| `ut info` | CPU, RAM, disques, IP |
| `ut clean` | Nettoie les fichiers temporaires |
| `ut ps list` | Top 20 des processus actifs |
| `ut ps kill <nom>` | Arrête un processus par nom |

### Réseau

| Commande | Description |
|---|---|
| `ut network diag` | IP locale/publique, ping, DNS, ports ouverts |
| `ut network scanport <hote> [debut] [fin]` | Scan d'une plage de ports |
| `ut network speed` | Test de débit Download / Upload |

### Tri de fichiers

| Commande | Description |
|---|---|
| `ut tri <chemin> <motcle>` | Déplace les fichiers contenant `<motcle>` dans un sous-dossier |
| `ut tri <chemin> --type <ext>` | Déplace les fichiers par extension |

```powershell
ut tri C:\Downloads maison       # -> C:\Downloads\maison\
ut tri C:\Downloads --type pdf   # -> C:\Downloads\pdf\
```

### Gestion de fichiers

| Commande | Description |
|---|---|
| `ut file doublons <chemin>` | Liste les fichiers en double (SHA-256) |
| `ut file doublons <chemin> --delete` | Suppression interactive des doublons |
| `ut file heavy <chemin> --min <taille>` | Fichiers volumineux (ex : `--min 500MB`) |
| `ut file rename <chemin> <regex> <rempl>` | Renommage en masse par regex |
| `ut file rename ... --dry-run` | Aperçu sans appliquer |
| `ut file zip <chemin> --age <durée>` | Archive les fichiers anciens (ex : `--age 30d`) |
| `ut file tree <chemin> [--depth N]` | Arborescence visuelle avec tailles |
| `ut file encrypt <fichier>` | Chiffre un fichier (AES + PBKDF2) |
| `ut file decrypt <fichier.enc>` | Déchiffre un fichier `.enc` |

### Recherche de texte

| Commande | Description |
|---|---|
| `ut text search <motcle> <dossier>` | Cherche dans tous les fichiers |
| `... --ext py,ps1` | Filtre par extension(s) |
| `... -i` | Ignore la casse |

### Données

| Commande | Description |
|---|---|
| `ut data convert <fichier> json` | Convertit CSV → JSON |
| `ut data convert <fichier> csv` | Convertit JSON → CSV |
| `... --output <fichier>` | Spécifie le fichier de sortie |

### Outils développeur

| Commande | Description |
|---|---|
| `ut dev pwd` | Génère un mot de passe sécurisé (16 car.) |
| `ut dev pwd --length <n>` | Longueur personnalisée |
| `ut dev pwd --no-special` | Sans caractères spéciaux |
| `ut dev pwd --copy` | Copie dans le presse-papiers |
| `ut dev hash <fichier>` | Calcule MD5 / SHA-1 / SHA-256 |
| `ut dev hash <fichier> --compare <hash>` | Vérifie l'intégrité d'un fichier |

### Autres

| Commande | Description |
|---|---|
| `ut style` | Affiche le logo et la carte des commandes |
| `ut help` | Affiche l'aide complète |

---

## Structure

```
ut-cli/
├── ut.ps1              # Point d'entrée principal
├── install.ps1         # Installateur Windows
├── install.bat         # Installateur Windows (manuel)
├── install.sh          # Installateur Linux/macOS
├── requirements.txt    # Dépendances Python
├── src/
│   ├── powershell/
│   │   ├── system.psm1     # Infos système
│   │   ├── cleanup.psm1    # Nettoyage
│   │   ├── process.psm1    # Processus
│   │   └── network.psm1    # Réseau
│   └── python/
│       ├── tri.py          # Tri de fichiers
│       ├── file.py         # Gestion avancée de fichiers
│       ├── text.py         # Recherche de texte
│       ├── data.py         # Conversion CSV/JSON
│       ├── dev.py          # Outils développeur
│       ├── network.py      # Test de débit
│       └── style.py        # Affichage / logo

```

---

