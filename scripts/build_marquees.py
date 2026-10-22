"""Genera las pasarelas animadas (SVG) del README de perfil.

GitHub no permite CSS ni JS en el README, pero sí SVG animados servidos
desde el repo. Un SVG cargado con <img> no puede pedir recursos externos,
así que cada icono/badge se descarga y se incrusta como data URI.

Uso:  python3 scripts/build_marquees.py
"""
import base64
import math
import re
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
VIEW_W = 820          # ancho visible de la pasarela
SPEED = 38            # px por segundo
NAVY, GOLD = "0A1F44", "C9A227"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-builder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def icon(name):
    svg = fetch(f"https://skillicons.dev/icons?i={name}&theme=dark")
    if len(svg) < 400:
        raise SystemExit(f"skillicons no reconoce el icono '{name}'")
    return svg, 48, 48


def badge(label, logo=None):
    q = {"style": "for-the-badge", "labelColor": NAVY}
    if logo:
        q.update(logo=logo, logoColor=GOLD)
    text = urllib.parse.quote(label.replace("-", "--").replace("_", "__"))
    svg = fetch(f"https://img.shields.io/badge/{text}-{NAVY}?{urllib.parse.urlencode(q)}")
    w = float(re.search(rb'width="([\d.]+)"', svg).group(1))
    return svg, w, 28


def marquee(filename, items, gap, reverse=False):
    h = max(i[2] for i in items)
    set_w = sum(i[1] for i in items) + gap * len(items)
    reps = max(1, math.ceil(VIEW_W / set_w))   # el set debe cubrir todo el ancho
    loop_w = set_w * reps
    imgs, x = [], 0.0
    for _ in range(reps * 2):                  # dos copias -> bucle sin cortes
        for svg, w, ih in items:
            uri = "data:image/svg+xml;base64," + base64.b64encode(svg).decode()
            imgs.append(f'<image x="{x:.1f}" y="{(h - ih) / 2:.1f}" width="{w:.1f}" height="{ih}" href="{uri}"/>')
            x += w + gap
    start, end = (-loop_w, 0) if reverse else (0, -loop_w)
    dur = loop_w / SPEED
    fade = 70
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{VIEW_W}" height="{h + 8}" viewBox="0 0 {VIEW_W} {h + 8}">
<style>
.track {{ animation: slide {dur:.1f}s linear infinite; }}
@keyframes slide {{ from {{ transform: translateX({start:.1f}px); }} to {{ transform: translateX({end:.1f}px); }} }}
@media (prefers-reduced-motion: reduce) {{ .track {{ animation: none; }} }}
</style>
<defs>
<linearGradient id="g" x1="0" x2="1">
<stop offset="0" stop-color="#fff" stop-opacity="0"/>
<stop offset="{fade / VIEW_W:.3f}" stop-color="#fff"/>
<stop offset="{1 - fade / VIEW_W:.3f}" stop-color="#fff"/>
<stop offset="1" stop-color="#fff" stop-opacity="0"/>
</linearGradient>
<mask id="m"><rect width="100%" height="100%" fill="url(#g)"/></mask>
</defs>
<g mask="url(#m)"><g transform="translate(0 4)"><g class="track">
{chr(10).join(imgs)}
</g></g></g>
</svg>
'''
    (OUT / filename).write_text(svg)
    print(f"{filename}: {len(items)} elementos, {reps} repeticiones, {len(svg) // 1024} KB")


def main():
    OUT.mkdir(exist_ok=True)
    marquee("nucleo.svg", [icon(i) for i in ["dotnet", "cs", "azure", "nestjs", "nodejs"]], gap=22)
    marquee("complementario.svg", [icon(i) for i in ["angular", "ts", "postgres", "docker", "nginx", "git"]],
            gap=22, reverse=True)
    marquee("devops.svg", [
        icon("kubernetes"),
        badge("Kubernetes (AKS)", "kubernetes"),
        badge("Podman", "podman"),
        icon("githubactions"),
        badge("Azure DevOps", "azuredevops"),
        badge("GitHub Actions", "githubactions"),
        badge("CI/CD", "githubactions"),
    ], gap=16)
    marquee("ia.svg", [
        badge("Claude Code", "claude"),
        badge("Agentes de IA"),
        badge("MCP", "modelcontextprotocol"),
    ], gap=12, reverse=True)


if __name__ == "__main__":
    main()
