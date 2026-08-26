# CoffeeRoast: gestapeltes RevA.2-/LOP-200-Gehäuse

Parametrisches, platzsparendes **Digitalprototyp-Gehäuse** für:

- CoffeeRoast Controller RevA.2: 160 × 100 × 1,6 mm
- Mean Well LOP-200-24: 101,6 × 50,8 × 25,4 mm

## Konzept

Die Platinen liegen nicht ungeschützt direkt übereinander. Das Gehäuse hat drei
Druckteile und zwei getrennte Ebenen:

1. `lower_base`: Werkzeugpflichtig geschlossene Netzteilkammer.
2. `controller_deck`: 2,4-mm-Vollseparator und darüber Drop-in-Aufnahme für die
   Controllerplatine. Vier M3-Schrauben befestigen das Deck an Inserts der
   Netzteilkammer; die Schraubenköpfe liegen später unter der Controllerplatine.
3. `lid_print`: abnehmbarer Snap-Deckel ausschließlich über dem SELV-Controller.

Der USB-C-Port J5 bleibt an der rechten Wand frei zugänglich. Die übrigen
Kabelöffnungen entsprechen dem bestehenden RevA.2-Gehäuse. Das Netzteil sitzt
auf vier echten leitfähigen 6-mm-M3-Abstandshaltern. Die Controllerplatine wird
ohne neue Bohrungen auf isolierten 5×5-mm-Auflagen eingelegt und vom Deckel an
verifizierten Randzonen niedergehalten.

## Abmessungen

| Teil | Nennmaß |
|---|---:|
| Geschlossener Außenkörper | ca. 169 × 109 × 76,6 mm |
| Netzteilkammer | 166 × 106 × 40,8 mm |
| Controllerdeck | 166 × 106 × 34,0 mm |
| USB-C-Ausschnitt | 11,0 × 5,8 mm |
| AC-Kabelverschraubung | Ø16,2 mm |
| 24-V-Deckdurchführung | Ø8,2 mm, zwingend mit geschlossener passender Buchse/Tülle |

Gegenüber einer seitlichen Anordnung wird die Grundfläche praktisch auf die
160×100-mm-Controllerplatine reduziert; bezahlt wird das mit rund 77 mm Höhe.

## Dateien erzeugen

```bash
cd mechanical/stacked-controller-psu-enclosure/openscad
./build.sh
```

Druckdateien in `generated/`:

- `lower_base.stl` / `.3mf`
- `controller_deck.stl` / `.3mf`
- `lid_print.stl` / `.3mf`
- geschlossene, Explosions-, USB- und AC-Ansichten
- `verification.json` und `manifest.json`

Alle Druckteile sind mit breiter Fläche auf dem Druckbett orientiert. Im Slicer
mindestens vier Perimeter und ausreichend Deck-/Bodenschichten verwenden; die
konkreten Einstellungen hängen vom tatsächlich qualifizierten V-0-Material ab.

## Benötigte Nicht-Druckteile

- 4 × leitfähige M3×6-mm-Abstandshalter, max. Ø6 mm, für das LOP-200
- passende M3-Schrauben/Scheiben/Sicherung und PE-Ringkabelschuhe
- 4 × M3 Heat-Set-Inserts plus Schrauben für den Controllerdeck
- zertifizierte Kabelverschraubung für Ø16,2-mm-Panelöffnung und reales AC-Kabel
- geschlossene, passende und für die Anwendung bewertete Kabeltülle/-buchse für
  die Ø8,2-mm-24-V-Durchführung
- korrekt ausgelegte Sicherung/Schaltung, Leitungen, Crimps und Zugentlastungen

## Sicherheits- und Freigabegrenze

`PROTOTYPE_NOT_RELEASED`. Das Modell ist keine Zulassung. Das LOP-200 ist ein
offenes 230-V-Netzteil. Vor realem Betrieb sind mindestens nötig:

1. dokumentiertes flammhemmendes UL94-V-0-Material und geeigneter Druckprozess;
2. PE-Bonding aller von Mean Well markierten Punkte, mit gemessener Kontinuität;
3. qualifizierte Prüfung von Sicherung, Schalter, Leiterquerschnitten, Crimps,
   Zugentlastung, Luft-/Kriechstrecken, Nähten und Touch-Probe-Schutz;
4. kein offenes Loch in der Trennplatte: 24-V-Durchführung mit passender
   geschlossener Tülle/Buchse bestücken;
5. physischer Fit-Test mit echter PCBA, USB-Stecker und sämtlichen Kabeln;
6. Temperaturtest bei maximaler realer Last und Einbaulage. Die Stapelung
   verschlechtert die freie Konvektion; **200 W Dauerleistung werden nicht
   unterstellt**.

Normales PLA oder PETG ist dafür nicht freigegeben. Für einen ersten stromlosen
Fit-Test kann günstiges Material verwendet werden; es darf danach nicht als
betriebsfertiges Netzspannungsgehäuse missverstanden werden.
