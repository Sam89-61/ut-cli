import os
import sys
import re
import hashlib
import zipfile
import getpass
import argparse
import base64
from datetime import datetime, timedelta

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TextColumn
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from rich import box

console = Console(highlight=False)

#Valeur de base
SALT_SIZE = 16
ITERATIONS = 480_000


def _fmt_taille(octets: int) -> str:
    for unit in ['o', 'Ko', 'Mo', 'Go', 'To']:
        if octets < 1024:
            return f"{octets:.1f} {unit}"
        octets /= 1024
    return f"{octets:.1f} Po"


def _parse_taille(s: str) -> int:
    s = s.strip().upper()
    for unit, mult in [('TB', 1024**4), ('GB', 1024**3), ('MB', 1024**2), ('KB', 1024)]:
        if s.endswith(unit):
            return int(s[:-len(unit)]) * mult
    return int(s)


def _parse_age(s: str) -> int:
    s = s.strip().lower()
    if s.endswith('w'):
        return int(s[:-1]) * 7
    if s.endswith('m'):
        return int(s[:-1]) * 30
    if s.endswith('d'):
        return int(s[:-1])
    return int(s)


def _verifier_dossier(chemin: str) -> None:
    if not os.path.isdir(chemin):
        console.print(f"[red]Erreur :[/red] '{chemin}' n'est pas un dossier valide.")
        sys.exit(1)


def _couleur_taille(octets: int) -> str:
    if octets >= 1024 ** 3:
        return "red"
    if octets >= 100 * 1024 ** 2:
        return "yellow"
    return "green"


def _hash_fichier(chemin: str, bloc: int = 65536) -> str:
    h = hashlib.sha256()
    with open(chemin, 'rb') as f:
        chunk = f.read(bloc)
        while chunk:
            h.update(chunk)
            chunk = f.read(bloc)
    return h.hexdigest()


def trouver_doublons(chemin: str, delete: bool = False) -> None:
    _verifier_dossier(chemin)

    tous_fichiers = [
        os.path.join(racine, nom)
        for racine, _, fichiers in os.walk(chemin)
        for nom in fichiers
    ]

    hashes: dict[str, list[str]] = {}
    en_tty = sys.stdout.isatty()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True,
        disable=not en_tty,
    ) as progress:
        task = progress.add_task(f"Analyse de '{chemin}'...", total=len(tous_fichiers))
        for fp in tous_fichiers:
            try:
                h = _hash_fichier(fp)
                hashes.setdefault(h, []).append(fp)
            except (PermissionError, OSError) as e:
                console.print(f"  [yellow]Ignoré :[/yellow] {fp} ({e})")
            progress.advance(task)

    doublons = {h: fps for h, fps in hashes.items() if len(fps) > 1}

    if not doublons:
        console.print("[green]Aucun doublon trouvé.[/green]")
        return

    total_recuperable = sum(
        os.path.getsize(fps[0]) * (len(fps) - 1)
        for fps in doublons.values()
    )
    console.print(Panel(
        f"[bold]{len(doublons)} groupe(s) de doublons[/bold] — "
        f"[green]{_fmt_taille(total_recuperable)} récupérables[/green]",
        expand=False,
    ))

    for h, fps in doublons.items():
        taille = os.path.getsize(fps[0])
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold dim")
        table.add_column("#", style="dim", width=4)
        table.add_column("Chemin", style="cyan")
        table.add_column("Taille", justify="right", style=_couleur_taille(taille))

        for i, fp in enumerate(fps):
            table.add_row(str(i), fp, _fmt_taille(taille))

        console.print(f"\n  [dim]SHA-256: {h[:16]}...[/dim]")
        console.print(table)

        if delete:
            console.print("  Numéros à supprimer (ex: [bold]1,2[/bold]), Entrée pour ignorer :", end=' ')
            choix = input().strip()
            if choix:
                indices = [
                    int(x.strip()) for x in choix.split(',')
                    if x.strip().isdigit() and 0 <= int(x.strip()) < len(fps)
                ]
                if len(indices) >= len(fps):
                    indices = indices[: len(fps) - 1]
                for i in indices:
                    os.remove(fps[i])
                    console.print(f"    [red]Supprimé :[/red] {fps[i]}")


