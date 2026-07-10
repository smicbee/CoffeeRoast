using System;
using System.Media;
using System.Threading.Tasks;

namespace iRoastControl
{
    public static class AlertSystem
    {
        public enum AlertType
        {
            RoastLevelReached,
            FirstCrackExpected,
            RoRWarning,
            RoastComplete,
            CoolingComplete
        }

        /// <summary>
        /// Spielt einen akustischen Alert asynchron ab (blockiert nicht den aufrufenden Thread).
        /// Verwendet Windows System-Sounds, keine externen Abhängigkeiten nötig.
        /// </summary>
        public static void PlayAlert(AlertType type)
        {
            Task.Run(() =>
            {
                try
                {
                    switch (type)
                    {
                        case AlertType.RoastLevelReached:
                            // 3x kurzer Beep
                            for (int i = 0; i < 3; i++)
                            {
                                Console.Beep(1000, 200);
                                System.Threading.Thread.Sleep(100);
                            }
                            break;

                        case AlertType.FirstCrackExpected:
                            // Aufsteigender Doppelton
                            Console.Beep(800, 300);
                            Console.Beep(1200, 300);
                            break;

                        case AlertType.RoRWarning:
                            // Schneller Warn-Beep
                            for (int i = 0; i < 5; i++)
                            {
                                Console.Beep(1500, 100);
                                System.Threading.Thread.Sleep(50);
                            }
                            break;

                        case AlertType.RoastComplete:
                            // Aufsteigende Melodie
                            Console.Beep(523, 200); // C
                            Console.Beep(659, 200); // E
                            Console.Beep(784, 200); // G
                            Console.Beep(1047, 400); // C (hoch)
                            break;

                        case AlertType.CoolingComplete:
                            // Kurzer tiefer Beep
                            Console.Beep(440, 500);
                            break;
                    }
                }
                catch
                {
                    // Beep ist auf manchen Systemen nicht verfügbar
                    SystemSounds.Beep.Play();
                }
            });
        }
    }
}
