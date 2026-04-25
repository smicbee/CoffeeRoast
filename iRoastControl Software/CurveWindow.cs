using iRoastControl;
using MathNet.Numerics;
using Numerics.NET;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.IO.Ports;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Drawing.Drawing2D;
using ZedGraph;

namespace Artisan
{
    public partial class CurveWindow : Form
    {
        public CurveWindow()
        {
            InitializeComponent();
           
        }

        void loadRecipes()
        {
            comboBox2.Items.Clear();
            if (!Directory.Exists("./Recipes/"))
            {
                return;
            }

            var kproFiles = Directory.GetFiles("./Recipes/", "*.kpro").Select(o => Path.GetFileNameWithoutExtension(o.ToString())).ToArray();

            if (kproFiles.Length == 0)
            {
                return;
            }

            comboBox2.Items.AddRange(kproFiles.ToArray());
            comboBox2.Text = comboBox2.Items[0].ToString();

        }


        private void CurveWindow_Load(object sender, EventArgs e)
        {
      
       
            for (int i = 0; i < ControlClass.realCurve.Length; i++)
            {
                ControlClass.realCurve[i] = double.NaN;
            }
            ControlClass.generateDefaultCurve();
            drawActiveCurve();

            timer1.Interval = 500;
            timer1.Enabled = true;
            timer1.Start();

            ControlClass.initialize();
            loadRecipes();

            cmbDropMode.SelectedIndex = 0; // default to Time
            chkAutoDrop.Checked = false;
            txtDropTarget.Text = "600"; // default 10 minutes

            loadSettings();
            resetView();
        }

        private string GetSettingsFolder()
        {
            return Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "iRoastControl");
        }

        public void loadSettings()
        {
            var settingsFolder = GetSettingsFolder();

            if (!Directory.Exists(settingsFolder))
            {
                Directory.CreateDirectory(settingsFolder);
            }

            var settingsPath = Path.Combine(settingsFolder, "default.roast");

            // Migration: alte Settings aus %TEMP% übernehmen
            if (!File.Exists(settingsPath))
            {
                var oldPath = Path.Combine(Path.GetTempPath(), "iRoastControl", "default.roast");
                if (File.Exists(oldPath))
                {
                    try { File.Copy(oldPath, settingsPath); } catch { }
                }
            }

            if (File.Exists(settingsPath))
            {

                SettingSaveFile s = Newtonsoft.Json.JsonConvert.DeserializeObject<SettingSaveFile>(File.ReadAllText(settingsPath));
                ThemeManager.IsDarkMode = s.isDarkMode;
                ThemeManager.ApplyTheme(this);

                if (s.Recipe != ".kpro") {
                textBox2.Text = (s.defaultFanSpeed.ToString());
                comboBox2.Text = Path.GetFileNameWithoutExtension(s.Recipe);
                var recipePath = "./Recipes/" + (s.Recipe);
                if (File.Exists(recipePath))
                {
                    readFile(recipePath);
                }
                zedGraphControl1.Refresh();
                }
            }
        }
        private void chkAutoDrop_CheckedChanged(object sender, EventArgs e)
        {
            UpdateDropTarget();
        }

        private void cmbDropMode_SelectedIndexChanged(object sender, EventArgs e)
        {
            UpdateDropTarget();
        }

        private void txtDropTarget_TextChanged(object sender, EventArgs e)
        {
            UpdateDropTarget();
        }

        private void UpdateDropTarget()
        {
            if (chkAutoDrop.Checked)
            {
                if (double.TryParse(txtDropTarget.Text, out double val))
                {
                    if (cmbDropMode.SelectedItem.ToString().Contains("Time"))
                    {
                        ControlClass.stopAt = (int)val;
                    }
                    else
                    {
                        ControlClass.stopAt = -1; // Temp based
                    }
                }
                else
                {
                    ControlClass.stopAt = -1;
                }
            }
            else
            {
                ControlClass.stopAt = -1;
            }
        }



