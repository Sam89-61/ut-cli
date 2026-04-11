import os
import sys
import re
import argparse

from rich.console import Console
from rich.text import Text
from rich.rule import Rule

console = Console(highlight=False)

def _est_binaire(chemin: str) -> bool:
    try:
        with open(chemin, 'rb') as f:
            return b'\x00' in f.read(8192)
    except (PermissionError, OSError):
        return True


def _lire_lignes(chemin: str) -> list[str] | None:
    for encoding in ('utf-8', 'utf-8-sig', 'latin-1', 'cp1252'):
        try:
            with open(chemin, encoding=encoding) as f:
                return f.readlines()
        except (UnicodeDecodeError, PermissionError, OSError):
            continue
    return None


def _surligner(ligne: str, pattern: re.Pattern) -> Text:
    """Retourne un objet Text avec le mot-clé surligné en jaune."""
    texte = Text()
    dernier = 0
    for m in pattern.finditer(ligne):
        texte.append(ligne[dernier:m.start()])
        texte.append(ligne[m.start():m.end()], style="black on yellow")
        dernier = m.end()
    texte.append(ligne[dernier:])
    return texte



def rechercher(
    mot_cle: str,
    dossier: str,
    extensions: list[str] | None = None,
    ignore_case: bool = False,
) -> None:
    if not os.path.isdir(dossier):
        console.print(f"[red]Erreur :[/red] '{dossier}' n'est pas un dossier valide.")
        sys.exit(1)

    flags = re.IGNORECASE if ignore_case else 0
    pattern = re.compile(re.escape(mot_cle), flags)
    exts = {e.lstrip('.').lower() for e in extensions} if extensions else None

    total_analyses = 0
    total_correspondances = 0
    fichiers_trouves = 0

    for racine, _, fichiers in os.walk(dossier):
        for nom in sorted(fichiers):
            fp = os.path.join(racine, nom)

            if exts:
                _, ext = os.path.splitext(nom)
                if ext.lstrip('.').lower() not in exts:
                    continue

            if _est_binaire(fp):
                continue

            lignes = _lire_lignes(fp)
            if lignes is None:
                continue

            total_analyses += 1

            correspondances = [
                (i, ligne.rstrip('\n'))
                for i, ligne in enumerate(lignes, start=1)
                if pattern.search(ligne)
            ]

            if not correspondances:
                continue

            fichiers_trouves += 1
            total_correspondances += len(correspondances)

            chemin_relatif = os.path.relpath(fp, dossier)
            console.print(Rule(
                f"[cyan bold]{chemin_relatif}[/cyan bold] "
                f"[dim]({len(correspondances)} ligne(s))[/dim]"
            ))

            for num_ligne, ligne in correspondances:
                console.print(f"  [dim]{num_ligne:5d}[/dim]  ", end="")
                console.print(_surligner(ligne, pattern))

    console.print()
    if total_correspondances == 0:
        console.print(
            f"[yellow]Aucune correspondance pour "
            f"'[bold]{mot_cle}[/bold]' dans {total_analyses} fichier(s) analysé(s).[/yellow]"
        )
    else:
        console.print(
            f"[green bold]{total_correspondances} correspondance(s)[/green bold] "
            f"dans [bold]{fichiers_trouves}[/bold] fichier(s) "
            f"(sur {total_analyses} analysé(s))"
        )


def main():
    parser = argparse.ArgumentParser(prog='text', description="Recherche de texte dans des fichiers.")
    sub = parser.add_subparsers(dest='commande')

    p_search = sub.add_parser('search', help='Chercher un mot-clé dans des fichiers')
    p_search.add_argument('mot_cle', help='Texte à rechercher')
    p_search.add_argument('dossier', help='Dossier à parcourir')
    p_search.add_argument('--ext', metavar='EXT', help='Extensions à inclure, séparées par virgule (ex: py,ps1)')
    p_search.add_argument('-i', '--ignore-case', action='store_true', dest='ignore_case',
                          help='Ignorer la casse')

    args = parser.parse_args()

    if args.commande == 'search':
        extensions = [e.strip() for e in args.ext.split(',')] if args.ext else None
        rechercher(args.mot_cle, args.dossier, extensions, args.ignore_case)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
