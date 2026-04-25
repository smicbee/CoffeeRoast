using Artisan;
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Linq;
using System.Windows.Forms;

namespace iRoastControl
{
    public class RoastReportWindow : Form
    {
        private RoastEvaluator.RoastScore _score;

        public RoastReportWindow(RoastEvaluator.RoastScore score)
        {
            _score = score;
            InitializeUI();
        }

        private void InitializeUI()
        {
            this.Text = "Roast Report";
            this.Size = new Size(520, 680);
            this.StartPosition = FormStartPosition.CenterParent;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.Font = new Font("Segoe UI", 10);
            
            this.Load += (s, e) => ThemeManager.ApplyTheme(this);

            var mainPanel = new Panel();
            mainPanel.Dock = DockStyle.Fill;
            mainPanel.AutoScroll = true;
            mainPanel.Padding = new Padding(20);
            this.Controls.Add(mainPanel);

            int y = 10;

            // === Header: Grade ===
            var gradeLabel = new Label();
            gradeLabel.Text = _score.Grade;
            gradeLabel.Font = new Font("Segoe UI", 48, FontStyle.Bold);
            gradeLabel.ForeColor = GetGradeColor(_score.Grade);
            gradeLabel.TextAlign = ContentAlignment.MiddleCenter;
            gradeLabel.Size = new Size(120, 80);
            gradeLabel.Location = new Point(20, y);
            mainPanel.Controls.Add(gradeLabel);

            var scoreLabel = new Label();
            scoreLabel.Text = $"{_score.TotalScore}/100 Punkte";
            scoreLabel.Font = new Font("Segoe UI", 16);
            scoreLabel.ForeColor = GetGradeColor(_score.Grade);
            scoreLabel.Location = new Point(150, y + 10);
            scoreLabel.Size = new Size(300, 30);
            mainPanel.Controls.Add(scoreLabel);

            var subtitleLabel = new Label();
            subtitleLabel.Text = GetGradeDescription(_score.Grade);
            subtitleLabel.Font = new Font("Segoe UI", 11, FontStyle.Italic);
            subtitleLabel.Location = new Point(150, y + 42);
            subtitleLabel.Size = new Size(300, 25);
            mainPanel.Controls.Add(subtitleLabel);

            y += 90;

            // === Separator ===
            var sep1 = CreateSeparator(y, mainPanel.Width - 40);
            mainPanel.Controls.Add(sep1);
            y += 15;

            // === Phasen-Zusammenfassung ===
            var phaseTitleLabel = new Label();
            phaseTitleLabel.Text = "📊 Phasen";
            phaseTitleLabel.Font = new Font("Segoe UI", 12, FontStyle.Bold);
            phaseTitleLabel.Location = new Point(20, y);
            phaseTitleLabel.Size = new Size(440, 25);
            mainPanel.Controls.Add(phaseTitleLabel);
            y += 28;

            var phaseLabel = new Label();
            phaseLabel.Text = _score.PhaseSummary;
            phaseLabel.Font = new Font("Segoe UI", 10);
            phaseLabel.Location = new Point(20, y);
            phaseLabel.Size = new Size(440, 22);
            mainPanel.Controls.Add(phaseLabel);
            y += 22;

            if (_score.DTR > 0)
            {
                var dtrLabel = new Label();
                dtrLabel.Text = $"DTR: {_score.DTR:F1}% | FC @ {TimeSpan.FromSeconds(_score.FirstCrackSecond):mm\\:ss} | Total: {TimeSpan.FromSeconds(_score.TotalDuration):mm\\:ss}";
                dtrLabel.Font = new Font("Segoe UI", 10);
                dtrLabel.Location = new Point(20, y);
                dtrLabel.Size = new Size(440, 22);
                mainPanel.Controls.Add(dtrLabel);
                y += 22;
            }

            // === Phasen-Bar ===
            y += 5;
            var phaseBar = new Panel();
            phaseBar.Location = new Point(20, y);
            phaseBar.Size = new Size(440, 24);
            phaseBar.Paint += (s, e) => DrawPhaseBar(e.Graphics, phaseBar.Width, phaseBar.Height);
            mainPanel.Controls.Add(phaseBar);
            y += 35;

            // === Separator ===
            mainPanel.Controls.Add(CreateSeparator(y, mainPanel.Width - 40));
            y += 15;

            // === Einzelbewertungen ===
            var detailTitle = new Label();
            detailTitle.Text = "📋 Bewertung";
            detailTitle.Font = new Font("Segoe UI", 12, FontStyle.Bold);
            detailTitle.Location = new Point(20, y);
            detailTitle.Size = new Size(440, 25);
            mainPanel.Controls.Add(detailTitle);
            y += 30;

            foreach (var item in _score.Items)
            {
                // Category name + status
                var catLabel = new Label();
                catLabel.Text = $"{item.Status} {item.Category}";
                catLabel.Font = new Font("Segoe UI", 10, FontStyle.Bold);
                catLabel.Location = new Point(20, y);
                catLabel.Size = new Size(300, 22);
                mainPanel.Controls.Add(catLabel);

                // Score
                var scoreItemLabel = new Label();
                scoreItemLabel.Text = $"{item.Score}/100";
                scoreItemLabel.Font = new Font("Segoe UI", 10, FontStyle.Bold);
                scoreItemLabel.ForeColor = GetScoreColor(item.Score);
                scoreItemLabel.TextAlign = ContentAlignment.MiddleRight;
                scoreItemLabel.Location = new Point(360, y);
                scoreItemLabel.Size = new Size(100, 22);
                mainPanel.Controls.Add(scoreItemLabel);
                y += 22;

                // Progress bar
                var barPanel = new Panel();
                barPanel.Location = new Point(20, y);
                barPanel.Size = new Size(440, 8);
                int barScore = item.Score;
                barPanel.Paint += (s, e) =>
                {
                    e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
                    // Background
                    Color barBg = ThemeManager.IsDarkMode ? Color.FromArgb(60, 60, 60) : Color.LightGray;
                    using (var bgBrush = new SolidBrush(barBg))
                        e.Graphics.FillRectangle(bgBrush, 0, 0, 440, 8);
                    // Fill
                    int fillWidth = (int)(440.0 * barScore / 100);
                    using (var fillBrush = new SolidBrush(GetScoreColor(barScore)))
                        e.Graphics.FillRectangle(fillBrush, 0, 0, fillWidth, 8);
                };
                mainPanel.Controls.Add(barPanel);
                y += 12;

                // Description
                var descLabel = new Label();
                descLabel.Text = item.Description;
                descLabel.Font = new Font("Segoe UI", 9);
                descLabel.Location = new Point(20, y);
                descLabel.Size = new Size(440, 20);
                mainPanel.Controls.Add(descLabel);
                y += 28;
            }

            // === Separator ===
            mainPanel.Controls.Add(CreateSeparator(y, mainPanel.Width - 40));
            y += 15;

            // === Verbesserungsvorschläge ===
            var improvTitle = new Label();
            improvTitle.Text = "💡 Verbesserungsvorschläge";
            improvTitle.Font = new Font("Segoe UI", 12, FontStyle.Bold);
            improvTitle.Location = new Point(20, y);
            improvTitle.Size = new Size(440, 25);
            mainPanel.Controls.Add(improvTitle);
            y += 30;

            foreach (var improvement in _score.Improvements)
            {
                var impLabel = new Label();
                impLabel.Text = "• " + improvement;
                impLabel.Font = new Font("Segoe UI", 9);
                impLabel.ForeColor = Color.FromArgb(255, 200, 100);
                impLabel.Location = new Point(30, y);
                impLabel.Size = new Size(430, 38);
                mainPanel.Controls.Add(impLabel);
                y += 40;
            }

            y += 10;

            // === RoR Statistics ===
            mainPanel.Controls.Add(CreateSeparator(y, mainPanel.Width - 40));
            y += 15;

            var rorTitle = new Label();
            rorTitle.Text = "📈 RoR Statistik";
            rorTitle.Font = new Font("Segoe UI", 12, FontStyle.Bold);
            rorTitle.Location = new Point(20, y);
            rorTitle.Size = new Size(440, 25);
            mainPanel.Controls.Add(rorTitle);
            y += 30;

            var rorStats = new Label();
            rorStats.Text = $"Durchschnitt: {_score.AvgRoR:F1}°C/min  |  Max: {_score.MaxRoR:F1}°C/min  |  Min: {_score.MinRoR:F1}°C/min";
            rorStats.Font = new Font("Segoe UI", 10);
            rorStats.Location = new Point(20, y);
            rorStats.Size = new Size(440, 22);
            mainPanel.Controls.Add(rorStats);
            y += 35;

            // === Close Button ===
            var closeButton = new Button();
            closeButton.Text = "Schließen";
            closeButton.Font = new Font("Segoe UI", 11);
            closeButton.Size = new Size(120, 35);
            closeButton.Location = new Point(340, y);
            closeButton.FlatStyle = FlatStyle.Flat;
            closeButton.Click += (s, e) => this.Close();
            mainPanel.Controls.Add(closeButton);
        }

