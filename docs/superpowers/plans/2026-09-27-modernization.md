# PlotterApp Modernization Implementation Plan

**Goal:** Bedienung, Datenintegrität, Speichergrenzen und Wartbarkeit der bestehenden Desktop-App verbessern.
**Architecture:** Qt-unabhängiger Kern, kompatible QObject-Fassade, kleinere QML-Arbeitsbereichskomponenten.
**Tech Stack:** Python 3.11–3.13, PySide6/QML, bestehende Transportbibliotheken.
**Spec:** ../specs/2026-09-27-modernization.md

## Global Constraints
Bestehende Wire-Formate und vier unterstützte Diagrammtypen erhalten. Keine GUI-Erfolgsaussagen ohne Qt-Laufzeit. Keine externen Schreibaktionen.

## Review Focus
Nicht-endliche Werte und boolesche Zahlen; Überlast bei hochfrequenten Quellen; Session-/Verbindungsbereinigung; kleine Fenster und Fokusbedienung; CSV-Export und atomare Speicherung.

## Aufgaben
- [x] 1. Parser-/Datenmodell-Regressionen zuerst reproduzieren, reine Parsing-Logik extrahieren und korrigieren.
- [x] 2. Speicherbegrenzung, unveränderte Analysewerte und atomare Konfigurationsdienste mit Unit-Tests implementieren.
- [x] 3. Backend-Fassade modularisieren, Lebenszyklus und Ereignisraten korrigieren; bestehende Slots erhalten.
- [x] 4. Plot-Rendering bündeln, Grenzen korrekt einhalten, Zoom/Pan und Cursoranalyse vereinheitlichen.
- [x] 5. Arbeitsfläche, Inspektor, Einstellungen und Dialoge überarbeiten; Tastatur und Export integrieren.
- [x] 6. Gesamttests, Quelltextprüfungen und Benchmark ausführen; Bedienungs-, Architektur- und Testdokumentation erstellen; vollständiges ZIP prüfen.

## Ergebnis
Implementierung und hier ausführbare Prüfungen durchgeführt. Die Laufzeitabnahme
der Qt-Oberfläche und realer Transporte bleibt offen; siehe `docs/TESTBERICHT.md`.
