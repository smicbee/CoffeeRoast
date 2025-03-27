using MathNet.Numerics;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Linq;
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

        static public string State { get; set; } = "idle";

        static Timer t = new Timer();
        public static void preHeat()
        {
           
            t.Elapsed += timer1_Tick;
            t.Interval = 500;
            t.Start();

            State = "pre-heating";
            setPoint = 180;
        }

        public static void runCurve()
        {
            for (int i = 0; i < realCurve.Length; i++)
            {
                realCurve[i] = double.NaN;
            }

            elappsedSeconds = new Stopwatch();
            State = "running";
         

            elappsedSeconds.Start();
        }

        public static void generateDefaultCurve()
        {
            List<PointF> targetPoints = new List<PointF>();
            targetPoints.Add(new PointF(0, 180));
            targetPoints.Add(new PointF(120, 107));
            targetPoints.Add(new PointF(240, 120));
            targetPoints.Add(new PointF(540, 175));
            targetPoints.Add(new PointF(660, 180));
            targetPoints.Add(new PointF(720, 185));
            targetPoints.Add(new PointF(780, 190));

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

                double[] curve = new double[800];

                for (int i = 0; i < 800; i++)
                {
                    curve[i] = interpolator.Interpolate(i);
                }

                activeCurve = curve;
            }
        }
        
        static public double[] activeCurve;
        static public double[] realCurve = new double[800];

        static public Stopwatch elappsedSeconds;

        public static void abortRun()
        {
            running = false; setPoint = 0;
            if (elappsedSeconds != null)
            {
                elappsedSeconds.Stop();
                elappsedSeconds.Reset();
            }

            State = "idle";
        }
            

        static private void timer1_Tick(object sender, EventArgs e)
        {
            int second = 0;
            if (elappsedSeconds != null)
            {
             second =  (int)(elappsedSeconds.ElapsedMilliseconds / 1000);
            }
            if (State == "running")
            {
                setPoint = activeCurve[second];

                if (second >= activeCurve.Count()) { abortRun(); }

            }
            else if (State == "pre-heating")
            {
                setPoint = 180;
       
                if (measuredTemp > 179 )
                {
                    State = "ready";
                  
                }
            }
            else { }

            double controlSignal = pid.Compute(setPoint, measuredTemp, deltaTime);

            SerialCommunication.setSetpoint(controlSignal);
            measuredTemp = SerialCommunication.getTemperature();

            if (simulation)
            {
                measuredTemp = simulatedTemp + (controlSignal - 10) * 0.2;
                simulatedTemp = measuredTemp;
            }

            realCurve[second] = measuredTemp;

        }


        static private double[] variables = new double[10];
        static private PIDController pid = new PIDController(5, 0.05, 0.0, 0, 255);

    }


}
