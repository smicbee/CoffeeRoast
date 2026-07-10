using iRoastControl;
using MathNet.Numerics;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Linq;
using System.Security;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Timers;

namespace Artisan
{
    public static class ControlClass
    {

        static public double deltaTime { get; set; } = 0.5; // Time step in seconds
        static public double setPoint { get; set; } = 0; // Desired temperature
        static public double measuredTemp { get; set; } = 0;
        static public double preheatTargetTemp { get; set; } = 180;

        static private double simulatedTemp { get; set; } = 0;
        static public bool simulation { get; set; } = false;
      
        static public double fanSpeed { get; set; } = 0.0;
        static public double initFanSpeed { get; set; } = 100.0;
        static public string State { get; set; } = "idle";
        static public double expectedFirstCrack { get; set; } = 208.0;
        static public int firstCrackSecond { get; set; } = -1;

        static Timer t = new Timer();

        public static void initialize()
        {
            t.Stop();

            t.Elapsed -= timer1_Tick;
            t.Elapsed += timer1_Tick;
            t.Interval = deltaTime * 1000;
            t.Start();

        }

        public static void prepareRoast()
        {
            if (ControlClass.elappsedSeconds == null)
            {
                ControlClass.elappsedSeconds = new Stopwatch();
            }
            else
            {
                ControlClass.elappsedSeconds.Reset();
            }
            State = "pre-heating";
            setPoint = 0;
        }

        public static void runCurve()
        {

            SerialCommunication.setFanSpeed(initFanSpeed / 100.0 * 255.0);
            pid = new PIDController();
            stopAt = -1;
            firstCrackSecond = -1;

            if (simulation)
            {
                Simulation.Reset();
            }

            for (int i = 0; i < realCurve.Length; i++)
            {
                realCurve[i] = double.NaN;
                pid.pidvalues[i] = double.NaN;
                fanSpeedCurve[i] = double.NaN;
                rateOfRise[i] = double.NaN;
            }

            elappsedSeconds = new Stopwatch();
            State = "running";
         

            elappsedSeconds.Start();
        }



        public static void generateDefaultCurve()
        {
            List<PointF> targetPoints = new List<PointF>();
            targetPoints.Add(new PointF(0, 160));
            targetPoints.Add(new PointF(120, 90));
            targetPoints.Add(new PointF(240, 90));
            targetPoints.Add(new PointF(540, 140));
            targetPoints.Add(new PointF(660, 150));
            targetPoints.Add(new PointF(720, 160));
            targetPoints.Add(new PointF(780, 170));

            keyPoints = targetPoints;

        }

        public static void CalibrateCurve()
        {
            List<PointF> targetPoints = new List<PointF>();
            targetPoints.Add(new PointF(0, 150));
            targetPoints.Add(new PointF(120, 150));
            targetPoints.Add(new PointF(240, 150));
            targetPoints.Add(new PointF(540, 150));
            targetPoints.Add(new PointF(660, 150));
            targetPoints.Add(new PointF(720, 150));
            targetPoints.Add(new PointF(780, 150));

            keyPoints = targetPoints;
          

        }



        private static List<PointF> _keyPoints;
        static public List<PointF> keyPoints
        {
            get
            {
                return _keyPoints;
            }
            set 
            {
                _keyPoints = value;                
                SplineInterpolator interpolator = new SplineInterpolator(_keyPoints);

                double[] curve = new double[1200];
                double[] derivative = new double[1200];

                for (int i = 0; i < curve.Count(); i++)
                {
                    curve[i] = interpolator.Interpolate(i);
                    if (i > 0)
                    {
                        derivative[i] = (curve[i] / curve[i - 1]);
                    }
                    else
                    {
                        derivative[i] = 1;
                    }
                }

                roastingProfile = curve;
                derivativeCurve = derivative;

                double[] timeSeries = new double[1200];
                for (int i = 0; i < timeSeries.Length; i++)
                {
                    timeSeries[i] = i;
                }


                ControlClass.pid = new PIDController();

            }
        }

        static public double[] derivativeCurve;
        static public double[] roastingProfile;
        static public double[] realCurve = new double[1200];
        static public double[] fanSpeedCurve = new double[1200];
        static public double[] rateOfRise = new double[1200];
        static public double timeOffset = 0;
        static public Stopwatch elappsedSeconds = new Stopwatch();
        static public double timeMultiplicator = 1;

        public static void abortRun()
        {
            setPoint = 0;
            AlertSystem.PlayAlert(AlertSystem.AlertType.RoastLevelReached);
            RoastLogger.SaveRoastLog(realCurve, roastingProfile, fanSpeedCurve, rateOfRise, pid != null ? pid.pidvalues : null, elappsedSeconds);
            stopAt = -1;
            State = "cooling";
        }

        static public int stopAt = -1;

