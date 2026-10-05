# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Erzeugt das Kymotrace-Logo-Set (Signal-Ring): SVGs, Favicon, Windows-Icon, Übersicht.

Aufruf: .venv/Scripts/python.exe tools/build_brand.py
Benötigt Plus Jakarta Sans (Google Fonts, OFL) als installierte Schrift.
"""
import math
import os
import struct
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QRectF
from PySide6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QImage, QPainter, QPainterPath
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "docs/brand"
ICONS = ROOT / "resources/icons"
ICONS.mkdir(parents=True, exist_ok=True)
app = QGuiApplication([])
FAMILY = QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\PlusJakartaSans-VariableFont_wght.ttf")))[0]

C = dict(ground="#15123A", track="#2E2A66", hub="#E9E6FF", wave="#A78BFA", tip="#FDE047",
         ink="#15123A", paper="#E9E6FF", claim_light="#6D5BD0", claim_dark="#A78BFA")


def ring_path(radius, amplitude, cycles, calm=0.35, ramp=0.15, n=400):
    start, end = math.radians(-60), math.radians(260)
    pts = []
    for i in range(n + 1):
        u = i / n
        env = 0 if u < calm else min(1.0, (u - calm) / ramp)
        r = radius + amplitude * env * math.sin(2 * math.pi * cycles * (u - calm))
        t = start + (end - start) * u
        pts.append((32 + r * math.cos(t), 32 + r * math.sin(t)))
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts), pts[-1]


def mark_svg(simple=False, standalone=True):
    if simple:  # favicon: dicker, wenige große Wellen
        d, (ex, ey) = ring_path(19, 5.5, 3.5, calm=0.3, ramp=0.1, n=200)
        body = (f'<circle cx="32" cy="32" r="32" fill="{C["ground"]}"/>'
                f'<circle cx="32" cy="32" r="6" fill="{C["hub"]}"/>'
                f'<path d="{d}" fill="none" stroke="{C["wave"]}" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<circle cx="{ex:.2f}" cy="{ey:.2f}" r="6" fill="{C["tip"]}"/>')
    else:
        d, (ex, ey) = ring_path(19.5, 3.3, 11)
        body = (f'<circle cx="32" cy="32" r="31" fill="{C["ground"]}"/>'
                f'<circle cx="32" cy="32" r="19.5" fill="none" stroke="{C["track"]}" stroke-width="1.2"/>'
                f'<circle cx="32" cy="32" r="4" fill="{C["hub"]}"/>'
                f'<path d="{d}" fill="none" stroke="{C["wave"]}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<circle cx="{ex:.2f}" cy="{ey:.2f}" r="3.6" fill="{C["tip"]}"/>')
    if not standalone:
        return body
    title = "Kymotrace" + (" (Favicon)" if simple else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" role="img">'
            f'<title>{title}</title>{body}</svg>\n')


def text_path(text, size, weight, spacing, x, y):
    font = QFont(FAMILY)
    font.setPixelSize(size)
    font.setWeight(weight)
    font.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
    path = QPainterPath()
    path.addText(x, y, font, text)
    parts, i = [], 0
    while i < path.elementCount():
        e = path.elementAt(i)
        if e.type == QPainterPath.ElementType.MoveToElement:
            parts.append(f"M{e.x:.2f} {e.y:.2f}")
        elif e.type == QPainterPath.ElementType.LineToElement:
            parts.append(f"L{e.x:.2f} {e.y:.2f}")
        elif e.type == QPainterPath.ElementType.CurveToElement:
            c2, p = path.elementAt(i + 1), path.elementAt(i + 2)
            parts.append(f"C{e.x:.2f} {e.y:.2f} {c2.x:.2f} {c2.y:.2f} {p.x:.2f} {p.y:.2f}")
            i += 2
        i += 1
    return "".join(parts), path.boundingRect()


def lockup(theme):
    word, wb = text_path("KYMOTRACE", 27, QFont.Light, 7, 82, 37)
    claim, cb = text_path("EMBEDDED TELEMETRY", 8.6, QFont.DemiBold, 3.4, 83, 53)
    width = math.ceil(max(wb.right(), cb.right()) + 4)
    fg = C["ink"] if theme == "light" else C["paper"]
    sub = C["claim_light"] if theme == "light" else C["claim_dark"]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 64" width="{width}" height="64" role="img">'
            f'<title>Kymotrace – Embedded Telemetry</title>{mark_svg(standalone=False)}'
            f'<path d="{word}" fill="{fg}"/><path d="{claim}" fill="{sub}"/></svg>\n')


def render(svg_text, size):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(QByteArray(svg_text.encode())).render(p, QRectF(0, 0, size, size))
    p.end()
    return img


def png_bytes(img):
    data = QByteArray()
    buf = QBuffer(data)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    return bytes(data)


def write_ico(path, images):
    entries = [png_bytes(img) for img in images]
    header = struct.pack("<HHH", 0, 1, len(entries))
    offset = 6 + 16 * len(entries)
    directory = b""
    for img, data in zip(images, entries):
        s = img.width()
        directory += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    path.write_bytes(header + directory + b"".join(entries))


mark, fav = mark_svg(), mark_svg(simple=True)
(BRAND / "kymotrace-mark.svg").write_text(mark, encoding="utf-8")
(BRAND / "kymotrace-favicon.svg").write_text(fav, encoding="utf-8")
(BRAND / "kymotrace-logo-light.svg").write_text(lockup("light"), encoding="utf-8")
(BRAND / "kymotrace-logo-dark.svg").write_text(lockup("dark"), encoding="utf-8")
(ICONS / "kymotrace.svg").write_text(mark, encoding="utf-8")
sizes = [16, 24, 32, 48, 64, 128, 256]
write_ico(ICONS / "kymotrace.ico", [render(fav if s <= 32 else mark, s) for s in sizes])
render(mark, 512).save(str(BRAND / "kymotrace-mark-512.png"))

# Übersicht
W, H = 1000, 520
sheet = QImage(W, H, QImage.Format_ARGB32)
sheet.fill(QColor("#F4F6F9"))
p = QPainter(sheet)
p.setRenderHint(QPainter.Antialiasing)
p.fillRect(0, 260, W, 260, QColor("#0D0B26"))
for y0, theme in ((0, "light"), (260, "dark")):
    svg = lockup(theme)
    r = QSvgRenderer(QByteArray(svg.encode()))
    vb = r.viewBoxF()
    r.render(p, QRectF(40, y0 + 40, vb.width() * 1.6, vb.height() * 1.6))
    x = 40
    for s in (128, 64, 32, 16):
        QSvgRenderer(QByteArray((fav if s <= 32 else mark).encode())).render(p, QRectF(x, y0 + 160 - (s - 16) / 2 + 20, s, s) if s < 128 else QRectF(W - 180, y0 + 50, s, s))
        if s < 128:
            x += s + 30
p.end()
sheet.save(str(BRAND / "kymotrace-uebersicht.png"))
print("fertig:", FAMILY)