        private void DrawPhaseBar(Graphics g, int width, int height)
        {
            g.SmoothingMode = SmoothingMode.AntiAlias;
            double total = _score.TotalDuration;
            if (total <= 0) return;

            int x = 0;

            // Drying
            int dryW = (int)(width * _score.DryingDuration / total);
            using (var b = new SolidBrush(Color.SandyBrown))
                g.FillRectangle(b, x, 0, dryW, height);
            if (dryW > 30) g.DrawString("Drying", new Font("Segoe UI", 7), Brushes.Black, x + 2, 4);
            x += dryW;

            // Maillard
            int mailW = (int)(width * _score.MaillardDuration / total);
            using (var b = new SolidBrush(Color.Chocolate))
                g.FillRectangle(b, x, 0, mailW, height);
            if (mailW > 30) g.DrawString("Maillard", new Font("Segoe UI", 7), Brushes.White, x + 2, 4);
            x += mailW;

            // Development
            int devW = width - x;
            using (var b = new SolidBrush(Color.DarkGreen))
                g.FillRectangle(b, x, 0, devW, height);
            if (devW > 30) g.DrawString("Dev", new Font("Segoe UI", 7), Brushes.White, x + 2, 4);
        }

        private Label CreateSeparator(int y, int width)
        {
            var sep = new Label();
            sep.BorderStyle = BorderStyle.Fixed3D;
            sep.Location = new Point(20, y);
            sep.Size = new Size(width > 0 ? width : 440, 2);
            return sep;
        }

