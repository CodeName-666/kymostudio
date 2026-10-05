# Lizenzierung von KymoStudio

Copyright (c) 2026 Christof Seidel

KymoStudio wird **doppelt lizenziert**. Du wählst eine der beiden Lizenzen:

1. **GNU General Public License v3.0** ([LICENSE](LICENSE)): kostenlos.
2. **Kommerzielle Lizenz**: kostenpflichtig, für Unternehmen.

SPDX-Kennung: `GPL-3.0-only OR LicenseRef-KymoStudio-Commercial`

## Welche Lizenz brauche ich?

| Einsatz | Lizenz |
|---|---|
| Hobby, Basteln, Lernen, Schule, Studium, private Projekte | GPLv3, kostenlos |
| Eigenes Open-Source-Projekt unter GPLv3 | GPLv3, kostenlos |
| Geänderte Version von KymoStudio wird **weitergegeben**, ohne den Quellcode unter der GPLv3 offenzulegen | **kommerzielle Lizenz erforderlich** |
| Einbau von KymoStudio oder Teilen davon in ein proprietäres Produkt | **kommerzielle Lizenz erforderlich** |
| Beruflicher, produktiver Einsatz im Unternehmen (Labor, Prüfstand, Entwicklung) | kommerzielle Lizenz erbeten (siehe unten) |

Rein interne Nutzung ohne Weitergabe erlaubt die GPLv3 auch Unternehmen. Wer
KymoStudio beruflich produktiv einsetzt, wird trotzdem gebeten, eine
kommerzielle Lizenz zu erwerben. Sie finanziert die Weiterentwicklung. Auf
Wunsch umfasst sie auch Unterstützung und eine Rechnung für die Buchhaltung.

## Wichtig: Qt-Module

KymoStudio nutzt **Qt Charts** und **Qt Quick 3D**. Diese Qt-Module stehen
ausschließlich unter der **GPLv3** oder einer **kommerziellen Lizenz der Qt
Company**. Eine kommerzielle KymoStudio-Lizenz umfasst den Code von
KymoStudio. Wer KymoStudio in einem proprietären Produkt weitergeben will,
braucht für diese beiden Qt-Module zusätzlich eine kommerzielle Qt-Lizenz.
Ausgenommen ist eine künftige Version, die ohne sie auskommt. Die übrigen
Abhängigkeiten haben andere Lizenzen:

| Abhängigkeit | Lizenz |
|---|---|
| PySide6 (Qt Core, Gui, Qml, Quick, Widgets) | LGPLv3 |
| pyserial | BSD-3-Clause |
| python-can | LGPLv3 |
| paho-mqtt | EPL-2.0 oder EDL-1.0 |

## Kommerzielle Lizenz anfragen

Lege im Repository ein Issue mit dem Titel **„Kommerzielle Lizenz“** an:
<https://github.com/CodeName-666/kymostudio/issues>

Hilfreiche Angaben sind Firma, Einsatzzweck und die Anzahl der Arbeitsplätze.
Bedingungen und Preise werden individuell vereinbart.
