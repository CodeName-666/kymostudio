# KymoStudio – Handbuch

[← Zurück zur Übersicht](../README.md)

Installation, Bedienung, Grenzen, Konfiguration und Prüfungen im Detail.

## Start unter Windows

Empfohlen ist eine separate Installation mit **Python 3.12**. Das Projekt nicht
blind in die bisherige Installation kopieren; zunächst in einem neuen Ordner testen.
Im entpackten Projektordner in PowerShell oder CMD:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe run.py --demo
```

Danach startet `start_windows.bat` die Anwendung, oder:

```powershell
.venv\Scripts\python.exe run.py
```

Die drei Demo-Signale benötigen keine angeschlossene Hardware. Reale Verbindungen
werden nicht automatisch gestartet. Ihre Einstellungen werden im Dialog
**Verbindungen** verwaltet; die Oberfläche unterscheidet „verbunden“ und „Verbindung wird aufgebaut“.

## Start unter Linux/macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py --demo
```

Für den normalen Betrieb ist eine Desktop-/Grafikumgebung erforderlich.
Geräteberechtigungen und CAN-Treiber hängen von Betriebssystem und Adapter ab.
Die Original-Anbindung heißt „Telnet“, verwendet aber den vorhandenen TCP-Datenstrom;
es wurde keine neue Telnet-Terminalemulation hinzugefügt.

## Neue Arbeitsweise

| Bereich | Bedienung |
|---|---|
| Arbeitsfläche | Diagramme im Mittelpunkt; schwebend, gekachelt oder einzeln fokussiert. |
| Seitenleiste | **Diagramme**, **Signale**, **Analyse** statt einer überladenen Gesamtansicht. Breite verstellbar, ausblendbar. |
| Signale | Suchfeld; Signal auswählen und einem oder mehreren Diagrammen zuordnen. Y(t) und X(t) getrennt. |
| Diagramme | Zeitreihe, XY-Linie, XY-Streuung und bestehende XYZ-Streuung. Kurven ein-/ausblenden; Namen und Farben ändern. |
| 2D-Navigation | Mausrad zum Zoomen, Ziehen zum Verschieben, Doppelklick zum Einpassen; optionales Koordinaten-Fadenkreuz. |
| Achsen | Diagrammoptionen für manuelle X-/Y-Grenzen und Zeitfenster. Konstante Signale erhalten einen sichtbaren Wertebereich. |
| Einstellungen | Gitternetz, Legende, Kantenglättung, Fadenkreuz, Aktualisierungsintervall, Kurvenlimit und optionale Verdichtung. |
| Analyse | Anzahl, Minimum, Maximum, Mittelwert, Effektivwert (RMS), Standardabweichung und letzter **Y-Wert** aus dem gespeicherten Rohdatenfenster. |
| Export | Einzelnes Signal oder gesamter Rohpuffer als CSV; sichtbare Diagramm-Arbeitsfläche als PNG; Konfiguration als JSON. |

**Anzeige pausieren stoppt nicht die Erfassung.** Die Puffer bleiben begrenzt; bei langer
Pause können ältere Anzeige- und Rohwerte verloren gehen. Die Statusleiste zeigt die
entsprechenden Zähler. Für einen echten Aufnahmestopp die Verbindung stoppen.

### Tastatur

| Kürzel | Aktion |
|---|---|
| Ctrl+N | Diagramm erstellen |
| Ctrl+E | Rohdaten-CSV exportieren |
| Ctrl+Leertaste | Anzeige pausieren/fortsetzen |
| Ctrl+B | Seitenleiste ein-/ausblenden |
| Ctrl+, | Anzeigeeinstellungen |
| Ctrl+S | Workspace speichern |
| Ctrl+0 | Daten in allen Diagrammen einpassen |

## Datenintegrität und Grenzen

Rohdaten werden **vor der Anzeigeverdichtung** gespeichert. Statistik und CSV greifen
auf diesen Speicher zu, nicht auf die möglicherweise reduzierten Kurven.
Fehlende X- oder Z-Koordinaten bleiben im CSV leer; Empfangszeit ist kein gemessener X-Wert.
Der CSV-Export ist UTF-8 mit BOM, Komma als Feldtrenner und Punkt als Dezimalzeichen.
In Tabellenprogrammen gegebenenfalls den CSV-Import mit diesen Einstellungen verwenden.

| Grenze | Wert / Bedeutung |
|---|---|
| Signal-IDs im Datenpaket | Echte ganze Zahlen von 0 bis 255; keine booleschen Werte. |
| Eingabepaket | Maximal 64 KiB; ungültige und nicht-endliche Werte werden abgewiesen. |
| Eingangswarteschlange | Pro Verbindung höchstens 2.048 Pakete / 4 MiB; bei Überlast ältere Pakete entfernen. |
| Rohdaten | Höchstens 20.000 Werte je Signal und 250.000 insgesamt. |
| Anzeige-Zwischenpuffer | Höchstens 4.096 Punkte je Signal und Dimension. Weitere begrenzte Puffer gibt es in QML. |
| 2D-Kurven | Einstellbar 500–50.000 Punkte, Standard 10.000. |
| Quellen / Signale / Fenster | Maximal 128 gespeicherte Verbindungen, 256 Signale, 16 Diagramme; 64 Kurven je Diagramm. |
| 3D | Bestehender Quick3D-Renderer mit maximal 5.000 Punktobjekten je Serie; kein neu implementierter instanzierter GPU-Renderer. |

