using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace iRoastControl
{
    using System;

    public static class Simulation
    {
        private static double _maxTemperature = 250.0; // °C
        private static double _roomTemperature = 30.0; // °C
        private static double _thermalEnergy = 0.0; // Arbitrary units
        private static double _heatingPower = 0.0; // 0 - 1000W scaled to 0.0 - 1.0

        private static double _heatCapacity = 20000.0; // Arbitrary "thermal mass"
        private static double _heatLossFactor = 0.0001; // Cooling rate per tick

        private static DateTime _lastUpdateTime = DateTime.Now;

        public static void SetHeatingPower(double power)
        {
            _heatingPower = power/255.0;

            if (_heatingPower > 1) { _heatingPower = 1;}
            if (_heatingPower < 0) { _heatingPower = 0;}
        }

        public static double GetTemperature()
        {
            Update(); // Ensure temperature is updated before returning
            return _roomTemperature + (_thermalEnergy / _heatCapacity) * (_maxTemperature - _roomTemperature);
        }

        private static void Update()
        {

            DateTime now = DateTime.Now;
            double deltaTime = (now - _lastUpdateTime).TotalSeconds;
            _lastUpdateTime = now;

            if (deltaTime <= 0) return;

            double inputEnergy = 1000.0 * _heatingPower * deltaTime; // Energy input (Joules)
            double currentTemperature = _roomTemperature + (_thermalEnergy / _heatCapacity) * (_maxTemperature - _roomTemperature); ; // Before updating energy
            double excessTemp = currentTemperature - _roomTemperature;

            double heatLoss = excessTemp * _heatLossFactor * deltaTime * _heatCapacity;

            _thermalEnergy += inputEnergy;
            _thermalEnergy -= heatLoss;
            _thermalEnergy = Math.Max(0.0, _thermalEnergy); // Clamp to avoid negative energy
        }
    }

}
