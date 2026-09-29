# Änderungen · Modernisierung vom 27.09.2026

## Aktive Oberfläche

`AppUi.qml` wurde als neue Arbeitsfläche aufgebaut, nicht nur umbenannt oder mit
neuen Kopfzeilen versehen. Die Bedienung verteilt sich auf schmale Hauptwerkzeugleiste,
Diagrammbereich, verstellbare Seitenleiste und sichtbare Status-/Überlastmeldungen.

Neue Komponenten unter `qml/content/Workbench/` trennen Diagrammerstellung,
Signalzuordnung, Einstellungen, Statistik, Achsengrenzen und Arbeitsbereichsliste.
Diagramme lassen sich kacheln, fokussieren, umbenennen und schließen. Signalfilter,
Mehrfachzuordnung, Y(t)/X(t), Kurvensichtbarkeit und vorhandene Kurveneditoren sind
angebunden. Einstellungen werden vor Anwendung geprüft; fehlgeschlagenes Speichern
wird nicht als Erfolg angezeigt. Ungültige Verbindungsdaten schließen den Dialog
nicht mehr sofort.

## Rendering und Erfassung

Der Backend-Frame-Timer bündelt die Übertragung standardmäßig auf ein 33-ms-Ziel.
Ein überfüllter Punktpuffer löst keinen zusätzlichen sofortigen QML-Aufruf mehr aus.
Die 2D-Renderer nutzen einen nativen Qt-Serienadapter für Punktlisten. Alte Punkte
werden anhand des exakten Überhangs entfernt, auch bei größeren Paketen.
Konstante Achsenbereiche bekommen eine nicht-nullbreite Darstellung.

Eine threadgeschützte, paket- und bytebegrenzte Eingangswarteschlange verhindert
unbegrenztes Wachstum durch pro Paket erzeugte GUI-Ereignisse. Anzeige, Rohdaten
und verzögert zugestellte QML-Ereignisse sind separat begrenzt. Überlast bleibt möglich
und wird gezählt; es gibt keine Verlustfreiheits- oder FPS-Garantie.

**Anzeige pausieren** bleibt unabhängig von der Erfassung. Optionale Min/Max-Verdichtung
betrifft nur Y-Daten ohne explizites X und nur die Anzeige. Statistiken und CSV werden
nicht aus verdichteten Diagrammpunkten berechnet. Der vorhandene XYZ-Renderer wurde
integriert, aber nicht durch einen vollständig neuen GPU-Renderer ersetzt.

## Korrigierte Daten- und Lebenszyklusprobleme

| Ausgangsproblem | Änderung / Nachweis |
|---|---|
| Bool, NaN und Infinity konnten als Messwerte durchgehen; Z-Prüfung war unerreichbar. | Strikte Prüfung in `Receiver/message.py`, Parser in `Core/parsing.py`; Regressionstests. |
| Große Punktpakete konnten Serienlimits überschreiten. | Exakte Begrenzung in `ChartMath.js` und `Backend/series_bridge.py`; JS-Tests und separater Qt-Test. |
| Konstante Werte erzeugten gleiche Achsenminima/-maxima. | Getestete gepolsterte Bereichsberechnung, in beide 2D-Renderer integriert. |
| Der bisherige Konfigurationspfad zeigte inkonsistent in den Quellbaum. | Eindeutiges Benutzerverzeichnis, expliziter Pfad und atomare Ersetzung. |
| Empfangs-/Zykluszeiten hingen von Änderungen der Systemuhr ab. | Monotone Empfangs-/Zyklusmessung; Zeitstempelursprung je Verbindung. |
| Aktive Einstellungen wurden ohne kontrollierten Receiver-Wechsel geändert. | Kandidat validieren, alte Verbindung stoppen, neuen Receiver zuordnen und starten. |
| Verspätete Signale eines ersetzten Receivers konnten den neuen beeinflussen. | Receiver-Identität vor Status- und Datenweiterleitung prüfen; Regressionstest. |
| Thread-Ende konnte unendlich blockieren oder ein noch laufender Worker verschwinden. | Kooperatives Stoppsignal, begrenztes Warten, Receiver bei Fehlschlag behalten. |
| MQTT-Callbacks konnten Zustände aus dem Worker direkt ändern. | Status über Qt-Signale; Eingangsdaten zunächst nur in den gesperrten Puffer schreiben. |
| Ein neuer Verbindungsversuch konnte während MQTT-CONNACK wiederholt werden. | Separate offene Sitzung, Bestätigungsfrist und unterbrechbare Wiederholpause. |
| Fehlerhafte gespeicherte Achsengrenzen gelangten ungeprüft zur UI. | Versions-, Struktur-, Wertebereichs- und Referenzprüfung des Workspaces. |

Bei Qt-/Transportänderungen dokumentiert die Tabelle **Implementierung**, nicht
bereits erfolgte Hardwareabnahme. Den tatsächlichen Testumfang beschreibt der Testbericht.

## Struktur, Analyse und Export

Parser, Eingangspuffer, Frame-Puffer, Rohdatenspeicher, Konfigurationslogik,
Workspace-Validierung und Pfadauflösung liegen in Qt-unabhängigen Modulen.
`ConnectionService`, `CsvExportWorker` und `SeriesBridge` entlasten die Backend-Fassade.
Die vorhandenen QML-Backend-Methoden bleiben verfügbar.

CSV wird aus einem begrenzten Rohdaten-Snapshot in einem Worker atomar geschrieben.
Externe Signalnamen werden gegen Tabellenformeln entschärft. Layout und Verbindungen
werden ohne Rohdaten gespeichert. Rotierende Logs ersetzen unbegrenzte Protokolldateien.

Neue Tests, Prüfskripte, Demo-/Smoke-Test-Start, Windows-Starter und GitHub-Actions-
Konfiguration sind enthalten. Historische Dokumente wurden unter `docs/legacy/`
eingeordnet. Bestehende nichtaktive Altkomponenten bleiben als Kompatibilitätsbestand
erhalten; dies ist kein vollständiges Entfernen sämtlicher Legacy-Pfade.
