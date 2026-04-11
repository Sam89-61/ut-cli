import os
import sys
import shutil
import argparse

from rich.console import Console
from rich.table import Table
from rich import box

console = Console(highlight=False)


def resoudre_conflit(fichier_source: str, dossier_dest: str) -> str:
    """Retourne un nom sans conflit dans dossier_dest. Ex: plan.pdf -> plan_2.pdf"""
    nom = os.path.basename(fichier_source)
    base, ext = os.path.splitext(nom)
    compteur = 2
    nouveau_nom = nom
    while os.path.exists(os.path.join(dossier_dest, nouveau_nom)):
        nouveau_nom = f"{base}_{compteur}{ext}"
        compteur += 1
    return nouveau_nom


def _deplacer(fichier_source: str, dossier_dest: str, interactif: bool) -> None:
    os.makedirs(dossier_dest, exist_ok=True)
    nom = os.path.basename(fichier_source)
    dest = os.path.join(dossier_dest, nom)

    if os.path.exists(dest):
        if interactif:
            console.print(f"[yellow]Conflit :[/yellow] '{nom}' existe déjà dans '{dossier_dest}'.")
            choix = input("Renommer automatiquement ? (o/n) : ").strip().lower()
            if choix != 'o':
                console.print(f"  [dim]Ignoré : '{nom}'[/dim]")
                return
        nouveau_nom = resoudre_conflit(fichier_source, dossier_dest)
        dest = os.path.join(dossier_dest, nouveau_nom)
        console.print(f"  [yellow]Renommé :[/yellow]  '{nom}' → '{nouveau_nom}'")

    shutil.move(fichier_source, dest)
    console.print(f"  [green]Déplacé :[/green]  '{nom}' → '{dossier_dest}'")


def tri_par_motcle(chemin: str, motcle: str, interactif: bool = True) -> None:
    """Déplace tous les fichiers/dossiers contenant motcle vers un sous-dossier du même nom."""
    if not os.path.isdir(chemin):
        console.print(f"[red]Erreur :[/red] '{chemin}' n'est pas un dossier valide.")
        sys.exit(1)

    dossier_dest = os.path.join(chemin, motcle)
    entrees = [
        e for e in os.listdir(chemin)
        if motcle.lower() in e.lower() and os.path.join(chemin, e) != dossier_dest
    ]

    if not entrees:
        console.print(f"[yellow]Aucun fichier contenant '{motcle}' trouvé dans '{chemin}'.[/yellow]")
        return

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("Fichier", style="cyan")
    for e in entrees:
        table.add_row(e)

    console.print(f"\n[bold]{len(entrees)} élément(s)[/bold] contenant '[cyan]{motcle}[/cyan]' :")
    console.print(table)

    for nom in entrees:
        _deplacer(os.path.join(chemin, nom), dossier_dest, interactif)

    console.print(f"\n[green bold]Tri terminé[/green bold] → '{dossier_dest}'")


def tri_par_type(chemin: str, extension: str, interactif: bool = True) -> None:
    """Déplace tous les fichiers d'une extension donnée vers un sous-dossier nommé d'après l'extension."""
    if not os.path.isdir(chemin):
        console.print(f"[red]Erreur :[/red] '{chemin}' n'est pas un dossier valide.")
        sys.exit(1)

    ext = extension.lstrip('.').lower()
    dossier_dest = os.path.join(chemin, ext)
    fichiers = [
        e for e in os.listdir(chemin)
        if os.path.isfile(os.path.join(chemin, e)) and e.lower().endswith(f".{ext}")
    ]

    if not fichiers:
        console.print(f"[yellow]Aucun fichier .{ext} trouvé dans '{chemin}'.[/yellow]")
        return

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("Fichier", style="cyan")
    for f in fichiers:
        table.add_row(f)

    console.print(f"\n[bold]{len(fichiers)} fichier(s)[/bold] [cyan].{ext}[/cyan] :")
    console.print(table)

    for nom in fichiers:
        _deplacer(os.path.join(chemin, nom), dossier_dest, interactif)

    console.print(f"\n[green bold]Tri terminé[/green bold] → '{dossier_dest}'")


def main():
    parser = argparse.ArgumentParser(
        prog='tri',
        description="Trier des fichiers par mot-clé ou par type."
    )
    parser.add_argument('chemin', help='Dossier à trier')
    parser.add_argument('motcle', nargs='?', help='Mot-clé dans les noms de fichiers')
    parser.add_argument('--type', dest='file_type', help='Extension à trier (ex: pdf, jpg)')

    args = parser.parse_args()

    if args.file_type:
        tri_par_type(args.chemin, args.file_type)
    elif args.motcle:
        tri_par_motcle(args.chemin, args.motcle)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
