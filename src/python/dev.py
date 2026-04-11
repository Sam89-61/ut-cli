import os
import sys
import hashlib
import secrets
import string
import subprocess
import argparse

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console(highlight=False)


def _fmt_taille(octets: int) -> str:
    for unit in ['o', 'Ko', 'Mo', 'Go']:
        if octets < 1024:
            return f"{octets:.1f} {unit}"
        octets /= 1024
    return f"{octets:.1f} To"


def _copier_presse_papiers(texte: str) -> bool:
    """Copie dans le presse-papiers via PowerShell (stdin, sans exposer le texte en arg)."""
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', '$input | Set-Clipboard'],
            input=texte,
            text=True,
            capture_output=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _evaluer_force(pwd: str) -> str:
    score = sum([
        any(c.isupper() for c in pwd),
        any(c.islower() for c in pwd),
        any(c.isdigit() for c in pwd),
        any(c in string.punctuation for c in pwd),
        len(pwd) >= 16,
        len(pwd) >= 24,
    ])
    if score <= 2:
        return "[red]Faible[/red]"
    if score <= 3:
        return "[yellow]Moyen[/yellow]"
    if score <= 4:
        return "[yellow]Bon[/yellow]"
    return "[green bold]Excellent[/green bold]"


def generer_mot_de_passe(longueur: int = 16, no_special: bool = False, copy: bool = False) -> str:
    if longueur < 4:
        console.print("[red]Erreur :[/red] longueur minimale : 4 caractères.")
        sys.exit(1)

    alphabet = string.ascii_letters + string.digits
    if not no_special:
        alphabet += string.punctuation

    # Garantir au moins un caractère de chaque catégorie activée
    guaranteed = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]
    if not no_special:
        guaranteed.append(secrets.choice(string.punctuation))

    reste = [secrets.choice(alphabet) for _ in range(longueur - len(guaranteed))]
    chars = guaranteed + reste
    secrets.SystemRandom().shuffle(chars)
    pwd = ''.join(chars)

    console.print(Panel(
        f"[bold green]{pwd}[/bold green]",
        title="[bold]Mot de passe généré[/bold]",
        expand=False,
    ))
    console.print(f"Force : {_evaluer_force(pwd)}  |  Longueur : [bold]{longueur}[/bold] caractères")

    if copy:
        if _copier_presse_papiers(pwd):
            console.print("[green]Copié dans le presse-papiers.[/green]")
        else:
            console.print("[yellow]Impossible de copier (PowerShell introuvable).[/yellow]")

    return pwd


def calculer_hash(chemin: str, compare: str = None) -> None:
    if not os.path.isfile(chemin):
        console.print(f"[red]Erreur :[/red] '{chemin}' n'est pas un fichier valide.")
        sys.exit(1)

    taille = os.path.getsize(chemin)
    console.print(
        f"Calcul des hashs de '[cyan]{os.path.basename(chemin)}[/cyan]' "
        f"({_fmt_taille(taille)})..."
    )

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()

    with open(chemin, 'rb') as f:
        for bloc in iter(lambda: f.read(65536), b''):
            md5.update(bloc)
            sha1.update(bloc)
            sha256.update(bloc)

    resultats = [
        ("MD5",    md5.hexdigest()),
        ("SHA-1",  sha1.hexdigest()),
        ("SHA-256", sha256.hexdigest()),
    ]

    compare_lower = compare.lower().strip() if compare else None

    table = Table(box=box.ROUNDED, header_style="bold")
    table.add_column("Algorithme", width=10)
    table.add_column("Hash", style="cyan", no_wrap=True)
    if compare_lower:
        table.add_column("", width=3, justify="center")

    correspondance = False
    for algo, h in resultats:
        match = compare_lower and h == compare_lower
        if match:
            correspondance = True
        if compare_lower:
            statut = Text("✓", style="green bold") if match else Text("✗", style="dim red")
            table.add_row(algo, Text(h, style="bold green" if match else "cyan"), statut)
        else:
            table.add_row(algo, h)

    console.print(table)

    if compare_lower:
        if correspondance:
            console.print("[green bold]Fichier intègre — hash vérifié.[/green bold]")
        else:
            console.print(f"[red bold]Échec — '{compare}' ne correspond à aucun hash.[/red bold]")


def main():
    parser = argparse.ArgumentParser(prog='dev', description="Outils pour développeurs.")
    sub = parser.add_subparsers(dest='commande')

    p_pwd = sub.add_parser('pwd', help='Générer un mot de passe sécurisé')
    p_pwd.add_argument('--length', type=int, default=16, dest='longueur',
                       help='Longueur du mot de passe (défaut : 16)')
    p_pwd.add_argument('--no-special', action='store_true', dest='no_special',
                       help='Exclure les caractères spéciaux')
    p_pwd.add_argument('--copy', action='store_true',
                       help='Copier dans le presse-papiers')

    p_hash = sub.add_parser('hash', help="Calculer les hashs d'un fichier")
    p_hash.add_argument('chemin', help='Fichier à analyser')
    p_hash.add_argument('--compare', metavar='HASH',
                        help='Hash de référence à vérifier (MD5/SHA-1/SHA-256)')

    args = parser.parse_args()

    if args.commande == 'pwd':
        generer_mot_de_passe(args.longueur, args.no_special, args.copy)
    elif args.commande == 'hash':
        calculer_hash(args.chemin, args.compare)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