        static private void timer1_Tick(object sender, EventArgs e)
        {
            t.Stop();
            if (roastingProfile == null)
            {
                generateDefaultCurve();
            }

            if (pid == null)
            {
                pid = new PIDController();
            }

            int requestedSecond = 0;
            if (elappsedSeconds != null)
            {
             requestedSecond =  Convert.ToInt32(elappsedSeconds.ElapsedMilliseconds * timeMultiplicator / 1000 + timeOffset );
            }

            int second = Math.Max(0, requestedSecond);
            second = Math.Min(roastingProfile.Length - 1,second);

            if (State != "idle" && (requestedSecond >= roastingProfile.Count() || (stopAt > -1 && requestedSecond >= stopAt))) { second = roastingProfile.Count() - 1; abortRun(); }


            if (State == "running")
            {                       
                setPoint = roastingProfile[second];            
                fanSpeed = FanControl.CalculateFanSpeed(measuredTemp, initFanSpeed/100*255);
                if (!simulation) { 
                SerialCommunication.setFanSpeed(fanSpeed);
                }
            }
            else if (State == "pre-heating")
            {
                SerialCommunication.setFanSpeed(initFanSpeed / 100.0 * 255.0);
                setPoint = preheatTargetTemp;
       
                if (measuredTemp >= preheatTargetTemp )
                {
                    State = "ready";
                  
                }
            }else if (State == "idle")
            {
                if (measuredTemp < 60 )
                {
                    SerialCommunication.setFanSpeed(0);
                }
                else
                {
                    fanSpeed = FanControl.CalculateFanSpeed(measuredTemp, initFanSpeed / 100 * 255);
                    SerialCommunication.setFanSpeed(fanSpeed);
                }
            }
            else if (State == "failsafe"){
                setPoint = 0;
                fanSpeed = 255;

                if (!simulation)
                {
                    SerialCommunication.setSetpoint(setPoint);
                    SerialCommunication.setFanSpeed(fanSpeed);
                }

            }
            else if (State == "cooling")
            {
                setPoint = 0.0;
                if (!simulation)
                {
                    SerialCommunication.setSetpoint(setPoint);
                }

                if (measuredTemp < 60)
                {
                    fanSpeed = 0;

                    if (!simulation)
                    {
                        SerialCommunication.setFanSpeed(fanSpeed);
                    }

                    if (elappsedSeconds != null)
                    {
                        elappsedSeconds.Stop();
                    }

                    State = "idle";
                    AlertSystem.PlayAlert(AlertSystem.AlertType.CoolingComplete);
                }
                else
                {
                    fanSpeed = FanControl.CalculateFanSpeed(measuredTemp, initFanSpeed / 100 * 255);

                    if (!simulation)
                    {
                        SerialCommunication.setFanSpeed(fanSpeed);
                    }
                }

            }
            else if (State == "calibration")
            {
                if (autoTuner != null)
                {
                    var tuneResult = autoTuner.Update(measuredTemp);
                    setPoint = tuneResult.HeaterPWM;
                    fanSpeed = tuneResult.FanPWM;
                    
                    if (!simulation)
                    {
                        SerialCommunication.setFanSpeed(fanSpeed);
                    }

                    if (autoTuner.State == PIDAutoTuner.TuningState.Finished || autoTuner.State == PIDAutoTuner.TuningState.Aborted)
                    {
                        State = "cooling";
                    }
                }
            }

            double controlSignal;
            if (pid == null)
            {
                controlSignal = Math.Max(0, Math.Min(255, setPoint));
            }
            else if (State == "running")
            {
                controlSignal = pid.Update(second, measuredTemp);
            }
            else
            {
                controlSignal = pid.Set(second, setPoint);
            }


            if (!simulation) { 
            SerialCommunication.setSetpoint(controlSignal);
            }
            System.Threading.Thread.Sleep(200);
            

            if (simulation)
            {
                Simulation.SetHeatingPower(controlSignal);
                measuredTemp = Simulation.GetTemperature(); 
            }
            else
            {
                measuredTemp = SerialCommunication.getTemperature() ;
            }

            if (simulation)
            {
                fanSpeedCurve[second] = fanSpeed;
            }
            else
            {
                var realFanSpeed = SerialCommunication.getFanSpeed();
                fanSpeedCurve[second] = realFanSpeed;
            }

            if (State != "idle")
            {
                realCurve[second] = measuredTemp;

                // Rate of Rise berechnen (°C/min, 30s rolling window)
                int rorWindow = 30;
                if (second >= rorWindow && !double.IsNaN(realCurve[second]) && !double.IsNaN(realCurve[second - rorWindow]))
                {
                    rateOfRise[second] = (realCurve[second] - realCurve[second - rorWindow]) / (rorWindow / 60.0);
                }

                // First Crack Erkennung
                if (firstCrackSecond == -1 && measuredTemp >= expectedFirstCrack && State == "running")
                {
                    firstCrackSecond = second;
                    AlertSystem.PlayAlert(AlertSystem.AlertType.FirstCrackExpected);
                }
            }
            t.Start();
        }


        static private double[] variables = new double[10];
        static public  PIDController pid;
        static public PIDAutoTuner autoTuner;

    }


}
