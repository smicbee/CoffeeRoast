using Artisan;
using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;

namespace iRoastControl
{
    /// <summary>
    /// Speichert automatisch einen Roast-Log als CSV nach Abschluss jedes Roasts.
    /// Ermöglicht Vergleiche zwischen Roasts und hilft beim Profil-Tuning.
    /// </summary>
    public static class RoastLogger
    {
        private static string GetLogFolder()
        {
            var folder = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "iRoastControl", "RoastLogs");

            if (!Directory.Exists(folder))
            {
                Directory.CreateDirectory(folder);
            }

            return folder;
        }

        /// <summary>
        /// Speichert den aktuellen Roast als CSV-Datei.
        /// </summary>
        public static void SaveRoastLog(double[] realCurve, double[] targetCurve, 
            double[] fanCurve, double[] rorCurve, double[] pidValues, Stopwatch elapsed)
        {
            try
            {
                if (realCurve == null || elapsed == null) return;

                int duration = Convert.ToInt32(elapsed.ElapsedMilliseconds / 1000);
                if (duration <= 0) return;

                var logFolder = GetLogFolder();
                var timestamp = DateTime.Now.ToString("yyyy-MM-dd_HH-mm-ss");
                var fileName = Path.Combine(logFolder, $"{timestamp}_roast.csv");

                var sb = new StringBuilder();
                
                // Header
                sb.AppendLine("Second,TargetTemp,RealTemp,FanSpeed,RateOfRise,PID");

                // Nur bis zur tatsächlichen Roast-Dauer schreiben
                int maxSeconds = Math.Min(duration + 10, realCurve.Length);
                for (int i = 0; i < maxSeconds; i++)
                {
                    string targetTemp = (targetCurve != null && i < targetCurve.Length && !double.IsNaN(targetCurve[i])) 
                        ? targetCurve[i].ToString("F1", CultureInfo.InvariantCulture) : "";
                    string realTemp = !double.IsNaN(realCurve[i]) 
                        ? realCurve[i].ToString("F1", CultureInfo.InvariantCulture) : "";
                    string fan = (fanCurve != null && i < fanCurve.Length && !double.IsNaN(fanCurve[i])) 
                        ? fanCurve[i].ToString("F1", CultureInfo.InvariantCulture) : "";
                    string ror = (rorCurve != null && i < rorCurve.Length && !double.IsNaN(rorCurve[i])) 
                        ? rorCurve[i].ToString("F2", CultureInfo.InvariantCulture) : "";
                    string pid = (pidValues != null && i < pidValues.Length && !double.IsNaN(pidValues[i])) 
                        ? pidValues[i].ToString("F1", CultureInfo.InvariantCulture) : "";

                    sb.AppendLine($"{i},{targetTemp},{realTemp},{fan},{ror},{pid}");
                }

                File.WriteAllText(fileName, sb.ToString());
                Console.WriteLine($"Roast log saved to: {fileName}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error saving roast log: {ex.Message}");
            }
        }
    }
}
