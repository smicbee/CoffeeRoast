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

        static private double simulatedTemp { get; set; } = 0;
        static public bool simulation { get; set; } = false;
        static public bool running {  get; set; } = false;

        static public double fanSpeed { get; set; } = 0.0;
        static public double initFanSpeed { get; set; } = 100.0;
        static public string State { get; set; } = "idle";

        static Timer t = new Timer();

        public static void initialize()
        {
            t.Stop();

            t.Elapsed += timer1_Tick;
            t.Interval = deltaTime/1000;
            t.Start();

        }

        public static void prepareRoast()
        {
           
            State = "pre-heating";
            setPoint = 0;
        }

        public static void runCurve()
        {

            SerialCommunication.setFanSpeed(initFanSpeed / 100.0 * 255.0);
            pid = new PIDController();

            for (int i = 0; i < realCurve.Length; i++)
            {
                realCurve[i] = double.NaN;
                pid.pidvalues[i] = double.NaN;
                fanSpeedCurve[i] = double.NaN;
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
        static public double timeOffset = 0;
        static public Stopwatch elappsedSeconds;

        public static void abortRun()
        {
            running = false; setPoint = 0;
            if (elappsedSeconds != null)
            {
                elappsedSeconds.Stop();
                elappsedSeconds.Reset();
            }

            State = "cooling";
        }

        static public int stopAt = -1;

        static private void timer1_Tick(object sender, EventArgs e)
        {
            t.Stop();
            int second = 0;
            if (elappsedSeconds != null)
            {
             second =  Convert.ToInt32(elappsedSeconds.ElapsedMilliseconds / 1000 + timeOffset);
            }

            second = Math.Max(0, second);
            second = Math.Min(1200,second);

            if (second >= roastingProfile.Count() || (stopAt > -1 && second >= stopAt)) { second = roastingProfile.Count() - 1; abortRun(); }


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
                setPoint = 0;
       
                if (measuredTemp > 0 )
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
            else if (State == "cooling")
            {
                SerialCommunication.setSetpoint(0.0);
                
                if (measuredTemp < 60)
                {
                    SerialCommunication.setFanSpeed(0);
                    State = "idle";
                }
                else
                {
                    fanSpeed = FanControl.CalculateFanSpeed(measuredTemp, initFanSpeed / 100 * 255);
                    SerialCommunication.setFanSpeed(fanSpeed);
                }

            }
            else { }

            double controlSignal;
            if (pid == null || State != "running")
            {
                controlSignal= setPoint;
            }
            else { 
                controlSignal = pid.Update(second,measuredTemp);
               // Console.WriteLine(controlSignal.ToString());

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

            realCurve[second] = measuredTemp;
            t.Start();
        }


        static private double[] variables = new double[10];
        static public  PIDController pid;

    }


}
