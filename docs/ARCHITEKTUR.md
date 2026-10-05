# Architektur der überarbeiteten KymoStudio

[Start / Bedienung](../README.md) · [Änderungen](../CHANGELOG.md) · [Testbericht](TESTBERICHT.md)

## Verantwortlichkeiten

| Ebene | Dateien | Aufgabe |
|---|---|---|
| Start | `run.py`, `python/main.py`, `python/Studio/studio.py` | Konfiguration und Qt starten; definierte Importpfade; QObject-/Engine-Lebensdauer. |
| Datenkern | `python/Core/parsing.py`, `Receiver/message.py` | Begrenzte Wire-Payloads parsen und Messwerte validieren; ohne QML. |
| Pufferschichten | `Core/ingress.py`, `buffering.py`, `samples.py` | Threadgrenze, begrenzte Anzeige, unabhängiger begrenzter Rohdatenbestand. |
| Persistenz | `Core/configuration.py`, `paths.py`, `workspace.py` | Vorlagen-/Benutzerpfade, atomare JSON-Dateien und validierte Workspace-Metadaten. |
| Qt-Fassade | `Backend/backend.py` | Öffentliche Slots, Signalmetadaten, Zeitbasis, Batches und Übergänge zur UI. |
| Verbindungsdienst | `Backend/connection_service.py` | Receiver erstellen/ersetzen/stoppen, echte Statusübergänge, alte Receiver-Ereignisse abweisen. |
| Receiver | `python/Receiver/` | Vorhandene Serial-, TCP/Telnet-, MQTT-, CAN- und Test-Anbindungen. |
| Native Helfer | `Backend/series_bridge.py`, `export_worker.py` | Qt-Serien stapelweise aktualisieren; CSV außerhalb des GUI-Threads schreiben. |
| UI-Zustand | `Workspace/WorkspaceController.qml` und `Models/` | Ein Verantwortlicher für Charts, Signale, Zuordnungen und Datenrouting. |
| UI-Ansichten | `AppUi.qml`, `Workbench/`, `ChartWorkspace.qml` | Benutzerabsichten an Controller/Backend weitergeben, keine eigene zweite Datenquelle. |
| Diagramme | `ChartTypes/`, `FloatingWindows/` | Typgerechte Darstellung und Fensterbedienung; keine eigenen Receiver-Abonnements. |

## Datenfluss

```text
Receiver-Worker
  -> IngressQueue (threadgeschützt, begrenzt)
  -> GUI-Timer: begrenzte Zahl Pakete entnehmen
  -> parse_payload / PlotDataPoint
  -> gemeinsame Zeitbasis je Quelle + Signalmetadaten
  -> SampleStore: ursprüngliche Werte behalten
  -> FrameBuffer: Anzeige separat begrenzen
  -> optional Min/Max-Verdichtung ohne explizites X
  -> QML-Ereignisbrücke
  -> WorkspaceController: Zuordnungen / kompatibler Diagrammtyp
  -> 2D: ChartMath + SeriesBridge -> Qt Charts
     3D: vorhandener begrenzter Quick3D-Punktrenderer
```

`Qt.DirectConnection` wird beim Empfang nur für das sehr kleine gesperrte Einreihen
verwendet. UI-Änderungen, Parsing und Service-Zustände erfolgen im GUI-Kontext.
Ein Paket zu erhalten bedeutet noch nicht, dass es gezeichnet oder im Rohpuffer
langfristig verfügbar ist; die Diagnostik trennt diese Fälle.

## Koordinaten und Statistik

`t` ist die normalisierte Quellzeit oder monotone Empfangslaufzeit. `x` bleibt eine
optionale echte Quellkoordinate. Zeitreihen können Y(t) oder explizites X(t) darstellen;
XY-Diagramme erfinden keinen gemessenen X-Wert aus der Empfangszeit.
Unterschiedliche Quellen werden nicht automatisch auf eine externe gemeinsame Uhr
synchronisiert. Rückwärts springende Quellzeitstempel werden nicht automatisch sortiert.

`SampleStore.statistics()` wertet das aktuell gespeicherte Y-Fenster aus und meldet
daneben einen Sitzungszähler. RMS/Standardabweichung verwenden skalierte Berechnungen,
um unnötigen Zwischenwert-Überlauf zu vermeiden. Eine Darstellungsausblendung löscht
keine gespeicherten Werte. Eine Messwertlöschung oder ein erfolgreicher Konfigurations-
import hingegen schon. Ein Signal, das erst später einem Diagramm zugeordnet wird,
erhält zukünftige Daten; der Rohpuffer wird nicht automatisch vollständig nachgezeichnet.

## Speicherung und Fehlerfälle

Atomare Speicherung: erst vollständig serialisieren, temporär im Zielverzeichnis
schreiben, flush/fsync, dann ersetzen. Ein ungültiger Import wird vor dem Verbindungs-
stopp abgewiesen. Scheitert die Dateioperation nach einem erfolgreichen Stopp, bleibt
die bisherige Datei erhalten; Verbindungen können bereits angehalten sein.
Ein Layout enthält keine Samples. Ein CSV-Export verwendet einen Snapshot; neue
währenddessen eintreffende Werte gehören nicht mehr zu diesem Export.

Beim Stoppen werden Worker nicht zwangsweise beendet. Nach 1,5 Sekunden wird ein
Fehler gemeldet und das Receiver-Objekt behalten. Dies reduziert die Gefahr, einen
laufenden Thread zu zerstören, garantiert aber nicht, dass jeder Treiber sofort stoppt.
Laufende CSV-Exporte verhindern das Schließen, bis ihre Dateibehandlung abgeschlossen ist.

## Erweiterungspunkte und verbleibender Bestand

Neue Transporte sollten den `Receiver`-Lebenszyklus erfüllen und über die bestehende
Registry verfügbar gemacht werden. Weitere reine Analysen gehören in `Core`, nicht
in QML. Neue Diagrammtypen benötigen Parser-unabhängige Koordinatenanforderungen,
Renderer, Controller-Unterstützung und eigene Tests.

Die QObject-Fassade und manche alten QML-Dateien sind weiterhin groß. Nichtaktive
`ChartsManager`-/`ChartWindow`-/Navigationsansichten sind aus Kompatibilitätsgründen
noch vorhanden. Ein weiterer Abbau sollte nach realer UI-Abnahme erfolgen, nicht
blind anhand vermeintlich ungenutzter Dateien. Die aktive Hauptansicht verwendet
die neue Workbench. 3D-Instancing, verlustfreie Aufzeichnung auf Disk, FFT/Filter,
Rückladen von CSV und Betriebssystem-Schlüsselspeicher wurden nicht hinzugefügt.

## Prüfbarkeit

Der reine Kern kann ohne Qt getestet werden. Statische API-/JavaScript-Prüfungen
sind ergänzend, aber weder QML-Typprüfung noch GUI-Test. Der echte Smoke-Test und
native Qt-Tests benötigen installierte Abhängigkeiten; deren Ausführung ist hier
nicht behauptet. Es erfolgte eine eigene Quelltextprüfung, kein unabhängiges Review
mit einem zweiten Agenten und keine Veröffentlichung in ein externes Repository.
