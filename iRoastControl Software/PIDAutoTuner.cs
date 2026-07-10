using System;
using System.Collections.Generic;

namespace iRoastControl
{
    public class PIDAutoTuner
    {
        public enum TuningState
        {
            Idle,
            Preheating,
            Equilibrium,
            StepResponse,
            Finished,
            Aborted
        }

        public TuningState State { get; private set; } = TuningState.Idle;
        
        // Settings
        public double PreheatTarget { get; set; } = 100; // Target temp to stabilize before step
        public double MaxSafeTemp { get; set; } = 240;   // Safety abort
        public int EquilibriumTimeSeconds { get; set; } = 60; // How long to hold preheat temp
        public double FanSpeedPct { get; set; } = 100;   // Fan speed during test
        
        // Calculated PID Values
        public double Kp { get; private set; }
        public double Ki { get; private set; }
        public double Kd { get; private set; }

        public string StatusMessage { get; private set; } = "Ready";

        // Internal Tuning Data
        private int _elapsedSeconds = 0;
        private int _equilibriumCounter = 0;
        
        // Step Response Data
        private double _stepStartTemp;
        private int _stepStartTime;
        private double _deadTimeL = -1;
        private double _maxSlopeR = 0;
        
        private List<double> _tempHistory;

        public event Action TuningCompleted;
        public event Action<string> StatusUpdated;

        public PIDAutoTuner()
        {
            _tempHistory = new List<double>();
        }

        public void Start()
        {
            SetState(TuningState.Preheating);
            _elapsedSeconds = 0;
            _equilibriumCounter = 0;
            _tempHistory.Clear();
            _deadTimeL = -1;
            _maxSlopeR = 0;
            UpdateStatus("Heize auf Basistemperatur auf...");
        }

        public void Abort(string reason = "Abgebrochen durch Benutzer.")
        {
            SetState(TuningState.Aborted);
            UpdateStatus("Test abgebrochen: " + reason);
        }

        // Returns current Heater Power (0-255 PWM) and Fan Speed (0-255 PWM)
        public (double HeaterPWM, double FanPWM) Update(double currentTemp)
        {
            _elapsedSeconds++;
            _tempHistory.Add(currentTemp);

            double fanPWM = Math.Min(255, Math.Max(0, FanSpeedPct / 100.0 * 255.0));
            double heaterPWM = 0;

            if (currentTemp >= MaxSafeTemp && State != TuningState.Aborted)
            {
                Abort("Maximale Sicherheitstemperatur erreicht (" + MaxSafeTemp + "°C).");
            }

            switch (State)
            {
                case TuningState.Preheating:
                    // Einfacher P-Regler zum Vorheizen
                    if (currentTemp < PreheatTarget - 2) heaterPWM = 255;
                    else if (currentTemp < PreheatTarget) heaterPWM = 100;
                    else
                    {
                        heaterPWM = 0; // oder halten wir mit geringer Leistung
                        if (currentTemp >= PreheatTarget)
                        {
                            SetState(TuningState.Equilibrium);
                            UpdateStatus("Warte auf thermisches Gleichgewicht...");
                        }
                    }
                    // Kleine Halte-Leistung in Eq-Nähe
                    if (currentTemp >= PreheatTarget - 5 && currentTemp <= PreheatTarget + 5)
                    {
                        heaterPWM = 50; // Annahme 50 PWM hält ca 100°C
                    }
                    break;

                case TuningState.Equilibrium:
                    // Versuche Temperatur konstant zu halten
                    if (currentTemp < PreheatTarget) heaterPWM = 60;
                    else heaterPWM = 30;

                    _equilibriumCounter++;
                    if (_equilibriumCounter >= EquilibriumTimeSeconds)
                    {
                        // Starte Sprungantwort
                        _stepStartTemp = currentTemp;
                        _stepStartTime = _elapsedSeconds;
                        SetState(TuningState.StepResponse);
                        UpdateStatus("Step Response (100% Heizung) läuft. Messe System...");
                    }
                    break;

                case TuningState.StepResponse:
                    heaterPWM = 255; // Volle Leistung!

                    AnalyzeStepResponse(currentTemp);

                    // Test beenden, wenn ein stabiler Trend gefunden wurde und Temperatur um +50°C gestiegen ist
                    if (currentTemp >= _stepStartTemp + 50)
                    {
                        FinishTuning();
                    }
                    break;

                case TuningState.Finished:
                case TuningState.Aborted:
                case TuningState.Idle:
                    heaterPWM = 0;
                    break;
            }

            return (heaterPWM, fanPWM);
        }

