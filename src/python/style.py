import sys
import io
import argparse

# Forcer UTF-8 pour les caractères Unicode du logo (Windows cp1252 par défaut)
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich.padding import Padding
from rich import box

console = Console(legacy_windows=False)


LOGO = """\
 ██╗   ██╗████████╗
 ██║   ██║╚══██╔══╝
 ██║   ██║   ██║
 ╚██████╔╝   ██║
  ╚═════╝    ╚═╝"""

CATEGORIES = [
    ("Système",   "info  ·  clean  ·  ps list  ·  ps kill"),
    ("Réseau",    "network diag  ·  scanport  ·  speed"),
    ("Fichiers",  "file doublons  ·  heavy  ·  rename  ·  zip"),
    ("",          "     tree  ·  encrypt  ·  decrypt"),
    ("Tri",       "tri <chemin> <motcle>  ·  tri --type <ext>"),
    ("Texte",     "text search  ·  --ext  ·  --ignore-case"),
    ("Données",   "data convert  <csv|json>"),
    ("Dev",       "dev pwd  ·  dev hash  ·  dev hash --compare"),
]

VERSION = "v1.0"
TAGLINE = "Un CLI hybride PowerShell + Python"



def afficher_logo(compact: bool = False) -> None:
    logo_text = Text(LOGO, style="bold cyan")
    header = Text(justify="left")
    header.append("\n")
    header.append("  Useful Tool  ", style="bold white")
    header.append(VERSION, style="dim white")
    header.append("  ·  ", style="dim")
    header.append(TAGLINE, style="dim white")
    header.append("\n")

    if compact:
        console.print()
        console.print(Panel(
            Group(logo_text, header),
            box=box.ROUNDED,
            border_style="cyan",
            padding=(0, 2),
            expand=False,
        ))
        console.print()
        return

    sep = Text("  " + "─" * 44, style="dim cyan")

    cats_text = Text(justify="left")
    cats_text.append("\n")
    for nom, cmds in CATEGORIES:
        if nom:
            cats_text.append(f"  {nom:<10}", style="bold cyan")
        else:
            cats_text.append(f"  {'':10}", style="")
        cats_text.append(f"  {cmds}\n", style="dim white")

    footer = Text(justify="left")
    footer.append("\n  ", style="")
    footer.append("ut help", style="bold cyan")
    footer.append("  pour la liste complète des options\n", style="dim")

    content = Group(logo_text, header, sep, cats_text, footer)

    console.print()
    console.print(Panel(
        content,
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 2),
        expand=False,
    ))
    console.print()


def afficher_banniere() -> None:
    """Bannière compacte à afficher en tête du help."""
    logo_text = Text(LOGO, style="bold cyan")
    header = Text(justify="left")
    header.append("\n  Useful Tool  ", style="bold white")
    header.append(VERSION, style="dim white")
    header.append("  ·  ", style="dim")
    header.append(TAGLINE + "\n", style="dim white")

    console.print()
    console.print(Panel(
        Group(logo_text, header),
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 2),
        expand=False,
    ))
    console.print()

def main():
    parser = argparse.ArgumentParser(prog='style', description="Afficher le logo de Useful Tool.")
    parser.add_argument('--compact', action='store_true', help='Logo seul, sans la liste des commandes')
    parser.add_argument('--banner', action='store_true', help='Bannière courte (pour le help)')
    args = parser.parse_args()

    if args.banner:
        afficher_banniere()
    else:
        afficher_logo(compact=args.compact)


if __name__ == '__main__':
    main()
