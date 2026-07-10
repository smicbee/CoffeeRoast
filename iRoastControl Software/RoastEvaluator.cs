using Artisan;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;

namespace iRoastControl
{
    /// <summary>
    /// Analysiert einen abgeschlossenen Roast und generiert eine detaillierte Bewertung.
    /// </summary>
    public class RoastEvaluator
    {
        public class RoastScore
        {
            public int TotalScore { get; set; } // 0-100
            public string Grade { get; set; } // A+ bis F
            public List<ScoreItem> Items { get; set; } = new List<ScoreItem>();
            public List<string> Improvements { get; set; } = new List<string>();
            public string PhaseSummary { get; set; }
            public double DryingDuration { get; set; }
            public double MaillardDuration { get; set; }
            public double DevelopmentDuration { get; set; }
            public double TotalDuration { get; set; }
            public double DTR { get; set; }
            public double AvgRoR { get; set; }
            public double MaxRoR { get; set; }
            public double MinRoR { get; set; }
            public int FirstCrackSecond { get; set; }
        }

        public class ScoreItem
        {
            public string Category { get; set; }
            public int Score { get; set; } // 0-100
            public string Status { get; set; } // ✅ ⚠️ ❌
            public string Description { get; set; }
        }

        public static RoastScore Evaluate(double[] realCurve, double[] targetCurve, 
            double[] rorCurve, int duration, int firstCrackSecond, double expectedFC)
        {
            var score = new RoastScore();
            score.TotalDuration = duration;
            score.FirstCrackSecond = firstCrackSecond;

            if (realCurve == null || duration <= 30) 
            {
                score.TotalScore = 0;
                score.Grade = "N/A";
                score.Items.Add(new ScoreItem { Category = "Dauer", Score = 0, Status = "❌", Description = "Roast zu kurz für Bewertung" });
                return score;
            }

            // === 1. RoR Analyse ===
            var validRoR = new List<double>();
            int rorCrashCount = 0;
            int rorFlickCount = 0;
            double prevRoR = double.NaN;
            
            for (int i = 60; i < Math.Min(duration, rorCurve.Length); i++)
            {
                if (!double.IsNaN(rorCurve[i]))
                {
                    validRoR.Add(rorCurve[i]);
                    if (!double.IsNaN(prevRoR))
                    {
                        double delta = rorCurve[i] - prevRoR;
                        if (delta < -3) rorCrashCount++;    // Plötzlicher RoR-Einbruch
                        if (delta > 2) rorFlickCount++;      // Unerwünschter RoR-Anstieg
                    }
                    prevRoR = rorCurve[i];
                }
            }

            if (validRoR.Count > 0)
            {
                score.AvgRoR = validRoR.Average();
                score.MaxRoR = validRoR.Max();
                score.MinRoR = validRoR.Min();
            }

            // RoR Declining Check
            int rorDecliningScore = 100;
            if (rorCrashCount > 3) rorDecliningScore -= 30;
            else if (rorCrashCount > 0) rorDecliningScore -= rorCrashCount * 8;
            if (rorFlickCount > 3) rorDecliningScore -= 25;
            else if (rorFlickCount > 0) rorDecliningScore -= rorFlickCount * 7;
            rorDecliningScore = Math.Max(0, rorDecliningScore);

            string rorStatus = rorDecliningScore >= 80 ? "✅" : rorDecliningScore >= 50 ? "⚠️" : "❌";
            string rorDesc = $"RoR-Verlauf: Avg {score.AvgRoR:F1}°C/min, {rorCrashCount} Crash(es), {rorFlickCount} Flick(s)";
            if (rorCrashCount > 0) score.Improvements.Add("RoR-Crashs vermeiden: Hitze gleichmäßiger reduzieren, nicht abrupt");
            if (rorFlickCount > 1) score.Improvements.Add("RoR-Flicks vermeiden: Nach First Crack die Hitze nicht erhöhen");
            score.Items.Add(new ScoreItem { Category = "RoR Verlauf", Score = rorDecliningScore, Status = rorStatus, Description = rorDesc });

            // === 2. Phasen-Analyse ===
            int dryingEnd = 0;
            int maillardEnd = 0;
            
            for (int i = 0; i < Math.Min(duration, realCurve.Length); i++)
            {
                if (!double.IsNaN(realCurve[i]))
                {
                    if (dryingEnd == 0 && realCurve[i] >= 150) dryingEnd = i;
                    if (maillardEnd == 0 && realCurve[i] >= 190) maillardEnd = i;
                }
            }

            score.DryingDuration = dryingEnd;
            score.MaillardDuration = firstCrackSecond > 0 ? firstCrackSecond - dryingEnd : maillardEnd - dryingEnd;
            score.DevelopmentDuration = firstCrackSecond > 0 ? duration - firstCrackSecond : 0;

            // DTR Bewertung
            if (firstCrackSecond > 0 && duration > firstCrackSecond)
            {
                score.DTR = (double)(duration - firstCrackSecond) / duration * 100;
                int dtrScore = 100;
                if (score.DTR < 15) { dtrScore = 40; score.Improvements.Add("DTR zu niedrig (<15%): Länger nach First Crack entwickeln lassen"); }
                else if (score.DTR < 18) { dtrScore = 70; score.Improvements.Add("DTR am unteren Rand: Etwas mehr Development Time könnte helfen"); }
                else if (score.DTR > 30) { dtrScore = 50; score.Improvements.Add("DTR zu hoch (>30%): Risiko von flachem \"baked\" Geschmack"); }
                else if (score.DTR > 25) { dtrScore = 75; }
                
                string dtrStatus = dtrScore >= 80 ? "✅" : dtrScore >= 50 ? "⚠️" : "❌";
                score.Items.Add(new ScoreItem { Category = "DTR", Score = dtrScore, Status = dtrStatus, 
                    Description = $"Development Time Ratio: {score.DTR:F1}% (Ziel: 18-25%)" });
            }
            else
            {
                score.Items.Add(new ScoreItem { Category = "DTR", Score = 0, Status = "⚠️", 
                    Description = "Kein First Crack erkannt – DTR kann nicht berechnet werden" });
                score.Improvements.Add("First Crack wurde nicht erreicht – Röstprofil oder Temperatur prüfen");
            }

            // === 3. Dauer-Bewertung ===
            int durationScore = 100;
            if (duration < 300) { durationScore = 30; score.Improvements.Add("Roast zu kurz (<5min): Bohnen sind wahrscheinlich unterentwickelt"); }
            else if (duration < 420) { durationScore = 60; score.Improvements.Add("Roast eher kurz: Langsamerer Temperaturanstieg könnte mehr Aromen entwickeln"); }
            else if (duration > 900) { durationScore = 50; score.Improvements.Add("Roast sehr lang (>15min): Risiko von \"baked\" Geschmack"); }
            else if (duration > 780) { durationScore = 70; }
            
            string durStatus = durationScore >= 80 ? "✅" : durationScore >= 50 ? "⚠️" : "❌";
            score.Items.Add(new ScoreItem { Category = "Röstdauer", Score = durationScore, Status = durStatus,
                Description = $"Gesamt: {TimeSpan.FromSeconds(duration):mm\\:ss} (Empfohlen: 8-13 min)" });

            // === 4. RoR-Minimum Check (Baked Risiko) ===
            int bakedScore = 100;
            if (score.MinRoR < 2 && score.MinRoR > 0) { bakedScore = 30; score.Improvements.Add("RoR unter 2°C/min gefallen: Hohes Risiko für 'baked' Kaffee"); }
            else if (score.MinRoR < 3) { bakedScore = 60; score.Improvements.Add("RoR nahe kritischer Grenze (3°C/min): Momentum besser halten"); }
            else if (score.MinRoR < 5) { bakedScore = 85; }

            string bakedStatus = bakedScore >= 80 ? "✅" : bakedScore >= 50 ? "⚠️" : "❌";
            score.Items.Add(new ScoreItem { Category = "RoR Minimum", Score = bakedScore, Status = bakedStatus,
                Description = $"Min RoR: {score.MinRoR:F1}°C/min (Nie unter 3°C/min fallen lassen)" });

            // === 5. Profilabweichung ===
            if (targetCurve != null)
            {
                double totalDeviation = 0;
                int deviationCount = 0;
                for (int i = 30; i < Math.Min(duration, Math.Min(realCurve.Length, targetCurve.Length)); i++)
                {
                    if (!double.IsNaN(realCurve[i]) && !double.IsNaN(targetCurve[i]))
                    {
                        totalDeviation += Math.Abs(realCurve[i] - targetCurve[i]);
                        deviationCount++;
                    }
                }
                double avgDeviation = deviationCount > 0 ? totalDeviation / deviationCount : 0;
                int profileScore = 100;
                if (avgDeviation > 20) { profileScore = 30; score.Improvements.Add($"Durchschnittliche Profilabweichung: {avgDeviation:F1}°C – PID-Tuning empfohlen"); }
                else if (avgDeviation > 10) { profileScore = 60; score.Improvements.Add($"Profilabweichung ({avgDeviation:F1}°C) leicht erhöht – Feintuning möglich"); }
                else if (avgDeviation > 5) { profileScore = 80; }

                string profStatus = profileScore >= 80 ? "✅" : profileScore >= 50 ? "⚠️" : "❌";
                score.Items.Add(new ScoreItem { Category = "Profilgenauigkeit", Score = profileScore, Status = profStatus,
                    Description = $"Durchschnittliche Abweichung: {avgDeviation:F1}°C vom Rezept" });
            }

            // === Gesamtscore ===
            if (score.Items.Count > 0)
            {
                score.TotalScore = (int)score.Items.Average(s => s.Score);
            }

            if (score.TotalScore >= 90) score.Grade = "A+";
            else if (score.TotalScore >= 80) score.Grade = "A";
            else if (score.TotalScore >= 70) score.Grade = "B";
            else if (score.TotalScore >= 60) score.Grade = "C";
            else if (score.TotalScore >= 50) score.Grade = "D";
            else score.Grade = "F";

            // Phasen-Zusammenfassung
            score.PhaseSummary = $"Drying: {TimeSpan.FromSeconds(score.DryingDuration):mm\\:ss} | " +
                                 $"Maillard: {TimeSpan.FromSeconds(score.MaillardDuration):mm\\:ss} | " +
                                 $"Development: {TimeSpan.FromSeconds(score.DevelopmentDuration):mm\\:ss}";

            if (score.Improvements.Count == 0)
            {
                score.Improvements.Add("Exzellenter Roast! Keine wesentlichen Verbesserungen nötig.");
            }

            return score;
        }