def trouver_gros_fichiers(chemin: str, min_taille: str = '100MB') -> None:
    _verifier_dossier(chemin)

    try:
        seuil = _parse_taille(min_taille)
    except ValueError:
        console.print(f"[red]Erreur :[/red] taille invalide '{min_taille}'. Exemples : 500MB, 1GB, 200KB")
        sys.exit(1)

    console.print(f"Recherche des fichiers >= [bold]{_fmt_taille(seuil)}[/bold] dans '{chemin}'...")

    resultats: list[tuple[int, str, datetime]] = []
    for racine, _, fichiers in os.walk(chemin):
        for nom in fichiers:
            fp = os.path.join(racine, nom)
            try:
                taille = os.path.getsize(fp)
                if taille >= seuil:
                    mtime = datetime.fromtimestamp(os.path.getmtime(fp))
                    resultats.append((taille, fp, mtime))
            except (PermissionError, OSError):
                continue

    if not resultats:
        console.print("[yellow]Aucun fichier trouvé.[/yellow]")
        return

    resultats.sort(reverse=True)

    table = Table(box=box.ROUNDED, header_style="bold", show_lines=False)
    table.add_column("Taille", justify="right", width=12)
    table.add_column("Modifié le", width=17)
    table.add_column("Chemin")

    for taille, fp, mtime in resultats:
        couleur = _couleur_taille(taille)
        table.add_row(
            Text(_fmt_taille(taille), style=couleur),
            mtime.strftime('%Y-%m-%d %H:%M'),
            fp,
        )

    console.print(f"\n[bold]{len(resultats)} fichier(s)[/bold]\n")
    console.print(table)


def renommer_masse(chemin: str, pattern: str, remplacement: str, dry_run: bool = False) -> None:
    _verifier_dossier(chemin)

    try:
        rx = re.compile(pattern)
    except re.error as e:
        console.print(f"[red]Erreur regex :[/red] {e}")
        sys.exit(1)

    fichiers = sorted(f for f in os.listdir(chemin) if os.path.isfile(os.path.join(chemin, f)))
    renommages: list[tuple[str, str]] = []
    conflits: list[tuple[str, str]] = []
    noms_cibles: set[str] = set()

    for nom in fichiers:
        nouveau = rx.sub(remplacement, nom)
        if nouveau == nom:
            continue
        if nouveau in noms_cibles or os.path.exists(os.path.join(chemin, nouveau)):
            conflits.append((nom, nouveau))
        else:
            noms_cibles.add(nouveau)
            renommages.append((nom, nouveau))

    if not renommages and not conflits:
        console.print("[yellow]Aucun fichier ne correspond au pattern.[/yellow]")
        return

    table = Table(box=box.ROUNDED, header_style="bold")
    table.add_column("Avant", style="cyan")
    table.add_column("", width=3, justify="center")
    table.add_column("Après", style="green")
    table.add_column("", width=10)

    for ancien, nouveau in renommages:
        table.add_row(ancien, "→", nouveau, "")
    for ancien, nouveau in conflits:
        table.add_row(ancien, "→", nouveau, "[red bold]CONFLIT[/red bold]")

    console.print(f"\n[bold]{len(renommages)} renommage(s)[/bold] prévu(s)"
                  + (f", [red]{len(conflits)} conflit(s) ignoré(s)[/red]" if conflits else ""))
    console.print(table)

    if not renommages:
        return

    if dry_run:
        console.print("\n[dim]Mode dry-run : aucun fichier modifié.[/dim]")
        return

    console.print("\nAppliquer ces renommages ? ([bold]o[/bold]/n) :", end=' ')
    if input().strip().lower() != 'o':
        console.print("[yellow]Annulé.[/yellow]")
        return

    for ancien, nouveau in renommages:
        os.rename(os.path.join(chemin, ancien), os.path.join(chemin, nouveau))
        console.print(f"  [green]Renommé :[/green] {ancien} → {nouveau}")

    console.print(f"\n[green bold]{len(renommages)} fichier(s) renommé(s).[/green bold]")


