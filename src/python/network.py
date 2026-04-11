import sys
import time
import argparse
import urllib.request
import urllib.error

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box

console = Console(highlight=False)

# URL Cloudflare utilisée pour le mode fallback (pas de dépendance externe)
_CF_DOWN_URL = "https://speed.cloudflare.com/__down?bytes=25000000"   # 25 Mo
_CF_PING_URL = "https://cloudflare.com"


# ── helpers ───────────────────────────────────────────────────────────────────

def _barre(mbps: float, ref: float) -> str:
    pct = min(mbps / ref, 1.0) if ref > 0 else 0
    blocs = int(pct * 18)
    if mbps >= 100:
        couleur = "green"
    elif mbps >= 20:
        couleur = "yellow"
    else:
        couleur = "red"
    return f"[{couleur}]{'█' * blocs}[/{couleur}][dim]{'░' * (18 - blocs)}[/dim]"


def _afficher_table(
    ping_ms: float | None,
    download_mbps: float | None,
    upload_mbps: float | None,
    source: str,
) -> None:
    table = Table(box=box.ROUNDED, header_style="bold")
    table.add_column("Mesure", width=12)
    table.add_column("Résultat", justify="right", width=16)
    table.add_column("", width=20)

    ref = max(filter(None, [download_mbps, upload_mbps, 1]), default=1)

    if ping_ms is not None:
        table.add_row("Ping", f"{ping_ms:.0f} ms", "")

    if download_mbps is not None:
        table.add_row(
            "Download",
            Text(f"{download_mbps:.1f} Mb/s", style="green bold"),
            _barre(download_mbps, ref),
        )
    if upload_mbps is not None:
        table.add_row(
            "Upload",
            Text(f"{upload_mbps:.1f} Mb/s", style="cyan bold"),
            _barre(upload_mbps, ref),
        )
    else:
        table.add_row("Upload", Text("N/A", style="dim"), "")

    console.print(table)
    console.print(f"[dim]Source : {source}[/dim]")


# ── mode speedtest-cli ────────────────────────────────────────────────────────

def _tester_speedtest_cli() -> bool:
    """Tente un test via speedtest-cli. Retourne True si réussi."""
    try:
        import speedtest as _st
    except ImportError:
        return False

    try:
        with console.status("Sélection du meilleur serveur..."):
            try:
                st = _st.Speedtest(secure=True)
            except Exception:
                st = _st.Speedtest(secure=False)
            serveur = st.get_best_server()

        console.print(
            f"Serveur : [cyan]{serveur['name']}[/cyan], "
            f"{serveur['country']} "
            f"[dim]({serveur['sponsor']})[/dim]\n"
        )

        with console.status("[bold]Test de téléchargement (Download)...[/bold]"):
            download_mbps = st.download() / 1_000_000

        with console.status("[bold]Test d'envoi (Upload)...[/bold]"):
            upload_mbps = st.upload() / 1_000_000

        ping_ms = st.results.ping

        _afficher_table(ping_ms, download_mbps, upload_mbps, "Speedtest.net")
        return True

    except Exception as e:
        console.print(f"[yellow]speedtest-cli indisponible :[/yellow] {e}")
        return False


# ── mode fallback HTTP (Cloudflare) ───────────────────────────────────────────

def _tester_http_fallback() -> None:
    """Test de téléchargement via Cloudflare (urllib, aucune dépendance externe)."""
    console.print("[dim]Mode fallback : test via Cloudflare CDN[/dim]\n")

    # Ping
    ping_ms = None
    with console.status("Mesure du ping (Cloudflare)..."):
        try:
            t0 = time.perf_counter()
            urllib.request.urlopen(_CF_PING_URL, timeout=5)
            ping_ms = (time.perf_counter() - t0) * 1000
        except Exception:
            pass

    # Download
    download_mbps = None
    with console.status("Test de téléchargement (25 Mo via Cloudflare)..."):
        try:
            t0 = time.perf_counter()
            total = 0
            with urllib.request.urlopen(_CF_DOWN_URL, timeout=60) as resp:
                while chunk := resp.read(65536):
                    total += len(chunk)
            elapsed = time.perf_counter() - t0
            if elapsed > 0:
                download_mbps = (total * 8) / elapsed / 1_000_000
        except urllib.error.URLError as e:
            console.print(f"[red]Erreur réseau :[/red] {e.reason}")
            console.print("[dim]Vérifiez votre connexion internet.[/dim]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Erreur :[/red] {e}")
            sys.exit(1)

    _afficher_table(ping_ms, download_mbps, None, "Cloudflare CDN (HTTP fallback)")


# ── speed ─────────────────────────────────────────────────────────────────────

def tester_debit() -> None:
    console.print("Test de débit en cours...\n")

    if not _tester_speedtest_cli():
        console.print()
        _tester_http_fallback()


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog='network', description="Outils réseau.")
    sub = parser.add_subparsers(dest='commande')
    sub.add_parser('speed', help='Tester le débit internet (Download / Upload)')

    args = parser.parse_args()

    if args.commande == 'speed':
        tester_debit()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