Das Aktualisierungsintervall ist eine **Ziel-Taktung, keine zugesicherte Bildrate**.
Sehr viele Kurven, 3D-Punkte, Quellen oder hohe Datenraten können weiterhin hohe Last
erzeugen. Diese Ausgabe ist **kein verlustfreier Langzeitrekorder**.
Der CSV-Export enthält nur die zum Exportstart noch gespeicherten Messwerte.
Zähler für Rohdatenersatz, ungültige Pakete und Überlast sind getrennt dargestellt.
Beim Verbindungsstopp kann die Oberfläche auf einen Worker bis zu 1,5 Sekunden warten;
bei mehreren problematischen Verbindungen kann sich diese Zeit summieren.

## Konfiguration und Migration

`config/config.json` ist die mitgelieferte **Vorlage**, nicht mehr der normale
Speicherort für laufende Benutzereinstellungen. Standardorte:

- Windows: `%APPDATA%\KymoStudio\config.json`
- Linux: `${XDG_CONFIG_HOME:-~/.config}/KymoStudio/config.json`
- macOS: `~/Library/Application Support/KymoStudio/config.json`

Ein vorhandenes Verzeichnis `PlotterApp` aus der Zeit vor der Umbenennung wird
beim ersten Start einmalig nach `KymoStudio` verschoben.

`KYMO_CONFIG_HOME` überschreibt das Benutzerdatenverzeichnis; der alte Name
`PLOTTER_CONFIG_HOME` wird weiterhin gelesen. Mit
`python run.py --config PFAD/config.json` lässt sich eine explizite schreibbare
Konfiguration wählen. Eine vorhandene Datei wird vor der Nutzung validiert.
Geometrie und einfache Darstellungspräferenzen liegen zusätzlich in Qt `Settings`.

Vorhandene JSON-Konfiguration zuerst sichern, dann in der neuen Oberfläche importieren.
Ein erfolgreicher Import stoppt vorhandene Verbindungen, leert Rohdaten und ersetzt
Verbindungsdefinitionen sowie den Workspace. Importierte Verbindungen bleiben gestoppt.
Bei einem Schreibfehler nach dem Stoppen können die alten Verbindungen bereits
angehalten sein; sie werden nicht stillschweigend wieder gestartet.

Gespeichert werden Diagrammdefinitionen, Zuordnungen, Namen, Farben, Sichtbarkeit und
2D-Achsenzustände. **Messwerte werden nicht im Workspace gespeichert.** Die Einstellung
„Anzeige pausiert“ und 3D-Kamerapositionen werden nicht als vollständige Sitzung gespeichert.

JSON kann MQTT-Zugangsdaten im Klartext enthalten. Konfigurationen und Protokolle nicht
ungeprüft veröffentlichen. Es wurde kein Betriebssystem-Schlüsselspeicher ergänzt.
Das Log rotiert im Benutzerdatenverzeichnis unter `logs/kymostudio.log`.

## Prüfungen auf dem Zielrechner

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe run.py --smoke-test
```

Der Smoke-Test verwendet ein temporäres Profil, öffnet die QML-Anwendung, startet die
Demo und prüft Dateneingang sowie erkannte QML-Fehler. Er ersetzt keine visuelle Abnahme.
Unter Windows anschließend `--demo` normal starten und die
[Abnahmecheckliste](TESTBERICHT.md#manuelle-abnahme-auf-dem-zielrechner) durchgehen.

Zusätzliche Prüfungen (Node.js nur für Entwicklungstests, nicht für die App nötig):

```bash
node tests/js/chart_math.test.cjs
node tools/check_qml_scripts.cjs
python tools/check_backend_contracts.py
python tools/benchmark_core.py
```

Der GitHub-Actions-Workflow führt Tests, Skript- und Vertragsprüfungen bei jedem Push aus.
Drei Tests lesen die Firmware-Quellen aus einem benachbarten
[KymoProbe](https://github.com/CodeName-666/kymoprobe)-Checkout; ohne diesen werden sie
nachvollziehbar übersprungen.

## Projektunterlagen

[Änderungen](../CHANGELOG.md) · [Architektur](ARCHITEKTUR.md) ·
[Testbericht](TESTBERICHT.md) · [offene Abnahmepunkte](TESTBERICHT.md#manuelle-abnahme-auf-dem-zielrechner)

Historische Planungs-/Phasendokumente liegen unter `docs/legacy/` und sind keine
aktuellen Freigabenachweise. Alte, nicht mehr von der Hauptansicht verwendete
QML-Komponenten bleiben aus Kompatibilitätsgründen im Quellbaum.

Die README-Screenshots erzeugt `tools/capture_screenshots.py` mit Demo-Daten
und einem temporären Profil; das Logo-Set erzeugt `tools/build_brand.py`.