        public void drawActiveCurve()
        {

            if (ControlClass.roastingProfile != null)
            {

                // Get a reference to the GraphPane
                GraphPane myPane = zedGraphControl1.GraphPane;

                // Set Titles
                myPane.Title.Text = "";
                myPane.XAxis.Title.Text = "Time / s";
                myPane.YAxis.Title.Text = "Temperatur / °C";

                double[] xList = new double[ControlClass.roastingProfile.Count()];

                for (int i = 0; i < xList.Length; i++)
                {
                    xList[i] = i;
                }


                realCurveY = ControlClass.realCurve;
                // Create a curve (Line graph)

                if (realCurve == null)
                {
                    realCurve = myPane.AddCurve("Measured Temp.", xList, realCurveY, System.Drawing.Color.Red, SymbolType.None);
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

                if (keyPointCurve == null)
                {
                    double[] keyPointsX = new double[ControlClass.keyPoints.Count()];
                    double[] keyPointsY = new double[ControlClass.keyPoints.Count()];


                    keyPointCurve = myPane.AddCurve("Points", keyPointsX, keyPointsY, System.Drawing.Color.Blue, SymbolType.Circle);
                    keyPointCurve.Line.Width = 0;
                    keyPointCurve.Line.Color = Color.Transparent;
                    myPane.AxisChange();
                }
                else
                {
                    keyPointCurve.Symbol.Size = 3;
                    double[] keyPointsX = new double[ControlClass.keyPoints.Count()];
                    double[] keyPointsY = new double[ControlClass.keyPoints.Count()];

                    while (keyPointCurve.Points.Count > ControlClass.keyPoints.Count())
                    {
                        keyPointCurve.RemovePoint(0);
                    }
                    while (keyPointCurve.Points.Count < ControlClass.keyPoints.Count())
                    {
                        keyPointCurve.AddPoint(new PointPair());
                    }



                    for (int i = 0; i < ControlClass.keyPoints.Count(); i++)
                    {
                        keyPointCurve.Points[i].X = ControlClass.keyPoints[i].X;
                        keyPointCurve.Points[i].Y = ControlClass.keyPoints[i].Y;
                    }
                }

                if (activeCurve == null)
                {
                    activeCurve = myPane.AddCurve("Recipe", xList, ControlClass.roastingProfile, System.Drawing.Color.Blue, SymbolType.None);
                    activeCurve.Line.Width = 2;
                    myPane.AxisChange();
                }
                else
                {
                    for (int i = 0; i < ControlClass.roastingProfile.Count(); i++)
                    {
                        activeCurve.Points[i].Y = ControlClass.roastingProfile[i];
                    }

                }





                if (ControlClass.pid != null)
                {
                    if (pidLevels == null)
                    {
                        pidLevels = myPane.AddCurve("PID", xList, ControlClass.pid.pidvalues, System.Drawing.Color.LightGray, SymbolType.None);
                        pidLevels.Line.Width = 2;
                        myPane.AxisChange();
                    }
                    else
                    {
                        for (int i = 0; i < ControlClass.pid.pidvalues.Count(); i++)
                        {
                            pidLevels.Points[i].Y = ControlClass.pid.pidvalues[i];
                        }
                    }
                }



                if (ControlClass.fanSpeedCurve != null)
                {
                    if (fanCurve == null)
                    {
                        fanCurve = myPane.AddCurve("Fan", xList, ControlClass.fanSpeedCurve, System.Drawing.Color.LightGreen, SymbolType.None);
                        fanCurve.Line.Width = 2;
                        myPane.AxisChange();
                    }
                    else
                    {
                        for (int i = 0; i < ControlClass.fanSpeedCurve.Count(); i++)
                        {
                            fanCurve.Points[i].Y = ControlClass.fanSpeedCurve[i];
                        }
                    }
                }
                // Rate of Rise Kurve (auf Y2Axis)
                if (ControlClass.rateOfRise != null)
                {
                    // Y2Axis einrichten
                    myPane.Y2Axis.IsVisible = true;
                    myPane.Y2Axis.Title.Text = "RoR / °C/min";
                    myPane.Y2Axis.Scale.Min = 0;
                    myPane.Y2Axis.Scale.Max = 30;
                    myPane.Y2Axis.Scale.FontSpec.FontColor = Color.DarkOrange;
                    myPane.Y2Axis.Title.FontSpec.FontColor = Color.DarkOrange;

                    if (rorCurve == null)
                    {
                        rorCurve = myPane.AddCurve("RoR", xList, ControlClass.rateOfRise, Color.DarkOrange, SymbolType.None);
                        rorCurve.Line.Width = 2;
                        rorCurve.Line.Style = DashStyle.Dash;
                        rorCurve.IsY2Axis = true;
                        myPane.AxisChange();
                    }
                    else
                    {
                        for (int i = 0; i < ControlClass.rateOfRise.Length; i++)
                        {
                            rorCurve.Points[i].Y = ControlClass.rateOfRise[i];
                        }
                    }
                }

                // First Crack Temperatur-Linie (horizontal)
                if (ControlClass.expectedFirstCrack > 0)
                {
                    // Alte FC-Linie entfernen und neu zeichnen
                    if (fcLine != null)
                    {
                        myPane.CurveList.Remove(fcLine);
                    }
                    double[] fcX = new double[] { 0, 1199 };
                    double[] fcY = new double[] { ControlClass.expectedFirstCrack, ControlClass.expectedFirstCrack };
                    fcLine = myPane.AddCurve("FC @ " + ControlClass.expectedFirstCrack + "°C", fcX, fcY, Color.Magenta, SymbolType.None);
                    fcLine.Line.Width = 1;
                    fcLine.Line.Style = DashStyle.DashDot;
                }


                zedGraphControl1.Invalidate();
            }
        }

        double[] realCurveY;
        LineItem keyPointCurve;
        LineItem activeCurve;
        LineItem realCurve;

        LineItem pidLevels;
        LineItem fanCurve;
        LineItem rorCurve;
        LineItem fcLine;

        private void zedGraphControl1_Load(object sender, EventArgs e)
        {



        }

        private void dragEnter(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop)) e.Effect = DragDropEffects.Copy;
        }

        private void dragDrop(object sender, DragEventArgs e)
        {

            string[] files = (string[])e.Data.GetData(DataFormats.FileDrop);

            if (Path.GetExtension(files[0]) == ".roast")
            { 
                SettingSaveFile s =  Newtonsoft.Json.JsonConvert.DeserializeObject<SettingSaveFile>(File.ReadAllText(files[0]));
                ThemeManager.IsDarkMode = s.isDarkMode;
                ThemeManager.ApplyTheme(this);
                textBox2.Text = s.defaultFanSpeed.ToString();
                if (s.Recipe != comboBox2.Text + ".kpro")
                {
                    switch (MessageBox.Show("Your roast levels were defined for another recipe. Do you want to load the recipe?", "Load another recipe?", MessageBoxButtons.YesNo))
                        {
                        case DialogResult.Yes:
                            comboBox2.Text = s.Recipe;
                            readFile("./Recipes/" + s.Recipe);
                            break;
                        case DialogResult.No:
                            break;
                    }

                }

                zedGraphControl1.Refresh();
            }
            else
            {
                readFile(files[0]);
            }

        }

        void readFile(string filename)
        {
            try
            {

            string[] lines = File.ReadAllLines(filename);

            Dictionary<string, string> datadict = new Dictionary<string, string>();
            foreach (string line in lines)
            {
                var separatorIndex = line.IndexOf(':');
                if (separatorIndex < 0) continue;
                var key = line.Substring(0, separatorIndex);
                var value = line.Substring(separatorIndex + 1);

                datadict[key] = value;
            }

            double kp = Convert.ToDouble(datadict["roast_PID_Kp"],CultureInfo.InvariantCulture);
            //kp *= Convert.ToDouble(datadict["specific_heat_adj_multiplier_Kp"], CultureInfo.InvariantCulture);
            double ki = Convert.ToDouble(datadict["roast_PID_Ki"], CultureInfo.InvariantCulture);
            double kd = Convert.ToDouble(datadict["roast_PID_Kd"], CultureInfo.InvariantCulture);
            //kd *= Convert.ToDouble(datadict["specific_heat_adj_multiplier_Kd"], CultureInfo.InvariantCulture);
            string description = datadict["profile_description"].ToString().Replace(@"\v",Environment.NewLine);
            textBox1.Text = description;

            double targetInFuture = Convert.ToDouble(datadict["roast_target_in_future"], CultureInfo.InvariantCulture);
            double timeShift = Convert.ToDouble(datadict["roast_target_timeshift"], CultureInfo.InvariantCulture);
            double minRateOfRise = Convert.ToDouble(datadict["roast_min_desired_rate_of_rise"], CultureInfo.InvariantCulture);

            // Rezept-Metadaten speichern
            if (datadict.ContainsKey("expect_fc"))
            {
                ControlClass.expectedFirstCrack = Convert.ToDouble(datadict["expect_fc"], CultureInfo.InvariantCulture);
            }

            ControlClass.keyPoints.Clear();

            var roastProfilestr = datadict["roast_profile"].Split(',');
            List<PointF> roastProfile = new List<PointF>();
            for (int i = 2; i < roastProfilestr.Length-2; i = i + 2) {
                roastProfile.Add(new PointF(Convert.ToSingle(roastProfilestr[i], CultureInfo.InvariantCulture), Convert.ToSingle(roastProfilestr[i + 1], CultureInfo.InvariantCulture)));
            }
            ControlClass.keyPoints = roastProfile;

            double[] timeSeries = new double[1200];
            for (int i = 0; i < timeSeries.Length; i++) {
                timeSeries[i] = i;
            }


            ControlClass.pid = new PIDController();


            zedGraphControl1.GraphPane.AxisChange();

            }
            catch (Exception ex)
            {
                MessageBox.Show("Error loading recipe: " + ex.Message, "Recipe Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }

        }



        private void button1_Click(object sender, EventArgs e)
        {
            if (ControlClass.State == "idle")
            {
                ControlClass.prepareRoast();
                button1.BackColor = Color.Red;
                button1.Text = "pre-heating";
            }
            else if (ControlClass.State == "ready")
            {
                ControlClass.runCurve();
                button1.BackColor = Color.Yellow;
                button1.Text = "Run";
            }
            else if (ControlClass.State == "cooling")
            {
                if (MessageBox.Show(this, "The machine is still cooling down. Starting a new recipe in this state might influence the result. Start anyways?", "Start anyways?", MessageBoxButtons.YesNo) == DialogResult.Yes)
                {
                    ControlClass.runCurve();
                    button1.BackColor = Color.Yellow;
                    button1.Text = "Run";
                }
            }
            else if (ControlClass.State == "failsafe")
            {
                MessageBox.Show("The application will try to recover the failsafe and go back into idle state. If the button does not change the ESP is still in failsafe mode");
                ControlClass.State = "cooling";
            }
            else
            {
                ControlClass.abortRun();
                button1.BackColor = Color.Transparent;
            }
            timer1_Tick(null, null);
        }

        private void timer1_Tick(object sender, EventArgs e)
        {
            timer1.Stop();
            drawActiveCurve();
            updateButton();


            label1.Text = "Current: " + Math.Round(ControlClass.measuredTemp).ToString() + "°C";
            label2.Text = "SetPoint: " + Math.Round(ControlClass.setPoint).ToString() + "°C";
            label7.Text = "Fan: " + Math.Round(ControlClass.fanSpeed/255*100).ToString() + " %";

            if (ControlClass.elappsedSeconds == null) { label3.Text = ""; }
            else { label3.Text = "Elapsed Time: " + TimeSpan.FromSeconds(ControlClass.elappsedSeconds.ElapsedMilliseconds / 1000).ToString(@"mm\:ss"); }

            // Restzeit-Anzeige
            if (ControlClass.State == "running" && ControlClass.stopAt > 0 && ControlClass.elappsedSeconds != null)
            {
                int elapsedSec = Convert.ToInt32(ControlClass.elappsedSeconds.ElapsedMilliseconds / 1000);
                int remaining = Math.Max(0, ControlClass.stopAt - elapsedSec);
                label3.Text += "  |  Remaining: " + TimeSpan.FromSeconds(remaining).ToString(@"mm\:ss");
            }

            // First Crack Timer + DTR
            if (ControlClass.firstCrackSecond > 0 && ControlClass.elappsedSeconds != null && ControlClass.State == "running")
            {
                int elapsedSec = Convert.ToInt32(ControlClass.elappsedSeconds.ElapsedMilliseconds / 1000);
                int sinceFC = Math.Max(0, elapsedSec - ControlClass.firstCrackSecond);
                double dtr = elapsedSec > 0 ? (double)sinceFC / elapsedSec * 100 : 0;
                label3.Text += "  |  FC+" + TimeSpan.FromSeconds(sinceFC).ToString(@"mm\:ss") + " (DTR: " + dtr.ToString("F1") + "%)";
            }


            // Live Phasen-Anzeige
            if (ControlClass.elappsedSeconds != null)
            {
                int elapsedSec = Convert.ToInt32(ControlClass.elappsedSeconds.ElapsedMilliseconds / 1000);
                double currentTemp = ControlClass.measuredTemp;
                double currentRoR = ControlClass.rateOfRise != null && elapsedSec < ControlClass.rateOfRise.Length 
                                    ? ControlClass.rateOfRise[elapsedSec] : double.NaN;
                double prevTemp = elapsedSec > 0 && elapsedSec - 1 < ControlClass.realCurve.Length 
                                  ? ControlClass.realCurve[elapsedSec - 1] : double.NaN;

                var phase = iRoastControl.RoastEvaluator.DetectPhase(currentTemp, prevTemp, currentRoR, 
                            elapsedSec, ControlClass.firstCrackSecond, ControlClass.expectedFirstCrack, ControlClass.State);
                
                string phaseStatus = iRoastControl.RoastEvaluator.PhaseToString(phase);
                label3.Text += "  |  " + phaseStatus;
                
                // Color label text
                label3.ForeColor = iRoastControl.RoastEvaluator.PhaseToColor(phase);
            }
            else
            {
                label3.ForeColor = Color.Black;
            }

            // Check if Roast has just finished (transition running -> cooling)
            if (_wasRunning && ControlClass.State == "cooling" && ControlClass.elappsedSeconds != null)
            {
                _wasRunning = false;
                ShowRoastReport();
            }
            else if (ControlClass.State == "running")
            {
                _wasRunning = true;
            }

            // Auto-Drop based on Temperature
            if (chkAutoDrop.Checked && cmbDropMode.SelectedItem != null && cmbDropMode.SelectedItem.ToString().Contains("Temp") && ControlClass.State == "running")
            {
                if (double.TryParse(txtDropTarget.Text, out double targetTemp))
                {
                    if (ControlClass.measuredTemp >= targetTemp)
                    {
                        ControlClass.abortRun();
                    }
                }
            }

            switch (ControlClass.State) {
                case "running":
                    { button1.Text = "Running..."; break;}
                case "idle":
                    { button1.Text = "Run"; break;}
                case "cooling":
                    { button1.Text = "Cooling..."; break; }
                case "pre-heating":
                    { button1.Text = "Preparation..."; break; }
                case "ready":
                    { button1.Text = "Ready to start!"; break; }
                case "failsafe":
                    { button1.Text = "FAILSAFE!"; button1.BackColor = Color.OrangeRed; break; }
            }

     

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
            else if (ControlClass.State == "running")
            {
                button1.BackColor = Color.Yellow;
                button1.Text = "Running...";
            }
            else if (ControlClass.State == "ready")
            {
                button1.BackColor = Color.LightGreen;
                button1.Text = "Run";
            }
            else if(ControlClass.State == "failsafe")
            {
                button1.BackColor = Color.OrangeRed;
                button1.Text = "FAILSAFE";
            }
            else
            {
                button1.BackColor = Color.White;
                button1.Text = "Unknown State";
            }
            button1.Update();
        }

        private void checkBox1_CheckedChanged(object sender, EventArgs e)
        {
            ControlClass.simulation = checkBox1.Checked;
        }

     

        private SettingsWindow _settingsWindow;
        private void ShowSettingsWindow()
        {
            if (_settingsWindow == null || _settingsWindow.IsDisposed)
            {
                _settingsWindow = new SettingsWindow();
                _settingsWindow.Show();
            }
            else
            {
                _settingsWindow.BringToFront();
            }
        }

        private void button2_Click(object sender, EventArgs e)
        {
            ShowSettingsWindow();
        }

        private void comboBox2_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (comboBox2.Text.Length != 0)
            {
                readFile("./Recipes/" + comboBox2.Text + ".kpro");
            }
        }



        class SettingSaveFile
        {
            public string Recipe;
            public double defaultFanSpeed;
            public bool isDarkMode;
            public SettingSaveFile(string recipefile, double fanspeed, bool isDarkMode) 
            {
                this.Recipe = recipefile;
                this.defaultFanSpeed = fanspeed;
                this.isDarkMode = isDarkMode;
            }

        }

        protected override void OnClosing(CancelEventArgs e)
        {
         

            var settingsFolder = GetSettingsFolder();

            if (!Directory.Exists(settingsFolder))
            {
                Directory.CreateDirectory(settingsFolder);
            }

            var settingsPath = Path.Combine(settingsFolder, "default.roast");

            SettingSaveFile settings = new SettingSaveFile(comboBox2.Text + ".kpro", ControlClass.initFanSpeed, ThemeManager.IsDarkMode);
               string json = Newtonsoft.Json.JsonConvert.SerializeObject(settings);
                File.WriteAllText(settingsPath, json);

        }

        private void button4_Click(object sender, EventArgs e)
        {
            SaveFileDialog saveFileDialog = new SaveFileDialog();
            saveFileDialog.DefaultExt = ".roast";
            saveFileDialog.Filter = "Roast Files (*.roast)|*.roast";
            if (saveFileDialog.ShowDialog() == DialogResult.OK)
            {
                string fileName = saveFileDialog.FileName;

                SettingSaveFile settings = new SettingSaveFile(comboBox2.Text + ".kpro", ControlClass.initFanSpeed, ThemeManager.IsDarkMode);
                string json = Newtonsoft.Json.JsonConvert.SerializeObject(settings);
                File.WriteAllText(fileName, json);
                
                MessageBox.Show("Settings saved to " + fileName);
            }

        }

        private void button5_Click(object sender, EventArgs e)
        {
            ShowSettingsWindow();
        }

        private void button6_Click(object sender, EventArgs e)
        {
            resetView();
        }

        private void resetView()
        {
            var myPane = zedGraphControl1.GraphPane;

            myPane.YAxis.Scale.Min = 0;
            myPane.YAxis.Scale.Max = 260;
            myPane.XAxis.Scale.Min = 0;
            myPane.XAxis.Scale.Max = 1000;
        }

        private void textBox2_TextChanged(object sender, EventArgs e)
        {
            try {
                double value = double.Parse(textBox2.Text);

                if (value > 100) { value = 100; textBox2.Text = value.ToString(); }
                if (value < 0) { value = 0; textBox2.Text = value.ToString(); }

                value = value / 100 * 255;
                ControlClass.initFanSpeed = value/ 255.0 * 100.0;

                SerialCommunication.setFanSpeed(Convert.ToDouble(value));
            } catch { }
        }

        private void button7_Click(object sender, EventArgs e)
        {
            var value = int.Parse(textBox2.Text);
            value += 5;
            textBox2.Text = value.ToString();
        }

        private void button8_Click(object sender, EventArgs e)
        {
            var value = int.Parse(textBox2.Text);
            value -= 5;
            textBox2.Text = value.ToString();

        }

        private bool _wasRunning = false;
        private iRoastControl.RoastEvaluator.RoastScore _lastScore;

        private void btnBestPractices_Click(object sender, EventArgs e)
        {
            var bpWindow = new iRoastControl.BestPracticesWindow();
            bpWindow.Show();
        }

        private void btnShowReport_Click(object sender, EventArgs e)
        {
            if (_lastScore != null)
            {
                var reportWindow = new iRoastControl.RoastReportWindow(_lastScore);
                reportWindow.ShowDialog();
            }
            else if (ControlClass.elappsedSeconds != null)
            {
                ShowRoastReport();
            }
            else
            {
                MessageBox.Show("Röste zuerst einen Kaffee, um einen Bericht zu sehen!");
            }
        }

        private void ShowRoastReport()
        {
            int duration = Convert.ToInt32(ControlClass.elappsedSeconds.ElapsedMilliseconds / 1000);
            
            // Clean up realCurve - remove NaNs after duration
            double[] cleanRealCurve = new double[duration];
            for(int i=0; i<duration && i<ControlClass.realCurve.Length; i++) {
                cleanRealCurve[i] = ControlClass.realCurve[i];
            }

            _lastScore = iRoastControl.RoastEvaluator.Evaluate(
                cleanRealCurve,
                ControlClass.roastingProfile,
                ControlClass.rateOfRise,
                duration,
                ControlClass.firstCrackSecond,
                ControlClass.expectedFirstCrack
            );

            var reportWindow = new iRoastControl.RoastReportWindow(_lastScore);
            reportWindow.ShowDialog();
        }
    }
}
