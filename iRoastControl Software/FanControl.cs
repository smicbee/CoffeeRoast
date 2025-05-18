using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace iRoastControl
{
    public static class FanControl
    {
        public static int CalculateFanSpeed(double currentTemperature, double initialSpeed)
        {
            // Target minimum speed: 80% of initial speed or 128, whichever is higher
            double minSpeed = Math.Max(128, initialSpeed * 0.8);

            if (currentTemperature <= 100)
            {
                return (int)Math.Round(initialSpeed);
            }

            if (currentTemperature >= 230)
            {
                return (int)Math.Round(minSpeed);
            }

            // Quadratic drop-off: progress increases faster as temperature rises
            double progress = Math.Pow(currentTemperature - 100, 2) / Math.Pow(130, 2);
            double fanSpeed = initialSpeed - (initialSpeed - minSpeed) * progress;

            return (int)Math.Round(fanSpeed);
        }
    }
}
