import os
import sys
import csv
import json
import argparse

from rich.console import Console
from rich.table import Table
from rich import box

console = Console(highlight=False)

FORMATS_SUPPORTES = {'csv', 'json'}

def _detecter_format(chemin: str) -> str | None:
    ext = os.path.splitext(chemin)[1].lstrip('.').lower()
    return ext if ext in FORMATS_SUPPORTES else None


def _apercu_table(donnees: list[dict], titre: str) -> None:
    if not donnees:
        return
    colonnes = list(donnees[0].keys())
    table = Table(box=box.ROUNDED, header_style="bold", title=titre, title_style="bold cyan")
    for col in colonnes:
        table.add_column(str(col), overflow="fold", max_width=30)
    for row in donnees[:5]:
        table.add_row(*[str(row.get(c, '')) for c in colonnes])
    console.print(table)
    if len(donnees) > 5:
        console.print(f"  [dim]... et {len(donnees) - 5} enregistrement(s) supplémentaire(s)[/dim]")


def _csv_vers_json(chemin_src: str, chemin_dest: str) -> list[dict]:
    with open(chemin_src, encoding='utf-8-sig', newline='') as f:
        donnees = list(csv.DictReader(f))
    with open(chemin_dest, 'w', encoding='utf-8') as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)
    return donnees


def _json_vers_csv(chemin_src: str, chemin_dest: str) -> list[dict]:
    with open(chemin_src, encoding='utf-8') as f:
        contenu = json.load(f)

    if isinstance(contenu, dict):
        donnees = [contenu]
    elif isinstance(contenu, list):
        donnees = contenu
    else:
        console.print("[red]Erreur :[/red] le JSON doit être un objet ou un tableau d'objets.")
        sys.exit(1)

    if not donnees:
        console.print("[yellow]Fichier JSON vide — aucune donnée à convertir.[/yellow]")
        return []

    colonnes: list[str] = list(dict.fromkeys(k for row in donnees for k in row.keys()))

    with open(chemin_dest, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=colonnes, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(donnees)

    return donnees


def convertir(chemin: str, format_cible: str, output: str | None = None) -> None:
    if not os.path.isfile(chemin):
        console.print(f"[red]Erreur :[/red] '{chemin}' n'est pas un fichier valide.")
        sys.exit(1)

    format_cible = format_cible.lower().lstrip('.')
    if format_cible not in FORMATS_SUPPORTES:
        console.print(
            f"[red]Erreur :[/red] format '{format_cible}' non supporté. "
            f"Options : {', '.join(sorted(FORMATS_SUPPORTES))}"
        )
        sys.exit(1)

    format_source = _detecter_format(chemin)
    if not format_source:
        console.print(
            f"[red]Erreur :[/red] extension non reconnue pour '{os.path.basename(chemin)}'. "
            f"Supporté : .csv, .json"
        )
        sys.exit(1)

    if format_source == format_cible:
        console.print(f"[yellow]Le fichier est déjà au format [bold]{format_cible.upper()}[/bold].[/yellow]")
        return

    fichier_sortie = output or f"{os.path.splitext(chemin)[0]}.{format_cible}"

    console.print(
        f"Conversion [cyan]{os.path.basename(chemin)}[/cyan] "
        f"→ [green bold]{format_cible.upper()}[/green bold]..."
    )

    if format_source == 'csv' and format_cible == 'json':
        donnees = _csv_vers_json(chemin, fichier_sortie)
    else:
        donnees = _json_vers_csv(chemin, fichier_sortie)

    if donnees:
        _apercu_table(donnees, titre=f"Aperçu — {os.path.basename(fichier_sortie)}")

    console.print(
        f"\n[green bold]{len(donnees)} enregistrement(s) converti(s)[/green bold] "
        f"→ '[cyan]{fichier_sortie}[/cyan]'"
    )


def main():
    parser = argparse.ArgumentParser(prog='data', description="Conversion et manipulation de données.")
    sub = parser.add_subparsers(dest='commande')

    p_conv = sub.add_parser('convert', help='Convertir un fichier de données (CSV ↔ JSON)')
    p_conv.add_argument('fichier', help='Fichier source (.csv ou .json)')
    p_conv.add_argument('format', help='Format cible : csv ou json')
    p_conv.add_argument('--output', metavar='FICHIER', help='Chemin du fichier de sortie')

    args = parser.parse_args()

    if args.commande == 'convert':
        convertir(args.fichier, args.format, args.output)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
