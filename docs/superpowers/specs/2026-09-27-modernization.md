# PlotterApp: Modernisierung

## Ziel und Rahmen
Die hochgeladene Desktop-Anwendung soll Messdaten weiterhin über Serial, TCP/Telnet, MQTT, CAN und synthetische Quellen empfangen und als Zeitreihe, XY-Linie, XY-Streuung oder XYZ darstellen. PySide6/QML und die vorhandenen öffentlichen Backend-Slots bleiben erhalten. Keine Umstellung auf eine Web-App.

## Gewählter Ansatz
Inkrementelle Modernisierung statt risikoreichem Komplett-Neubau: Qt-unabhängige Datenvalidierung, Konfiguration und begrenzte Messwertpuffer werden aus dem Backend herausgelöst. Die aktive Arbeitsfläche wird neu organisiert. Vorhandene Transport- und Chart-Komponenten werden korrigiert und integriert.

## Anforderungen
- Endliche numerische Werte, echte Integer-IDs, begrenzte Eingaben und eindeutige Zeit-/XY-Semantik.
- Begrenzte Anzeige-, Ereignis- und Analysepuffer; messbare Überlastzähler, keine behauptete verlustfreie Aufzeichnung.
- Größtmögliche Plotfläche, verstellbarer Inspektor, Suche, zentrale Einstellungen, sichtbarer Live-/Analysezustand.
- Diagramme anordnen, Fokusansicht, Screenshot und CSV-Export der gespeicherten Rohdaten.
- Konfiguration atomar schreiben, Quellvorlage nicht unbeabsichtigt überschreiben; sauberes Beenden.
- Vorhandene öffentliche Schnittstellen kompatibel halten; vorhandene Dateien nicht nur mit Kommentar-Kopfzeilen versehen.

## Prüfung
Neue reine Python-Tests sowie ausführbare JavaScript-Tests prüfen Datenlogik. Qt-Integrationstests und UI-Smoke-Test werden mitgeliefert. Fehlende Qt-Laufzeit in der Bearbeitungsumgebung wird ausdrücklich als Testgrenze dokumentiert, nicht durch Mocks als echter GUI-Test ausgegeben.