        private void AnalyzeStepResponse(double currentTemp)
        {
            int timeSinceStep = _elapsedSeconds - _stepStartTime;
            if (timeSinceStep < 5) return; // Zu wenig Daten

            // Berechne RoR (Rate of Rise in °C/min) für die letzten 5 Sekunden
            double temp5sAgo = _tempHistory[_elapsedSeconds - 5];
            double currentSlope = (currentTemp - temp5sAgo) * (60.0 / 5.0);

            // Finde Max Slope R
            if (currentSlope > _maxSlopeR)
            {
                _maxSlopeR = currentSlope;
            }

            // Finde Dead Time L (Zeit bis der Anstieg signifikant > 10% der max Slope ist)
            // oder definieren wir es als Schnittpunkt der Tangente mit der Starttemperatur
            if (_deadTimeL == -1 && currentSlope > 5.0)
            {
                // Eine einfache Annäherung an L:
                // Wenn RoR > 5°C/min erreicht ist, schätzen wir L
                _deadTimeL = timeSinceStep;
            }
        }

        private void FinishTuning()
        {
            SetState(TuningState.Finished);

            // Sicherheitschecks
            if (_maxSlopeR <= 0 || _deadTimeL <= 0)
            {
                UpdateStatus("Test fehlgeschlagen: Keine auswertbare Steigung gefunden.");
                return;
            }

            // Ziegler-Nichols (Open Loop / Reaction Curve) Method für PID Regelung
            // L = Verzögerungszeit / Dead Time in Minuten! (Wir haben Sekunden gemessen, also in Minuten umrechnen)
            double L_min = _deadTimeL / 60.0;
            // R = Steigung in °C / min
            // Gain K des Systems: Wie viel Temperaturzuwachs (prozentual) schafft 100% Leistung? 
            // In der einfachen Reaction Rate Methode:
            // Kp = 1.2 / (R * L_min)
            // Ti = 2 * L_min
            // Td = 0.5 * L_min

            // Da unser PID Controller mit Ki und Kd statt Ti und Td arbeitet:
            // Ki = Kp / Ti
            // Kd = Kp * Td

            Kp = Math.Max(0.1, 1.2 / (_maxSlopeR * L_min));
            
            double Ti = 2.0 * L_min;
            double Td = 0.5 * L_min;

            if (Ti > 0) Ki = Kp / Ti;
            else Ki = 0;

            Kd = Kp * Td;

            // Skalierung für unser spezifisches System (oft muss Z-N für Kastenröster runter skaliert werden)
            Kp = Math.Round(Kp * 0.1, 2); // Kp um Faktor 10 verringern für feineres Tastverhältnis
            Ki = Math.Round(Ki * 0.05, 4);
            Kd = Math.Round(Kd * 0.1, 2);

            UpdateStatus($"Abgeschlossen! Lag: {_deadTimeL}s, MaxSlope: {Math.Round(_maxSlopeR, 1)}°C/m");
            TuningCompleted?.Invoke();
        }

        private void SetState(TuningState newState)
        {
            State = newState;
        }

        private void UpdateStatus(string message)
        {
            StatusMessage = message;
            StatusUpdated?.Invoke(message);
        }
    }
}
