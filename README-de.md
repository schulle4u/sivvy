# Sivvy
Ein CSV-Editor für das Terminal.

## Über Sivvy

Sivvy (eine Art Kosename für CSV) ist ein Terminal-Editor zum Erstellen und Bearbeiten von CSV-Tabellen. Er wurde in Python geschrieben und verwendet die integrierten CSV-Funktionen zum Öffnen und Bearbeiten der Dateien. Für die Anzeige der Daten nutzt Sivvy {Python Tabulate](https://pypi.org/project/tabulate/), wodurch zahlreiche Ausgabeformate und Designs zur Verfügung stehen. Es ist nur ein persönliches Tool, welches ich zur Verwaltung von digitalen Archivbeständen verwende, und erhebt keinen Anspruch darauf, die zahlreichen anderen Lösungen zur Visualisierung von CSV-Datensätzen zu ergänzen oder gar zu bereichern. Fehlerkorrekturen und Verbesserungsvorschläge sind natürlich trotzdem herzlich willkommen. 

## Funktionen

* Zahlreiche Ausgabeformate: Simple, Grid, Markdown, HTML und viele weitere.
* Befehlseingabe: Zeilennummer, Spaltenköpfe, Programmsteuerung
* Trennzeichenerkennung: Ermittelt übliche CSV-Trennzeichen und legt sie beim Öffnen der Datei für die Eingabe neuer Daten fest.
* Zeilenbegrenzung: Zeigt nur die gewünschten Datensätze auf dem Bildschirm an.
* Positionsberechnung: Wenn der angegebene Zeilenindex eines neuen Datensatzes höher als die nächste freie Zeile ist, kann automatisch die nächsthöhere freie Zeile angelegt oder ein Satz Leerzeilen bis zum angegebenen Index eingefügt werden.
* Mehrsprachigkeit: Interface in englisch und deutsch, dank Gettext-Vorlage weitere Sprachen nachrüstbar.

## Installation

Einfach das Repository laden und Python-Abhängigkeiten via Pip oder die Paketverwaltung des Betriebssystmesinstallieren: 

`pip install -r requirements.txt`. 

Der Aufruf geschieht mittels `python sivvy.py <Datei>`. Weitere Hilfe: `python sivvy.py --help`. 

Man kann auch das Script mittels Pyinstaller in eine ausführbare Programmdatei umwandeln, wodurch sich CSV-Dateien leichter im Dateimanager ohne die Kommandozeile mit Sivvy öffnen lassen sollten: 

`pyinstaller --onefile sivvy.py`

Die fertige Programmdatei befindet sich danach im Dist-Ordner. 

## Entwicklung

Copyright (C) Steffen Schultz, freigegeben unter den Bedingungen der MIT-Lizenz. 