def archiver_anciens(chemin: str, age: str = '30d') -> None:
    _verifier_dossier(chemin)

    try:
        jours = _parse_age(age)
    except ValueError:
        console.print(f"[red]Erreur :[/red] âge invalide '{age}'. Exemples : 30d, 2w, 1m")
        sys.exit(1)

    limite = datetime.now() - timedelta(days=jours)
    nom_archive = os.path.join(chemin, f"archive_{datetime.now().strftime('%Y-%m-%d')}.zip")

    console.print(f"Recherche des fichiers non modifiés depuis [bold]{jours} jour(s)[/bold] dans '{chemin}'...")

    candidats: list[tuple[str, str, datetime]] = []
    for nom in sorted(os.listdir(chemin)):
        fp = os.path.join(chemin, nom)
        if not os.path.isfile(fp) or fp == nom_archive:
            continue
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(fp))
            if mtime < limite:
                candidats.append((fp, nom, mtime))
        except (PermissionError, OSError):
            continue

    if not candidats:
        console.print("[yellow]Aucun fichier à archiver.[/yellow]")
        return

    taille_totale = sum(os.path.getsize(fp) for fp, _, _ in candidats)

    table = Table(box=box.ROUNDED, header_style="bold")
    table.add_column("Fichier", style="cyan")
    table.add_column("Modifié le", width=12)
    table.add_column("Taille", justify="right", width=10)

    for fp, nom, mtime in candidats:
        table.add_row(nom, mtime.strftime('%Y-%m-%d'), _fmt_taille(os.path.getsize(fp)))

    console.print(Panel(
        f"[bold]{len(candidats)} fichier(s)[/bold] à archiver "
        f"([yellow]{_fmt_taille(taille_totale)}[/yellow]) "
        f"→ [cyan]{os.path.basename(nom_archive)}[/cyan]",
        expand=False,
    ))
    console.print(table)

    console.print("\nConfirmer l'archivage et la suppression des originaux ? ([bold]o[/bold]/n) :", end=' ')
    if input().strip().lower() != 'o':
        console.print("[yellow]Annulé.[/yellow]")
        return

    en_tty = sys.stdout.isatty()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True,
        disable=not en_tty,
    ) as progress:
        task = progress.add_task("Archivage...", total=len(candidats))
        with zipfile.ZipFile(nom_archive, 'a', zipfile.ZIP_DEFLATED) as zf:
            for fp, nom, _ in candidats:
                zf.write(fp, nom)
                os.remove(fp)
                progress.advance(task)
                if not en_tty:
                    console.print(f"  [green]Archivé :[/green] {nom}")

    console.print(f"\n[green bold]{len(candidats)} fichier(s) archivé(s)[/green bold] → '{nom_archive}'")


def _taille_dossier(chemin: str) -> int:
    total = 0
    for racine, _, fichiers in os.walk(chemin):
        for nom in fichiers:
            try:
                total += os.path.getsize(os.path.join(racine, nom))
            except (PermissionError, OSError):
                pass
    return total


