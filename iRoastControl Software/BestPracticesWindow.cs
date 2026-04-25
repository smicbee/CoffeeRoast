using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace iRoastControl
{
    public class BestPracticesWindow : Form
    {
        public BestPracticesWindow()
        {
            InitializeUI();
        }

        private void InitializeUI()
        {
            this.Text = "☕ Coffee Roasting Best Practices";
            this.Size = new Size(780, 850);
            this.StartPosition = FormStartPosition.CenterParent;
            this.BackColor = Color.FromArgb(25, 25, 30);
            this.ForeColor = Color.White;
            this.Font = new Font("Segoe UI", 10);
            this.AutoScroll = false;

            var tabControl = new TabControl();
            tabControl.Dock = DockStyle.Fill;
            tabControl.Font = new Font("Segoe UI", 10);
            this.Controls.Add(tabControl);

            tabControl.TabPages.Add(CreateOverviewTab());
            tabControl.TabPages.Add(CreateRoRTab());
            tabControl.TabPages.Add(CreatePhasesTab());
            tabControl.TabPages.Add(CreateDefectsTab());
            tabControl.TabPages.Add(CreateTipsTab());

            this.Load += (s, e) => ThemeManager.ApplyTheme(this);
        }

        // =============================================================
        // TAB 1: OVERVIEW
        // =============================================================
        private TabPage CreateOverviewTab()
        {
            var tab = new TabPage("📖 Übersicht");
            tab.BackColor = Color.FromArgb(30, 30, 35);
            tab.AutoScroll = true;
            int y = 15;

            AddTitle(tab, ref y, "Kaffee Rösten – Grundlagen");
            AddParagraph(tab, ref y,
                "Beim Rösten durchläuft die Kaffeebohne eine komplexe chemische Transformation. " +
                "Über 800 verschiedene Aromaverbindungen entstehen durch die Maillard-Reaktion, " +
                "Karamellisierung und Strecker-Abbau. Die Kunst des Röstens liegt darin, diese " +
                "Reaktionen so zu steuern, dass das maximale Geschmackspotential entfaltet wird.");

            AddSubTitle(tab, ref y, "Die 4 Schlüsselprinzipien");
            AddBullet(tab, ref y, "🔥 Wärmeübertragung", "Konvektion (heiße Luft) und Leitung (Kontakt mit der Trommel) müssen ausgewogen sein");
            AddBullet(tab, ref y, "📈 Rate of Rise (RoR)", "Die Geschwindigkeit des Temperaturanstiegs bestimmt die Aromaentwicklung");
            AddBullet(tab, ref y, "⏱️ Timing", "Jede Phase hat ihre optimale Dauer – zu schnell oder zu langsam zerstört Aromen");
            AddBullet(tab, ref y, "🎯 Endpunkt", "Das Roast Level bestimmt den Charakter: hell = fruchtig/säuerlich, dunkel = schokoladig/bitter");

            y += 10;
            AddSubTitle(tab, ref y, "Empfohlene Zielwerte");

            var grid = new DataGridView();
            grid.Location = new Point(20, y);
            grid.Size = new Size(700, 175);
            grid.BackgroundColor = Color.FromArgb(40, 40, 45);
            grid.ForeColor = Color.White;
            grid.DefaultCellStyle.BackColor = Color.FromArgb(40, 40, 45);
            grid.DefaultCellStyle.ForeColor = Color.White;
            grid.DefaultCellStyle.SelectionBackColor = Color.FromArgb(60, 60, 65);
            grid.ColumnHeadersDefaultCellStyle.BackColor = Color.FromArgb(50, 50, 55);
            grid.ColumnHeadersDefaultCellStyle.ForeColor = Color.White;
            grid.EnableHeadersVisualStyles = false;
            grid.RowHeadersVisible = false;
            grid.AllowUserToAddRows = false;
            grid.ReadOnly = true;
            grid.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
            grid.Columns.Add("param", "Parameter");
            grid.Columns.Add("light", "Light Roast");
            grid.Columns.Add("medium", "Medium");
            grid.Columns.Add("dark", "Dark Roast");
            grid.Rows.Add("Endtemperatur", "195-205°C", "210-220°C", "225-235°C");
            grid.Rows.Add("Gesamtdauer", "8-10 min", "10-13 min", "12-15 min");
            grid.Rows.Add("DTR", "15-18%", "20-25%", "25-30%");
            grid.Rows.Add("RoR am Ende", "8-10 °C/min", "5-7 °C/min", "3-5 °C/min");
            grid.Rows.Add("First Crack", "~196-205°C", "~196-205°C", "~196-205°C");
            tab.Controls.Add(grid);
            y += 185;

            return tab;
        }

        // =============================================================
        // TAB 2: RATE OF RISE
        // =============================================================
        private TabPage CreateRoRTab()
        {
            var tab = new TabPage("📈 Rate of Rise");
            tab.BackColor = Color.FromArgb(30, 30, 35);
            tab.AutoScroll = true;
            int y = 15;

            AddTitle(tab, ref y, "Rate of Rise (RoR) – Der wichtigste Indikator");
            AddParagraph(tab, ref y,
                "Die RoR zeigt, wie schnell die Temperatur steigt (°C pro Minute). " +
                "Eine stetig fallende RoR ist das Zeichen eines gut kontrollierten Roasts. " +
                "Die RoR wird alle 30 Sekunden berechnet für ein sauberes Signal.");

            // === RoR Diagram ===
            y += 5;
            var rorDiagram = new Panel();
            rorDiagram.Location = new Point(20, y);
            rorDiagram.Size = new Size(700, 250);
            rorDiagram.Paint += DrawRoRDiagram;
            tab.Controls.Add(rorDiagram);
            y += 260;

            AddSubTitle(tab, ref y, "Die goldenen Regeln der RoR");
            AddBullet(tab, ref y, "📉 Stetig fallend", "Die RoR soll über den gesamten Roast monoton fallen – keine plötzlichen Sprünge");
            AddBullet(tab, ref y, "⚡ Nie unter 3°C/min", "Fällt die RoR unter 3, wird der Kaffee 'baked' – flach, brotartig, ohne Charakter");
            AddBullet(tab, ref y, "💥 FC-Flick ist OK", "Ein kurzer Anstieg der RoR um 1-2°C bei First Crack ist normal (exotherme Reaktion)");
            AddBullet(tab, ref y, "🚫 Kein RoR-Crash", "Ein plötzlicher Einbruch von >5°C/min deutet auf Energieverlust hin – mehr Hitze nachregeln");

            AddSubTitle(tab, ref y, "RoR Interpretation");
            AddBullet(tab, ref y, "RoR zu hoch (>20)", "Zu viel Energie → Bohnen verbrennen außen (Tipping/Scorching)");
            AddBullet(tab, ref y, "RoR zu niedrig (<3)", "Zu wenig Energie → Bohnen backen statt rösten → flach, ohne Süße");
            AddBullet(tab, ref y, "RoR stagniert", "Die Röstung 'stalled' → grasiger, unterentwickelter Geschmack");
            AddBullet(tab, ref y, "RoR steigt nach FC", "Unkontrollierte exotherme Reaktion → Scorching-Risiko");

            return tab;
        }

        private void DrawRoRDiagram(object sender, PaintEventArgs e)
        {
            var g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            int w = ((Panel)sender).Width;
            int h = ((Panel)sender).Height;

            // Background
            Color bgColor = ThemeManager.IsDarkMode ? Color.FromArgb(20, 20, 25) : Color.WhiteSmoke;
            using (var bgBrush = new SolidBrush(bgColor))
                g.FillRectangle(bgBrush, 0, 0, w, h);

            // Margins
            int ml = 50, mr = 20, mt = 20, mb = 40;
            int plotW = w - ml - mr;
            int plotH = h - mt - mb;

            // Grid
            Color gridColor = ThemeManager.IsDarkMode ? Color.FromArgb(50, 50, 55) : Color.LightGray;
            using (var gridPen = new Pen(gridColor))
            {
                for (int i = 0; i <= 5; i++)
                {
                    int gy = mt + plotH * i / 5;
                    g.DrawLine(gridPen, ml, gy, w - mr, gy);
                    g.DrawString((25 - i * 5).ToString(), new Font("Segoe UI", 8), Brushes.Gray, 10, gy - 7);
                }
                for (int i = 0; i <= 12; i++)
                {
                    int gx = ml + plotW * i / 12;
                    if (i % 2 == 0)
                        g.DrawString(i + "min", new Font("Segoe UI", 7), Brushes.Gray, gx - 10, h - 25);
                }
            }

            // Danger zone (below 3°C/min)
            int dangerY = mt + (int)(plotH * (25.0 - 3.0) / 25.0);
            using (var dangerBrush = new SolidBrush(Color.FromArgb(30, 255, 50, 50)))
                g.FillRectangle(dangerBrush, ml, dangerY, plotW, mt + plotH - dangerY);
            g.DrawString("⚠️ BAKED ZONE (<3°C/min)", new Font("Segoe UI", 7, FontStyle.Bold), 
                new SolidBrush(Color.FromArgb(100, 255, 80, 80)), ml + 5, dangerY + 2);

            // Ideal RoR curve (declining)
            var idealPoints = new PointF[] {
                GetPoint(0, 0, ml, mt, plotW, plotH, 12, 25),     // start
                GetPoint(1, 18, ml, mt, plotW, plotH, 12, 25),    // peak
                GetPoint(2, 16, ml, mt, plotW, plotH, 12, 25),
                GetPoint(3, 14, ml, mt, plotW, plotH, 12, 25),
                GetPoint(4, 12, ml, mt, plotW, plotH, 12, 25),
                GetPoint(5, 11, ml, mt, plotW, plotH, 12, 25),
                GetPoint(6, 10, ml, mt, plotW, plotH, 12, 25),
                GetPoint(7, 9, ml, mt, plotW, plotH, 12, 25),
                GetPoint(8, 8.5f, ml, mt, plotW, plotH, 12, 25),  // pre-FC
                GetPoint(8.5f, 10, ml, mt, plotW, plotH, 12, 25), // FC flick
                GetPoint(9, 8, ml, mt, plotW, plotH, 12, 25),
                GetPoint(10, 7, ml, mt, plotW, plotH, 12, 25),
                GetPoint(11, 6, ml, mt, plotW, plotH, 12, 25),
                GetPoint(12, 5, ml, mt, plotW, plotH, 12, 25),
            };
            using (var idealPen = new Pen(Color.FromArgb(0, 200, 100), 3))
                g.DrawCurve(idealPen, idealPoints, 0.3f);

            // Bad curve (crash)
            var badPoints = new PointF[] {
                GetPoint(0, 0, ml, mt, plotW, plotH, 12, 25),
                GetPoint(1, 20, ml, mt, plotW, plotH, 12, 25),
                GetPoint(3, 15, ml, mt, plotW, plotH, 12, 25),
                GetPoint(5, 12, ml, mt, plotW, plotH, 12, 25),
                GetPoint(7, 8, ml, mt, plotW, plotH, 12, 25),
                GetPoint(8, 4, ml, mt, plotW, plotH, 12, 25),   // crash!
                GetPoint(9, 2, ml, mt, plotW, plotH, 12, 25),
                GetPoint(10, 1.5f, ml, mt, plotW, plotH, 12, 25),
            };
            using (var badPen = new Pen(Color.FromArgb(150, 255, 80, 80), 2) { DashStyle = DashStyle.Dash })
                g.DrawCurve(badPen, badPoints, 0.3f);

            // FC marker
            float fcX = ml + plotW * 8.5f / 12f;
            using (var fcPen = new Pen(Color.FromArgb(150, 255, 0, 255), 1) { DashStyle = DashStyle.DashDot })
                g.DrawLine(fcPen, fcX, mt, fcX, mt + plotH);
            g.DrawString("FC", new Font("Segoe UI", 8, FontStyle.Bold), Brushes.Magenta, fcX + 3, mt + 3);

            // Legend
            int ly = h - 22;
            using (var idealPen = new Pen(Color.FromArgb(0, 200, 100), 2))
                g.DrawLine(idealPen, ml, ly + 5, ml + 25, ly + 5);
            g.DrawString("Ideal (stetig fallend)", new Font("Segoe UI", 8), Brushes.LightGray, ml + 30, ly - 2);

            using (var badPen = new Pen(Color.FromArgb(255, 80, 80), 2) { DashStyle = DashStyle.Dash })
                g.DrawLine(badPen, ml + 210, ly + 5, ml + 235, ly + 5);
            g.DrawString("Schlecht (RoR-Crash → baked)", new Font("Segoe UI", 8), Brushes.LightGray, ml + 240, ly - 2);

            // Axis labels
            g.DrawString("RoR (°C/min)", new Font("Segoe UI", 8), Brushes.Gray, 0, 2);
        }

        private PointF GetPoint(float min, float ror, int ml, int mt, int plotW, int plotH, float maxMin, float maxRoR)
        {
            return new PointF(ml + plotW * min / maxMin, mt + plotH * (1 - ror / maxRoR));
        }

        // =============================================================
        // TAB 3: PHASES
        // =============================================================
        private TabPage CreatePhasesTab()
        {
            var tab = new TabPage("🔥 Phasen");
            tab.BackColor = Color.FromArgb(30, 30, 35);
            tab.AutoScroll = true;
            int y = 15;

            AddTitle(tab, ref y, "Die 5 Phasen des Kaffeeröstens");

            // Phase diagram
            var phaseDiagram = new Panel();
            phaseDiagram.Location = new Point(20, y);
            phaseDiagram.Size = new Size(700, 200);
            phaseDiagram.Paint += DrawPhaseDiagram;
            tab.Controls.Add(phaseDiagram);
            y += 210;

            AddPhaseCard(tab, ref y, "💧 Drying Phase", "0 – 150°C  |  ca. 4-5 Min  |  ~30% der Zeit",
                "Die Bohnen verlieren ihre Feuchtigkeit (10-12%). Die Farbe wechselt von grün zu gelb. " +
                "In dieser Phase sollte viel Energie zugeführt werden (hohe RoR 15-20°C/min). " +
                "Die Bohnen riechen nach Heu/Gras.",
                Color.SandyBrown);

            AddPhaseCard(tab, ref y, "🟤 Maillard Phase", "150°C – FC  |  ca. 4-5 Min  |  ~35% der Zeit",
                "Die Maillard-Reaktion startet: Aminosäuren + Zucker → hunderte Aromaverbindungen. " +
                "Die Bohnen werden braun. Die RoR sollte stetig fallen (10-12°C/min). " +
                "Geruch wechselt zu Brot/Toast. Hier entstehen Schokoladen- und Nussaromen.",
                Color.Chocolate);

            AddPhaseCard(tab, ref y, "💥 First Crack", "~196-205°C  |  30-90 Sek",
                "Die Bohnen knacken hörbar – Dampf und CO₂ entweichen durch die Zellstruktur. " +
                "Dies ist eine exotherme Reaktion: die Bohne gibt Energie ab. " +
                "Die RoR kann kurz um 1-2°C ansteigen – das ist normal! " +
                "Light Roasts enden kurz nach dem ersten Knacken.",
                Color.OrangeRed);

            AddPhaseCard(tab, ref y, "☕ Development Phase", "Nach FC  |  1-3 Min  |  18-25% (DTR)",
                "Hier entwickeln sich die finalen Aromen. Die Balance zwischen Süße, Säure und Bitterkeit " +
                "wird in dieser Phase bestimmt. Die RoR sollte kontrolliert fallen (5-8°C/min). " +
                "ZU KURZ = sauer, unreif. ZU LANG = bitter, baked, flach. " +
                "Die Development Time Ratio (DTR) sollte 18-25% der Gesamtzeit betragen.",
                Color.DarkGreen);

            AddPhaseCard(tab, ref y, "⚠️ Second Crack", ">230°C  |  VORSICHT!",
                "Ein zweites, leiseres Knacken. Die Zellstruktur bricht weiter auf, Öle treten an die Oberfläche. " +
                "Für die meisten Spezialitäten-Kaffees ist dies ZU DUNKEL. " +
                "Die Bohnen können hier schnell verbrennen. Nur für Dark/Italian Roasts gedacht.",
                Color.DarkRed);

            return tab;
        }

        private void DrawPhaseDiagram(object sender, PaintEventArgs e)
        {
            var g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            int w = ((Panel)sender).Width;
            int h = ((Panel)sender).Height;

            // Background
            Color bgColor = ThemeManager.IsDarkMode ? Color.FromArgb(20, 20, 25) : Color.WhiteSmoke;
            using (var bgBrush = new SolidBrush(bgColor))
                g.FillRectangle(bgBrush, 0, 0, w, h);

            int barY = 30;
            int barH = 40;
            int ml = 20;
            int barW = w - 40;

            // Phase bars (proportional)
            float[] proportions = { 0.30f, 0.35f, 0.05f, 0.20f, 0.10f };
            Color[] colors = { Color.SandyBrown, Color.Chocolate, Color.OrangeRed, Color.DarkGreen, Color.FromArgb(60, 60, 60) };
            string[] labels = { "Drying", "Maillard", "FC", "Development", "Cooling" };
            string[] temps = { "25→150°C", "150→~200°C", "~200°C", "200→220°C", "→60°C" };

            int x = ml;
            for (int i = 0; i < 5; i++)
            {
                int pw = (int)(barW * proportions[i]);
                using (var b = new SolidBrush(colors[i]))
                    g.FillRectangle(b, x, barY, pw, barH);
                g.DrawRectangle(Pens.White, x, barY, pw, barH);

                if (pw > 50)
                {
                    var sf = new StringFormat { Alignment = StringAlignment.Center };
                    g.DrawString(labels[i], new Font("Segoe UI", 9, FontStyle.Bold), Brushes.White,
                        new RectangleF(x, barY + 5, pw, 18), sf);
                    g.DrawString(temps[i], new Font("Segoe UI", 7), Brushes.LightGray,
                        new RectangleF(x, barY + 22, pw, 15), sf);
                }
                x += pw;
            }

            // Time axis
            g.DrawString("0 min", new Font("Segoe UI", 8), Brushes.Gray, ml, barY + barH + 5);
            g.DrawString("~4-5 min", new Font("Segoe UI", 8), Brushes.Gray, ml + (int)(barW * 0.30), barY + barH + 5);
            g.DrawString("~8-9 min", new Font("Segoe UI", 8), Brushes.Gray, ml + (int)(barW * 0.65), barY + barH + 5);
            g.DrawString("~11-13 min", new Font("Segoe UI", 8), Brushes.Gray, ml + (int)(barW * 0.90) - 20, barY + barH + 5);

            // Temp curve overlay
            int curveTop = barY + barH + 30;
            int curveH = h - curveTop - 30;
            
            var tempPoints = new PointF[] {
                new PointF(ml, curveTop + curveH),
                new PointF(ml + barW * 0.08f, curveTop + curveH * 0.7f),
                new PointF(ml + barW * 0.30f, curveTop + curveH * 0.5f),
                new PointF(ml + barW * 0.50f, curveTop + curveH * 0.3f),
                new PointF(ml + barW * 0.65f, curveTop + curveH * 0.15f),
                new PointF(ml + barW * 0.70f, curveTop + curveH * 0.12f),
                new PointF(ml + barW * 0.85f, curveTop + curveH * 0.05f),
                new PointF(ml + barW * 0.90f, curveTop + curveH * 0.03f),
            };
            using (var curvePen = new Pen(Color.Red, 2))
                g.DrawCurve(curvePen, tempPoints, 0.3f);

            g.DrawString("25°C", new Font("Segoe UI", 7), Brushes.Gray, 0, curveTop + curveH - 8);
            g.DrawString("240°C", new Font("Segoe UI", 7), Brushes.Gray, 0, curveTop - 3);
            g.DrawString("Temperaturverlauf", new Font("Segoe UI", 8, FontStyle.Italic), Brushes.Red, ml + barW * 0.5f, curveTop + curveH * 0.15f);
        }

        // =============================================================
        // TAB 4: COMMON DEFECTS
        // =============================================================
        private TabPage CreateDefectsTab()
        {
            var tab = new TabPage("⚠️ Fehler");
            tab.BackColor = Color.FromArgb(30, 30, 35);
            tab.AutoScroll = true;
            int y = 15;

            AddTitle(tab, ref y, "Häufige Röstfehler und wie man sie vermeidet");

            AddDefectCard(tab, ref y, "🍞 Baked", "Ursache: RoR fällt unter 3°C/min oder stagniert",
                "Geschmack: Flach, brotartig, papierartig, keine Süße\n" +
                "Lösung: Mehr initiale Energie, RoR über 3°C/min halten, schneller abschließen",
                Color.FromArgb(255, 200, 100));

            AddDefectCard(tab, ref y, "🔥 Scorching", "Ursache: RoR zu hoch oder steigt nach FC",
                "Geschmack: Verbrannt, rauchig, bitter, scharfe Bitternoten\n" +
                "Lösung: Temperatur vor FC reduzieren, Ventilator erhöhen",
                Color.FromArgb(255, 100, 80));

            AddDefectCard(tab, ref y, "📌 Tipping", "Ursache: Zu viel Kontakthitze bei zu hoher initialer Temperatur",
                "Geschmack: Verbrannte Punkte an den Bohnen-Enden, ungleichmäßiger Geschmack\n" +
                "Lösung: Niedrigere Eingangstemperatur, mehr Konvektion (Ventilator hoch)",
                Color.FromArgb(255, 150, 50));

            AddDefectCard(tab, ref y, "🌿 Underdeveloped", "Ursache: Zu kurze Development Time (DTR <15%)",
                "Geschmack: Grasig, herb-sauer, grünlich, astringent\n" +
                "Lösung: Länger nach FC rösten, DTR auf 18-25% bringen",
                Color.FromArgb(150, 255, 150));

            AddDefectCard(tab, ref y, "⏸️ Stalling", "Ursache: RoR geht auf 0 oder wird negativ",
                "Geschmack: Unterentwickelt, grasig, flat\n" +
                "Lösung: Sofort reagieren – mehr Energie zuführen, bevor das Momentum verloren geht",
                Color.FromArgb(200, 200, 200));

            AddDefectCard(tab, ref y, "💨 Quaking", "Ursache: Zu viel Hitze kurz vor FC",
                "Geschmack: Ungleichmäßige Röstung – Innenseite roh, Außenseite dunkel\n" +
                "Lösung: Hitze 30-60s vor erwartetem FC reduzieren",
                Color.FromArgb(200, 150, 255));

            return tab;
        }

        // =============================================================
        // TAB 5: TIPS & TRICKS
        // =============================================================
        private TabPage CreateTipsTab()
        {
            var tab = new TabPage("💡 Tipps");
            tab.BackColor = Color.FromArgb(30, 30, 35);
            tab.AutoScroll = true;
            int y = 15;

            AddTitle(tab, ref y, "Profi-Tipps für bessere Roasts");

            AddSubTitle(tab, ref y, "🎯 Vor dem Roast");
            AddBullet(tab, ref y, "Vorheizen", "Immer gleichmäßig vorheizen – die Starttemperatur beeinflusst den gesamten Roast");
            AddBullet(tab, ref y, "Batchgröße", "Immer die gleiche Menge verwenden – Änderungen der Batchgröße ändern das Profil komplett");
            AddBullet(tab, ref y, "Rezept wählen", "Verwende das Rezept passend zur Bohnenhöhenlage (z.B. 1200-1500m für mittlere Höhenlagen)");

            y += 10;
            AddSubTitle(tab, ref y, "📈 Während des Roasts");
            AddBullet(tab, ref y, "RoR beobachten", "Die RoR-Kurve ist dein wichtigstes Werkzeug – sie zeigt Probleme bevor sie passieren");
            AddBullet(tab, ref y, "Fan-Speed anpassen", "Mehr Fan = weniger Hitze + mehr Konvektion. Nutze den Fan um die RoR sanft zu steuern");
            AddBullet(tab, ref y, "First Crack hören", "FC klingt wie Popcorn – dauert ~60-90s. Notiere den Zeitpunkt für die DTR-Berechnung");
            AddBullet(tab, ref y, "Nicht zu früh eingreifen", "Kleine Schwankungen sind normal. Greife nur ein wenn ein klarer Trend erkennbar ist");

            y += 10;
            AddSubTitle(tab, ref y, "☕ Nach dem Roast");
            AddBullet(tab, ref y, "Schnell kühlen", "Die Bohnen rösten nach dem Auswurf weiter – schnelle Kühlung ist essentiell");
            AddBullet(tab, ref y, "Ruhen lassen", "Frisch gerösteter Kaffee braucht 24-72h Entgasung – erst dann optimal");
            AddBullet(tab, ref y, "Filterkaffee", "4-7 Tage nach dem Rösten am besten");
            AddBullet(tab, ref y, "Espresso", "7-14 Tage nach dem Rösten optimal – braucht mehr CO₂-Entgasung");
            AddBullet(tab, ref y, "Logfile nutzen", "Vergleiche deine Roast-Logs (CSV) um systematische Verbesserungen zu finden");

            y += 10;
            AddSubTitle(tab, ref y, "📊 Bewertungs-Indikatoren in dieser App");
            AddBullet(tab, ref y, "RoR Verlauf", "Stetig fallend = gut. Crashs und Flicks = schlecht");
            AddBullet(tab, ref y, "DTR (Development Time Ratio)", "Zeit nach FC / Gesamtzeit. Ziel: 18-25%");
            AddBullet(tab, ref y, "Profilgenauigkeit", "Wie nah warst du am Rezept? <5°C = sehr gut");
            AddBullet(tab, ref y, "RoR Minimum", "Nie unter 3°C/min – sonst Baked-Risiko");

            return tab;
        }

        // =============================================================
        // HELPER METHODS
        // =============================================================
        private void AddTitle(TabPage tab, ref int y, string text)
        {
            var label = new Label();
            label.Text = text;
            label.Font = new Font("Segoe UI", 16, FontStyle.Bold);
            label.ForeColor = Color.White;
            label.Location = new Point(20, y);
            label.Size = new Size(700, 35);
            tab.Controls.Add(label);
            y += 40;
        }

        private void AddSubTitle(TabPage tab, ref int y, string text)
        {
            var label = new Label();
            label.Text = text;
            label.Font = new Font("Segoe UI", 13, FontStyle.Bold);
            label.ForeColor = Color.FromArgb(200, 200, 255);
            label.Location = new Point(20, y);
            label.Size = new Size(700, 28);
            tab.Controls.Add(label);
            y += 32;
        }

        private void AddParagraph(TabPage tab, ref int y, string text)
        {
            var label = new Label();
            label.Text = text;
            label.Font = new Font("Segoe UI", 10);
            label.ForeColor = Color.LightGray;
            label.Location = new Point(20, y);
            label.Size = new Size(700, 60);
            tab.Controls.Add(label);
            y += 65;
        }

        private void AddBullet(TabPage tab, ref int y, string title, string desc)
        {
            var titleLabel = new Label();
            titleLabel.Text = "▸ " + title;
            titleLabel.Font = new Font("Segoe UI", 10, FontStyle.Bold);
            titleLabel.ForeColor = Color.FromArgb(255, 220, 150);
            titleLabel.Location = new Point(30, y);
            titleLabel.Size = new Size(680, 22);
            tab.Controls.Add(titleLabel);
            y += 22;

            var descLabel = new Label();
            descLabel.Text = desc;
            descLabel.Font = new Font("Segoe UI", 9);
            descLabel.ForeColor = Color.Silver;
            descLabel.Location = new Point(50, y);
            descLabel.Size = new Size(660, 20);
            tab.Controls.Add(descLabel);
            y += 26;
        }

        private void AddPhaseCard(TabPage tab, ref int y, string title, string subtitle, string description, Color accentColor)
        {
            var panel = new Panel();
            panel.Location = new Point(20, y);
            panel.Size = new Size(700, 95);
            panel.BackColor = Color.FromArgb(40, 40, 45);
            panel.Paint += (s, e) =>
            {
                using (var pen = new Pen(accentColor, 3))
                    e.Graphics.DrawLine(pen, 0, 0, 0, panel.Height);
            };
            tab.Controls.Add(panel);

            var titleLabel = new Label();
            titleLabel.Text = title;
            titleLabel.Font = new Font("Segoe UI", 11, FontStyle.Bold);
            titleLabel.ForeColor = accentColor;
            titleLabel.Location = new Point(12, 5);
            titleLabel.Size = new Size(680, 22);
            panel.Controls.Add(titleLabel);

            var subLabel = new Label();
            subLabel.Text = subtitle;
            subLabel.Font = new Font("Segoe UI", 9, FontStyle.Italic);
            subLabel.ForeColor = Color.Gray;
            subLabel.Location = new Point(12, 26);
            subLabel.Size = new Size(680, 18);
            panel.Controls.Add(subLabel);

            var descLabel = new Label();
            descLabel.Text = description;
            descLabel.Font = new Font("Segoe UI", 9);
            descLabel.ForeColor = Color.LightGray;
            descLabel.Location = new Point(12, 46);
            descLabel.Size = new Size(680, 44);
            panel.Controls.Add(descLabel);

            y += 102;
        }

        private void AddDefectCard(TabPage tab, ref int y, string title, string cause, string details, Color color)
        {
            var panel = new Panel();
            panel.Location = new Point(20, y);
            panel.Size = new Size(700, 100);
            panel.BackColor = Color.FromArgb(40, 40, 45);
            panel.Paint += (s, e) =>
            {
                using (var pen = new Pen(color, 3))
                    e.Graphics.DrawLine(pen, 0, 0, 0, panel.Height);
            };
            tab.Controls.Add(panel);

            var titleLabel = new Label();
            titleLabel.Text = title;
            titleLabel.Font = new Font("Segoe UI", 11, FontStyle.Bold);
            titleLabel.ForeColor = color;
            titleLabel.Location = new Point(12, 5);
            titleLabel.Size = new Size(680, 22);
            panel.Controls.Add(titleLabel);

            var causeLabel = new Label();
            causeLabel.Text = cause;
            causeLabel.Font = new Font("Segoe UI", 9, FontStyle.Italic);
            causeLabel.ForeColor = Color.Gray;
            causeLabel.Location = new Point(12, 26);
            causeLabel.Size = new Size(680, 18);
            panel.Controls.Add(causeLabel);

            var detailLabel = new Label();
            detailLabel.Text = details;
            detailLabel.Font = new Font("Segoe UI", 9);
            detailLabel.ForeColor = Color.LightGray;
            detailLabel.Location = new Point(12, 46);
            detailLabel.Size = new Size(680, 48);
            panel.Controls.Add(detailLabel);

            y += 107;
        }
    }
}
