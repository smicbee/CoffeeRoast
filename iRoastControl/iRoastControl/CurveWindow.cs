using Numerics.NET;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.IO.Ports;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using ZedGraph;

namespace Artisan
{
    public partial class CurveWindow : Form
    {
        public CurveWindow()
        {
            InitializeComponent();
        }

        private void CurveWindow_Load(object sender, EventArgs e)
        {
            foreach (var i in SerialPort.GetPortNames())
            {
                comboBox1.Items.Add(i);
            }

            for (int i = 0; i < ControlClass.realCurve.Length; i++)
            {
                ControlClass.realCurve[i] = double.NaN;
            }
            ControlClass.generateDefaultCurve();
            drawActiveCurve();

            timer1.Interval = 500;
            timer1.Enabled = true;
            timer1.Tick += timer1_Tick;
            timer1.Start();
        }

        public void drawActiveCurve()
        {

            if (ControlClass.activeCurve != null)
            {

                // Get a reference to the GraphPane
                GraphPane myPane = zedGraphControl1.GraphPane;

                // Set Titles
                myPane.Title.Text = "";
                myPane.XAxis.Title.Text = "Time / s";
                myPane.YAxis.Title.Text = "Temperatur / °C";

                double[] xList = new double[ControlClass.activeCurve.Count()];

                for (int i = 0; i < xList.Length; i++)
                {
                    xList[i] = i;
                }


                realCurveY = ControlClass.realCurve;
                // Create a curve (Line graph)

         

                if (realCurve == null)
                {
                    realCurve = myPane.AddCurve("Measured Temp.", xList , realCurveY, System.Drawing.Color.Red, SymbolType.None);
                    realCurve.Line.Width = 2;
                    myPane.AxisChange();
                }
                else
                {
                    for (int i = 0; i < ControlClass.realCurve.Count(); i++)
                    {
                        realCurve.Points[i].Y = ControlClass.realCurve[i];
                    }
                }

                if (activeCurve == null)
                {
                    activeCurve = myPane.AddCurve("Recipe", xList, ControlClass.activeCurve, System.Drawing.Color.Blue, SymbolType.None);
                    activeCurve.Line.Width = 2;
                    myPane.AxisChange();
                }
                else
                {
                    for (int i = 0; i < ControlClass.activeCurve.Count(); i++)
                    {
                        activeCurve.Points[i].Y = ControlClass.activeCurve[i];
                    }

                }
                zedGraphControl1.Invalidate();
            }
        }

        double[] realCurveY;

        LineItem activeCurve;
        LineItem realCurve;

        private void zedGraphControl1_Load(object sender, EventArgs e)
        {

          

        }



        private void button1_Click(object sender, EventArgs e)
        {
            if (ControlClass.State == "idle")
            {
                ControlClass.preHeat();
                button1.BackColor = Color.Red;
                button1.Text = "pre-heating";
            }
            else if (ControlClass.State == "ready")
            {
                ControlClass.runCurve();
                button1.BackColor = Color.Yellow;
                button1.Text = "Run";
            }
            else
            {
                ControlClass.abortRun();
                button1.BackColor = Color.Transparent;
            }
        }

        private void timer1_Tick(object sender, EventArgs e)
        {
            timer1.Stop();
            drawActiveCurve();
            updateButton();


            label1.Text = "Current: " + Math.Round(ControlClass.measuredTemp).ToString() + "°C";
            label2.Text = "SetPoint: " + Math.Round(ControlClass.setPoint).ToString() + "°C";

            if (ControlClass.elappsedSeconds == null) { label3.Text = ""; }
            else { label3.Text = "Elappsed Time: " + TimeSpan.FromSeconds(ControlClass.elappsedSeconds.ElapsedMilliseconds / 1000).ToString(@"mm\:ss"); }

            timer1.Start();
        }


        private void updateButton()
        {
            if (ControlClass.State == "idle")
            {
                button1.BackColor = Color.Transparent;
                button1.Text = "Start";
            }
            else if (ControlClass.State == "pre-heating")
            {
                button1.BackColor = Color.Red;
                button1.Text = "Please wait...";
            }
            else if (ControlClass.State == "ready")
            {
                button1.BackColor = Color.LightGreen;
                button1.Text = "Run";
            }
            else
            {
               
            }
        }

        private void checkBox1_CheckedChanged(object sender, EventArgs e)
        {
            ControlClass.simulation = checkBox1.Checked;
        }

        private void comboBox1_SelectedIndexChanged(object sender, EventArgs e)
        {
            SerialCommunication.serialPort = new SerialPort(comboBox1.Text, SerialCommunication.baudRate)
            {
                Parity = Parity.None,
                StopBits = StopBits.One,
                DataBits = 8,
                Handshake = Handshake.None,
                ReadTimeout = 5000,
                WriteTimeout = 500
            };
        }
    }
}
