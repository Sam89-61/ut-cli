set -e

REPO_URL="https://github.com/Sam89-61/ut-cli/archive/refs/heads/main.zip"
TMP_ZIP="/tmp/ut-cli.zip"
TMP_DIR="/tmp/ut-cli-extract"
if [ "$EUID" -eq 0 ]; then
    INSTALL_DIR="/usr/local/share/ut-cli"
    BIN_DIR="/usr/local/bin"
else
    INSTALL_DIR="$HOME/.local/share/ut-cli"
    BIN_DIR="$HOME/.local/bin"
fi

echo ""
echo "  Useful Tool (ut) — Installation"
echo "  ================================"
echo ""
command -v curl >/dev/null 2>&1 || { echo "  Erreur : curl est requis."; exit 1; }
command -v unzip >/dev/null 2>&1 || { echo "  Erreur : unzip est requis."; exit 1; }
if ! command -v pwsh >/dev/null 2>&1; then
    echo "  PowerShell (pwsh) non trouvé. Installation automatique..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get install -y wget apt-transport-https
        source /etc/os-release
        wget -q "https://packages.microsoft.com/config/$ID/$VERSION_ID/packages-microsoft-prod.deb"
        sudo dpkg -i packages-microsoft-prod.deb
        rm packages-microsoft-prod.deb
        sudo apt-get update -y
        sudo apt-get install -y powershell
    elif command -v brew >/dev/null 2>&1; then
        brew install --cask powershell
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y powershell
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm powershell-bin
    else
        echo ""
        echo "  Erreur : impossible d'installer PowerShell automatiquement."
        echo "  Installez-le manuellement : https://github.com/PowerShell/PowerShell"
        echo ""
        exit 1
    fi
    if ! command -v pwsh >/dev/null 2>&1; then
        echo "  Erreur : échec de l'installation de PowerShell."
        exit 1
    fi
    echo "  PowerShell installé."
    echo ""
fi
echo "  Téléchargement..."
curl -fsSL "$REPO_URL" -o "$TMP_ZIP"
echo "  Extraction..."
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"
unzip -q "$TMP_ZIP" -d "$TMP_DIR"
SOURCE_DIR=$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)
echo "  Installation dans $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp -r "$SOURCE_DIR"/. "$INSTALL_DIR/"
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    echo "  Installation des dépendances Python..."
    if ! command -v python3 >/dev/null 2>&1; then
        echo "  Python 3 non trouvé. Installation automatique..."
        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get install -y python3 python3-pip
        elif command -v brew >/dev/null 2>&1; then
            brew install python3
        elif command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y python3 python3-pip
        elif command -v pacman >/dev/null 2>&1; then
            sudo pacman -S --noconfirm python python-pip
        else
            echo ""
            echo "  Erreur : gestionnaire de paquets non reconnu."
            echo "  Installez Python 3 manuellement puis relancez."
            echo ""
            exit 1
        fi
        if ! command -v python3 >/dev/null 2>&1; then
            echo "  Erreur : échec de l'installation de Python 3."
            exit 1
        fi
        echo "  Python 3 installé."
    fi
    python3 -m pip install -r "$INSTALL_DIR/requirements.txt" --quiet --break-system-packages 2>/dev/null \
        || python3 -m pip install -r "$INSTALL_DIR/requirements.txt" --quiet
    echo "  Dépendances Python installées."
    echo "  Dépendances Python installées."
fi
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/ut" << EOF
#!/usr/bin/env bash
exec pwsh -ExecutionPolicy Bypass -File "$INSTALL_DIR/ut.ps1" "\$@"
EOF
chmod +x "$BIN_DIR/ut"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    SHELL_RC="$HOME/.bashrc"
    [ -n "$ZSH_VERSION" ] && SHELL_RC="$HOME/.zshrc"
    echo "" >> "$SHELL_RC"
    echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$SHELL_RC"
    export PATH="$PATH:$BIN_DIR"
    echo "  $BIN_DIR ajouté au PATH dans $SHELL_RC"
fi
rm -f "$TMP_ZIP"
rm -rf "$TMP_DIR"

echo ""
echo "  Installation terminée !"
echo "  Tape 'ut help' depuis n'importe où."
echo "  (Redémarre le terminal si 'ut' n'est pas reconnu)"
echo ""
