#!/usr/bin/env python3
"""Scenes set in a place.

The cast used to stand against a gradient while props appeared overhead like
thought bubbles. These are rooms: a back wall, furniture that means something
for the line being spoken, and a floor in perspective that the characters
stand on.
"""
from config import W, H

ACCENT = "#ffc14d"


def floor_grid(y):
    """Receding floor lines - the cheapest way to say "standing in a place"."""
    out = [f'<rect x="0" y="{y}" width="{W}" height="{H - y}" fill="#2c3d50"/>']
    for k in range(1, 8):
        yy = y + (H - y) * (k / 7) ** 1.7
        out.append(f'<line x1="0" y1="{yy:.0f}" x2="{W}" y2="{yy:.0f}" '
                   f'stroke="#22303f" stroke-width="3" opacity=".45"/>')
    for k in range(-3, 4):
        out.append(f'<line x1="{540 + k * 96}" y1="{y}" x2="{540 + k * 430}" y2="{H}" '
                   f'stroke="#22303f" stroke-width="3" opacity=".45"/>')
    return "".join(out)


def window_tall(x, y, w, h, op=1.0):
    return (f'<g opacity="{op}"><rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="url(#warm)" stroke="#16202b" stroke-width="10"/>'
            f'<line x1="{x + w / 2}" y1="{y}" x2="{x + w / 2}" y2="{y + h}" '
            f'stroke="#16202b" stroke-width="10"/>'
            f'<line x1="{x}" y1="{y + h * .42}" x2="{x + w}" y2="{y + h * .42}" '
            f'stroke="#16202b" stroke-width="10"/></g>')


def mansion(fy):
    return (f'<rect width="{W}" height="{H}" fill="#35485e"/>'
            + window_tall(70, 300, 300, 548) + window_tall(710, 300, 300, 548)
            + '<rect x="430" y="250" width="220" height="598" fill="#3d5068" '
              'stroke="#1d2a38" stroke-width="8"/>'
            + '<g fill="#e0b24a" stroke="#1d2a38" stroke-width="6">'
              '<rect x="436" y="300" width="208" height="26" rx="8"/>'
              '<rect x="436" y="786" width="208" height="26" rx="8"/>'
              '<rect x="470" y="326" width="18" height="460"/>'
              '<rect x="532" y="326" width="18" height="460"/>'
              '<rect x="594" y="326" width="18" height="460"/></g>'
            + '<g transform="translate(540 140)">'
              '<path d="M0 0 v92" stroke="#1d2a38" stroke-width="8"/>'
              '<path d="M-132 92 h264 l-46 72 h-172 z" fill="#f0c860" '
              'stroke="#1d2a38" stroke-width="8"/>'
              '<ellipse cx="0" cy="196" rx="156" ry="38" fill="#ffd27a" opacity=".22"/></g>'
            + floor_grid(fy))


def office(fy):
    cab = "".join(f'<rect x="{x}" y="{y}" width="198" height="92" fill="#404b57"/>'
                  for x in (86, 796) for y in (412, 524, 636))
    return (f'<rect width="{W}" height="{H}" fill="#3a4654"/>'
            + '<g stroke="#1d2a38" stroke-width="8">'
              '<rect x="60" y="380" width="250" height="468" fill="#56636f"/>'
              '<rect x="770" y="380" width="250" height="468" fill="#56636f"/>'
            + cab + '</g>'
            + '<g transform="translate(540 296)"><circle r="86" fill="#eee6d4" '
              'stroke="#1d2a38" stroke-width="8"/>'
              '<path d="M0 0 v-56 M0 0 l40 26" stroke="#1d2a38" stroke-width="9" '
              'stroke-linecap="round"/></g>'
            + floor_grid(fy))


def empty(fy):
    return (f'<rect width="{W}" height="{H}" fill="#33404f"/>'
            + window_tall(70, 300, 300, 548, .45) + window_tall(710, 300, 300, 548, .45)
            + '<g transform="translate(540 160)">'
              '<path d="M0 0 v152" stroke="#1d2a38" stroke-width="7"/>'
              '<circle cy="182" r="38" fill="#ffd98a" stroke="#1d2a38" stroke-width="7"/>'
              '<ellipse cy="256" rx="196" ry="62" fill="#ffd27a" opacity=".18"/></g>'
            + '<g fill="#6b5a44" stroke="#1d2a38" stroke-width="7">'
              f'<rect x="120" y="{fy-100}" width="150" height="100"/>'
              f'<rect x="150" y="{fy-158}" width="110" height="58"/>'
              f'<rect x="846" y="{fy-92}" width="140" height="92"/></g>'
            + floor_grid(fy))


def stage_empty(fy):
    return (f'<rect width="{W}" height="{H}" fill="#2f3f52"/>'
            + '<ellipse cx="540" cy="700" rx="520" ry="430" fill="url(#spill)" opacity=".5"/>'
            + floor_grid(fy))


ROOMS = dict(mansion=mansion, office=office, empty=empty, stage=stage_empty)


def note_plate(text, y):
    fs = 56
    while fs > 30 and len(text) * fs * .62 + 96 > 900:
        fs -= 2
    half = (len(text) * fs * .62) / 2 + 48
    return (f'<g transform="translate(540 {y:.0f})"><g class="note" opacity="0">'
            f'<rect x="{-half:.0f}" y="-56" width="{2 * half:.0f}" height="112" rx="18" '
            f'fill="#13202a" opacity=".92"/>'
            f'<rect x="{-half:.0f}" y="-56" width="{2 * half:.0f}" height="112" rx="18" '
            f'fill="none" stroke="{ACCENT}" stroke-width="3"/>'
            f'<text x="0" y="19" text-anchor="middle" font-family="Archivo Black" '
            f'font-size="{fs}" fill="{ACCENT}">{text}</text></g></g>')