        // === Live-Phasen-Erkennung ===
        public enum RoastPhase
        {
            Idle,
            Charging,       // Bohnen eingeworfen, Temperatur fällt
            Drying,         // Feuchtigkeit verdampft, < 150°C
            Maillard,       // Bräunung, 150-FC
            FirstCrack,     // Exotherme Reaktion
            Development,    // Nach First Crack
            SecondCrack,    // Zweiter Crack (zu dunkel für die meisten)
            Cooling         // Abkühlung
        }

        public static RoastPhase DetectPhase(double currentTemp, double previousTemp, 
            double currentRoR, int secondsElapsed, int firstCrackSecond, double expectedFC, string state)
        {
            if (state == "cooling" || state == "idle") return RoastPhase.Cooling;
            if (state == "pre-heating" || state == "ready") return RoastPhase.Idle;

            // Charging: Temperatur fällt in den ersten 60s
            if (secondsElapsed < 60 && currentRoR < 0 && !double.IsNaN(currentRoR))
                return RoastPhase.Charging;

            // Nach First Crack
            if (firstCrackSecond > 0 && secondsElapsed > firstCrackSecond)
            {
                if (currentTemp > 235) return RoastPhase.SecondCrack;
                return RoastPhase.Development;
            }

            // First Crack Zone
            if (currentTemp >= expectedFC - 5 && currentTemp <= expectedFC + 10)
                return RoastPhase.FirstCrack;

            // Maillard: 150°C bis FC
            if (currentTemp >= 150)
                return RoastPhase.Maillard;

            // Drying
            if (currentTemp > 0)
                return RoastPhase.Drying;

            return RoastPhase.Idle;
        }