def arborescence(chemin: str, max_depth: int | None = None) -> None:
    _verifier_dossier(chemin)

    nb_fichiers = 0
    nb_dossiers = 0

    def _ajouter(noeud, chemin_courant: str, profondeur: int) -> None:
        nonlocal nb_fichiers, nb_dossiers
        if max_depth is not None and profondeur >= max_depth:
            return
        try:
            entrees = sorted(
                os.listdir(chemin_courant),
                key=lambda e: (not os.path.isdir(os.path.join(chemin_courant, e)), e.lower()),
            )
        except PermissionError:
            noeud.add(Text("Permission refusée", style="dim red"))
            return

        for nom in entrees:
            fp = os.path.join(chemin_courant, nom)
            if os.path.isdir(fp):
                nb_dossiers += 1
                taille = _taille_dossier(fp)
                label = Text()
                label.append(nom + "/", style="bold cyan")
                label.append(f"  {_fmt_taille(taille)}", style="dim")
                branche = noeud.add(label)
                _ajouter(branche, fp, profondeur + 1)
            else:
                nb_fichiers += 1
                try:
                    taille = os.path.getsize(fp)
                    label = Text()
                    label.append(nom)
                    label.append(f"  {_fmt_taille(taille)}", style="dim green")
                    noeud.add(label)
                except (PermissionError, OSError):
                    noeud.add(Text(f"{nom}  [permission refusée]", style="dim red"))

    taille_totale = _taille_dossier(chemin)
    nom_racine = os.path.basename(os.path.abspath(chemin)) or chemin
    label_racine = Text()
    label_racine.append(nom_racine + "/", style="bold yellow")
    label_racine.append(f"  {_fmt_taille(taille_totale)}", style="dim")

    tree = Tree(label_racine)
    _ajouter(tree, chemin, 0)
    console.print(tree)
    console.print(
        f"\n[dim]{nb_dossiers} dossier(s), {nb_fichiers} fichier(s), "
        f"[bold]{_fmt_taille(taille_totale)}[/bold] au total[/dim]"
    )



def _derive_key(password: str, salt: bytes) -> bytes:
    try:
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes as _hashes
    except ImportError:
        console.print(
            "[red]Erreur :[/red] bibliothèque 'cryptography' non installée. "
            "Lancez : [bold]pip install cryptography[/bold]"
        )
        sys.exit(1)

    kdf = PBKDF2HMAC(
        algorithm=_hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))


def chiffrer(chemin: str, password: str | None = None) -> None:
    if not os.path.isfile(chemin):
        console.print(f"[red]Erreur :[/red] '{chemin}' n'est pas un fichier valide.")
        sys.exit(1)

    if chemin.endswith('.enc'):
        console.print("[yellow]Ce fichier est déjà chiffré (.enc).[/yellow]")
        return

    if password is None:
        password = getpass.getpass("Mot de passe : ")
        confirm = getpass.getpass("Confirmer    : ")
        if password != confirm:
            console.print("[red]Erreur :[/red] les mots de passe ne correspondent pas.")
            sys.exit(1)

    from cryptography.fernet import Fernet

    salt = os.urandom(SALT_SIZE)
    key = _derive_key(password, salt)
    f = Fernet(key)

    with open(chemin, 'rb') as fin:
        data = fin.read()

    encrypted = f.encrypt(data)
    chemin_sortie = chemin + '.enc'

    with open(chemin_sortie, 'wb') as fout:
        fout.write(salt + encrypted)

    console.print(
        f"[green bold]Chiffré[/green bold] : '[cyan]{os.path.basename(chemin)}[/cyan]' "
        f"→ '[cyan]{os.path.basename(chemin_sortie)}[/cyan]' "
        f"({_fmt_taille(len(data))} → {_fmt_taille(os.path.getsize(chemin_sortie))})"
    )
    console.print("[dim]Le fichier original est conservé.[/dim]")


