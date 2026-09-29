# Testbericht · 27.09.2026

[README](../README.md) · [Architektur](ARCHITEKTUR.md) · [Änderungen](../CHANGELOG.md)

## Tatsächlich ausgeführt

Umgebung: Linux-Sandbox, Python 3.13.5; JavaScript-Prüfungen mit Node.js.
**PySide6 sowie die Serial-/MQTT-/CAN-Bibliotheken waren nicht verfügbar.**
Ein Installationsversuch konnte die benötigten Pakete nicht herunterladen.
Es wurden keine Qt-Ersatzmodule als vermeintlicher Laufzeitnachweis benutzt.

| Prüfung | Ergebnis | Aussage und Grenze |
|---|---|---|
| `python -m pytest -q` | **130 bestanden, 8 übersprungen** | Reiner Datenkern, Dienste, Wire-Protokoll und statische Architekturprüfungen. Kein vollständiger Qt-Lauf. |
| `python -m compileall -q python run.py tests tools` | Erfolgreich | Python-Syntax; importiert und startet die Qt-Oberfläche nicht. |
| `node tests/js/chart_math.test.cjs` | **12 Prüfungen bestanden** | Puffergrenzen, Serien-Anhängen und Achsenmathematik mit kontrollierten JavaScript-Testobjekten. Kein nativer Render-Benchmark. |
| `node tools/check_qml_scripts.cjs` | 100 QML-/JS-Dateien untersucht; 11 Scripts und 467 eingebettete Funktionen syntaktisch prüfbar | JavaScript-Syntax, keine QML-Typauflösung, keine Layout-Abnahme. |
| `python tools/check_backend_contracts.py` | 40 Datei/API-Paare ohne fehlende Backend-Methode | Methodenexistenz, nicht Qt-Metaobjekt-/Slot-Konvertierung. |
| `python tools/benchmark_core.py` | 300.000 Werte / 32 Signale; 250.000 Rohwerte behalten, 50.000 alte entfernt | Rohspeicher und Frame-Puffer; keine reale Datenschnittstelle, keine FPS-Messung. |

Die **acht übersprungenen Einträge** bestehen aus fünf Qt-abhängigen Testmodulen und
drei Tests gegen die nicht mitgelieferte separate `PlotterEcu`-Bibliothek.
Die fünf Module enthalten mehrere Testfälle; „acht“ darf nicht als Zahl aller
ungeprüften Qt-Funktionen missverstanden werden.

Aktuelle zusammengefasste Ausgabe: [verification/FINAL_CHECKS.txt](verification/FINAL_CHECKS.txt).
Weitere Ausgaben unter `verification/` zeigen echte Zwischenstände, einschließlich
absichtlich roter Regressionstests vor den Korrekturen. Ein früherer fehlgeschlagener
Zwischenstand ist nicht der Freigabestatus der später korrigierten Dateien.

## Testgetrieben reproduzierte Fälle

NaN/Infinity, boolesche Zahlen, ungültige IDs/Z-Werte, UTF-8-/JSON-/Binär-Payloads,
fragmentierte Frames, CRC-Prüfungen, Überlastgrenzen, konkurrierende Produzenten,
Rohdatenersatz, Statistik bei großen endlichen Werten, CSV-Metadaten,
fehlschlagende atomare Speicherung, Dateipfade und Datei-URLs, ungültige
Performance-Konfigurationen, verspätete Receiver-Ereignisse sowie ungültige
Workspace-/Achsenwerte wurden mit fokussierten Tests abgesichert.

Die Qt-freien Service-Tests nutzen kontrollierte Receiver-Doubles. Sie prüfen
Lebenszyklusentscheidungen, aber weder echte USB-Geräte noch Qt-Thread-Scheduling.

## Nicht als geprüft ausgegeben

Es gab hier **keinen erfolgreich ausgeführten Qt-/QML-Start**, keine visuelle
Screenshotabnahme, keine Prüfung unter Windows oder macOS, keinen GPU-/3D-Benchmark,
keinen echten Serial-/MQTT-/CAN-/TCP-Gerätetest und keinen extern ausgeführten
GitHub-Actions-Lauf. Deshalb ist dies ein implementierter Modernisierungsstand
mit dokumentierten Tests, **keine uneingeschränkte produktive Freigabe**.

Die native Qt-Serienbrücke und der Start-/Demo-Test liegen in
`tests/test_qt_workbench_integration.py`. Nach Installation von
`requirements-dev.txt` werden diese nicht mehr wegen fehlendem PySide6 übersprungen.
Das separate `--smoke-test`-Kommando verwendet ein temporäres Profil und prüft
Anwendungsstart, erkannte QML-Fehler und Dateneingang. Es beweist nicht, dass jedes
Diagramm korrekt gezeichnet wird oder jedes Bedienelement angenehm benutzbar ist.

## Manuelle Abnahme auf dem Zielrechner

| Schritt | Erwartung |
|---|---|
| Neue Umgebung installieren; `run.py --smoke-test` | Exitcode 0; Ausgabe `qt_smoke: passed`; keine QML-Fehler. |
| `run.py --demo` normal öffnen | Drei sichtbare, bewegte Zeitreihen; Quellenstatus und Zähler reagieren. |
| Fenster 900×600, 1440×900 und bei 125/150/200 % Skalierung testen | Bedienelemente erreichbar; Seitenleiste verstellbar; keine verdeckten wichtigen Dialogaktionen. |
| 2D zoomen, verschieben, Doppelklick, Ctrl+0, Achsen manuell ändern | Ausschnitt passt zur Aktion; konstante Signale verschwinden nicht. |
| Diagramme hinzufügen, kacheln, fokussieren, minimieren und schließen | Keine doppelten Zuordnungen oder übrigbleibenden Fenster. |
| Signal suchen, mehrfach zuordnen, sichtbar/unsichtbar schalten | Passende Kurven reagieren; explizites X wird nicht mit Zeit verwechselt. |
| Anzeige pausieren und später fortsetzen | Kurve pausiert; Eingangs-/Rohdatenzähler laufen weiter; Verluste bleiben sichtbar. |
| Rohdaten eines Signals exportieren | CSV lässt sich mit korrektem Trennzeichen lesen; Werte entsprechen dem Rohpuffer, nicht nur sichtbaren Punkten. |
| CSV-Fehler / schreibgeschützter Ordner / Schließen während Export | Fehler sichtbar; keine falsche Erfolgsmeldung; laufender Export nicht abgebrochen. |
| Layout speichern, App schließen und öffnen | Diagramme/Zuordnungen/2D-Ansicht erhalten; keine erfundenen alten Messwerte. |
| Ungültige Verbindung / Broker nicht erreichbar / Kabel abziehen | Ehrlicher Fehler-/Verbindungsstatus, Stoppen und erneuter Start möglich. |
| Aktive Verbindung bearbeiten und erneut verbinden | Keine alten Receiver-Daten oder verwaisten Threads. |
| JSON-Konfiguration importieren, auch ohne Workspace | Erst Validierung; danach definierter gestoppter Zustand; alter Workspace nicht versehentlich aktiv. |
| Reales XYZ-Signal über längere Zeit darstellen | Kamera, Farben und Punktgrenze prüfen; akzeptable Last separat messen. |
| Lange reale Messung mit Zielrate | Speichergrenzen und Zähler beobachten; benötigte Verlustfreiheit nicht voraussetzen. |

Erst nach dieser Abnahme sollte der Stand die bisherige produktive Installation
ersetzen. Die Original-7z-Datei wurde bei der Bearbeitung unverändert belassen.
