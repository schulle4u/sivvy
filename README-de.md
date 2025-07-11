# Sivvy
Ein CSV-Editor für das Terminal.

## Über Sivvy

Sivvy (eine Art Kosename für CSV) ist ein Terminal-Editor zum Erstellen und Bearbeiten von CSV-Tabellen. Er wurde in Python geschrieben (v3.10 oder höher wird benötigt) und verwendet die integrierten CSV-Funktionen zum Öffnen und Bearbeiten der Dateien. Für die Anzeige der Daten nutzt Sivvy [Python Tabulate](https://pypi.org/project/tabulate/), wodurch zahlreiche Ausgabeformate und Designs zur Verfügung stehen. Es ist nur ein persönliches Tool, welches ich zur Verwaltung von digitalen Archivbeständen verwende, und erhebt keinen Anspruch darauf, die zahlreichen anderen Lösungen zur Visualisierung von CSV-Datensätzen zu ergänzen oder gar zu bereichern. Fehlerkorrekturen und Verbesserungsvorschläge sind natürlich trotzdem herzlich willkommen. 

## Funktionen

* Zahlreiche Ausgabeformate: Simple, Grid, Markdown, HTML und viele weitere.
* Integrierte Befehle zum Hinzufügen/bearbeiten/löschen/wiederherstellen von Zeilen, Bearbeiten der Spaltenköpfe, Programmsteuerung
* Trennzeichenerkennung: Ermittelt übliche CSV-Trennzeichen und legt sie beim Öffnen der Datei für die Eingabe neuer Daten fest.
* Zeilenbegrenzung: Zeigt nur die gewünschten Datensätze auf dem Bildschirm an.
* Positionsberechnung: Wenn der angegebene Zeilenindex eines neuen Datensatzes höher als die nächste freie Zeile ist, kann automatisch die nächsthöhere freie Zeile angelegt oder ein Satz Leerzeilen bis zum angegebenen Index eingefügt werden.
* Mehrsprachigkeit: Interface in englisch und deutsch, dank Gettext-Vorlage weitere Sprachen nachrüstbar.

## Aus dem Quellcode aufrufen

Einfach das Repository laden und Python-Abhängigkeiten via Pip oder die Paketverwaltung des Betriebssystems installieren: 

`pip install -r requirements.txt`. 

Der Aufruf geschieht mittels `python sivvy.py <Datei>`. Weitere Hilfe: `python sivvy.py --help`. 

Man kann auch das Script mittels Pyinstaller in eine ausführbare Programmdatei umwandeln, wodurch sich CSV-Dateien leichter im Dateimanager ohne die Kommandozeile mit Sivvy öffnen lassen sollten: 

`pyinstaller --onefile sivvy.py`

Die fertige Programmdatei befindet sich danach im Dist-Ordner. 

## Verwendung

Nach dem Öffnen einer CSV-Datei wird die Tabelle als formatierte Ausgabe auf dem Bildschirm angezeigt. Ist die angegebene Datei nicht vorhanden, fragt das Programm zunächst nach den Spaltenköpfen und legt die neue Datei danach an. Zusätzlich zu den eigentlichen Tabellenspalten wird in der ersten Spalte der Zeilenindex, also die Nummer der Tabellenzeile, angegeben. Der Editor geht davon aus, dass die erste Zeile der Tabelle immer die Spaltenköpfe enthält. Daher ist der Zeilenindex 1 nicht die Kopfzeile, sondern die erste Datenzeile. Um eine Zeile zu bearbeiten oder neu zu erstellen, wird einfach der entsprechende Zeilenindex in die Befehlszeile unterhalb der Tabelle eingegeben und mit der Enter-Taste bestätigt. Danach öffnet sich der Bearbeitungsbildschirm, in dem man einen neuen Datensatz erfassen oder bestehende Zeilen bearbeiten kann. Um die Kopfzeile zu ändern, muss als Zeilenindex 0 eingegeben werden. Oberhalb der Tabelle befindet sich die Statusanzeige, die alle Erfolgs- und etwaige Fehlermeldungen anzeigt.

Sivvy unterstützt einige einfache Befehle zur Steuerung des Programms. Eine Liste aller Befehle kann jederzeit mit "h" über die Befehlszeile abgerufen werden.

* "`d <Zeilennummer>`" zum Löschen einer Zeile
* "`u`" zum Wiederherstellen gelöschter Zeilen
* "`v <Zeilennummer>`" für die Detailansicht einer Zeile
* "`e`" zum Exportieren der aktuellen Tabelle als Datei
* "`s`" zum Umschalten der Statusmeldungsanzeige (alle oder nur die neusten 5 meldungen)
* "`c`" zum Bereinigen der Statusmeldungen
* "`h`" zum Anzeigen der Befehlsliste
* "`q`" zum Beenden des Programms

## Entwicklung

Copyright (C) Steffen Schultz, freigegeben unter den Bedingungen der MIT-Lizenz. 