def dechiffrer(chemin: str, password: str | None = None) -> None:
    if not os.path.isfile(chemin):
        console.print(f"[red]Erreur :[/red] '{chemin}' n'est pas un fichier valide.")
        sys.exit(1)

    if not chemin.endswith('.enc'):
        console.print("[yellow]Attention :[/yellow] le fichier n'a pas l'extension .enc")

    if password is None:
        password = getpass.getpass("Mot de passe : ")

    from cryptography.fernet import Fernet, InvalidToken

    with open(chemin, 'rb') as fin:
        contenu = fin.read()

    if len(contenu) <= SALT_SIZE:
        console.print("[red]Erreur :[/red] fichier trop court ou corrompu.")
        sys.exit(1)

    salt = contenu[:SALT_SIZE]
    encrypted = contenu[SALT_SIZE:]
    key = _derive_key(password, salt)
    f = Fernet(key)

    try:
        data = f.decrypt(encrypted)
    except InvalidToken:
        console.print("[red bold]Erreur :[/red bold] mot de passe incorrect ou fichier corrompu.")
        sys.exit(1)

    chemin_sortie = chemin[:-4] if chemin.endswith('.enc') else chemin + '.dec'

    if os.path.exists(chemin_sortie):
        console.print(f"[yellow]'{os.path.basename(chemin_sortie)}' existe déjà. Écraser ? ([bold]o[/bold]/n) :[/yellow] ", end='')
        if input().strip().lower() != 'o':
            console.print("Annulé.")
            return

    with open(chemin_sortie, 'wb') as fout:
        fout.write(data)

    console.print(
        f"[green bold]Déchiffré[/green bold] : '[cyan]{os.path.basename(chemin)}[/cyan]' "
        f"→ '[cyan]{os.path.basename(chemin_sortie)}[/cyan]'"
    )


def main():
    parser = argparse.ArgumentParser(prog='file', description="Gestion avancée de fichiers.")
    sub = parser.add_subparsers(dest='commande')

    p_dup = sub.add_parser('doublons', help='Trouver les fichiers en double')
    p_dup.add_argument('chemin', help='Dossier à analyser')
    p_dup.add_argument('--delete', action='store_true', help='Mode interactif de suppression')

    p_hvy = sub.add_parser('heavy', help='Trouver les gros fichiers')
    p_hvy.add_argument('chemin', help='Dossier à analyser')
    p_hvy.add_argument('--min', default='100MB', dest='min_taille', help='Taille minimale (ex: 500MB, 1GB)')

    p_ren = sub.add_parser('rename', help='Renommage en masse par regex')
    p_ren.add_argument('chemin', help='Dossier cible')
    p_ren.add_argument('regex', help='Expression régulière à chercher')
    p_ren.add_argument('remplacement', help='Chaîne de remplacement')
    p_ren.add_argument('--dry-run', action='store_true', dest='dry_run', help='Afficher sans appliquer')

    p_zip = sub.add_parser('zip', help='Archiver les anciens fichiers')
    p_zip.add_argument('chemin', help='Dossier à archiver')
    p_zip.add_argument('--age', default='30d', help='Âge minimum (ex: 30d, 2w, 1m)')

    p_tree = sub.add_parser('tree', help="Arborescence visuelle d'un dossier avec tailles")
    p_tree.add_argument('chemin', help='Dossier à afficher')
    p_tree.add_argument('--depth', type=int, default=None, dest='max_depth',
                        help='Profondeur maximale (ex: --depth 3)')

    p_enc = sub.add_parser('encrypt', help='Chiffrer un fichier (Fernet/AES + PBKDF2)')
    p_enc.add_argument('chemin', help='Fichier à chiffrer')

    p_dec = sub.add_parser('decrypt', help='Déchiffrer un fichier .enc')
    p_dec.add_argument('chemin', help='Fichier .enc à déchiffrer')

    args = parser.parse_args()

    if args.commande == 'doublons':
        trouver_doublons(args.chemin, args.delete)
    elif args.commande == 'heavy':
        trouver_gros_fichiers(args.chemin, args.min_taille)
    elif args.commande == 'rename':
        renommer_masse(args.chemin, args.regex, args.remplacement, args.dry_run)
    elif args.commande == 'zip':
        archiver_anciens(args.chemin, args.age)
    elif args.commande == 'tree':
        arborescence(args.chemin, args.max_depth)
    elif args.commande == 'encrypt':
        chiffrer(args.chemin)
    elif args.commande == 'decrypt':
        dechiffrer(args.chemin)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