        private Color GetGradeColor(string grade)
        {
            switch (grade)
            {
                case "A+": return Color.FromArgb(0, 255, 100);
                case "A": return Color.FromArgb(100, 255, 100);
                case "B": return Color.FromArgb(200, 255, 50);
                case "C": return Color.FromArgb(255, 200, 0);
                case "D": return Color.FromArgb(255, 130, 0);
                default: return Color.FromArgb(255, 50, 50);
            }
        }

        private Color GetScoreColor(int score)
        {
            if (score >= 80) return Color.FromArgb(100, 255, 100);
            if (score >= 60) return Color.FromArgb(255, 200, 0);
            if (score >= 40) return Color.FromArgb(255, 130, 0);
            return Color.FromArgb(255, 50, 50);
        }

        private string GetGradeDescription(string grade)
        {
            switch (grade)
            {
                case "A+": return "Perfekter Roast! Meisterklasse.";
                case "A": return "Exzellenter Roast. Sehr gut gemacht!";
                case "B": return "Guter Roast mit leichtem Verbesserungspotential.";
                case "C": return "Akzeptabler Roast – ein paar Dinge können besser werden.";
                case "D": return "Unter dem Optimum – Verbesserungen empfohlen.";
                default: return "Dieser Roast braucht deutliche Verbesserungen.";
            }
        }
    }
}