        public static string PhaseToString(RoastPhase phase)
        {
            switch (phase)
            {
                case RoastPhase.Charging: return "🫘 Charging";
                case RoastPhase.Drying: return "💧 Drying";
                case RoastPhase.Maillard: return "🟤 Maillard";
                case RoastPhase.FirstCrack: return "💥 First Crack!";
                case RoastPhase.Development: return "☕ Development";
                case RoastPhase.SecondCrack: return "⚠️ Second Crack!";
                case RoastPhase.Cooling: return "❄️ Cooling";
                default: return "⏸️ Idle";
            }
        }

        public static System.Drawing.Color PhaseToColor(RoastPhase phase)
        {
            switch (phase)
            {
                case RoastPhase.Charging: return System.Drawing.Color.LightBlue;
                case RoastPhase.Drying: return System.Drawing.Color.SandyBrown;
                case RoastPhase.Maillard: return System.Drawing.Color.Chocolate;
                case RoastPhase.FirstCrack: return System.Drawing.Color.OrangeRed;
                case RoastPhase.Development: return System.Drawing.Color.DarkGreen;
                case RoastPhase.SecondCrack: return System.Drawing.Color.DarkRed;
                case RoastPhase.Cooling: return System.Drawing.Color.CornflowerBlue;
                default: return System.Drawing.Color.Gray;
            }
        }
    }
}
