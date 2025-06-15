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
            var kproFiles = Directory.GetFiles("./Recipes/", "*.kpro").Select(o => Path.GetFileNameWithoutExtension(o.ToString())).ToArray();
            comboBox2.Items.AddRange(kproFiles.ToArray());
            comboBox2.Text = (comboBox2.Items[0].ToString());

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
            timer1.Tick += timer1_Tick;
            timer1.Start();

            ControlClass.initialize();
            loadRecipes();
            roastLevelControl1.RoastLevelChanged = RoastLevelChanged;

            loadSettings();
            resetView();
        }

        public void loadSettings()
        {
            var tempFolder = Path.GetTempPath() + "/iRoastControl";

            if (!Directory.Exists(tempFolder))
            {
                Directory.CreateDirectory(tempFolder);
            }

            var settingsPath = tempFolder + "/default.roast";

            if (File.Exists(settingsPath))
            {

                SettingSaveFile s = Newtonsoft.Json.JsonConvert.DeserializeObject<SettingSaveFile>(File.ReadAllText(settingsPath));
                
                if (s.Recipe != ".kpro") { 
                
                RoastLevelValues = s.RoastLevels;
                textBox2.Text = (s.defaultFanSpeed.ToString());
                comboBox2.Text = Path.GetFileNameWithoutExtension(s.Recipe);
                readFile("./Recipes/" + (s.Recipe));
                zedGraphControl1.Refresh();
                }
            }
        }
        public void RoastLevelChanged()
        {
            if (roastLevelControl1.RoastLevelIntensity == RoastLevelControl.RoastLevel.None) { ControlClass.stopAt = -1; return; }


            if (!_SetRoastLevelMode) { 
            
                
                if (RoastLevelValues.ContainsKey(roastLevelControl1.RoastLevelIntensity))
                {
                    if (ControlClass.State == "running" && ControlClass.elappsedSeconds.ElapsedMilliseconds > RoastLevelValues[roastLevelControl1.RoastLevelIntensity] * 1000)
                    {
                        var result = MessageBox.Show("You try to set a roast level, which has already passed. This would instantly stop your roast. Do you want to continue?", "Continue?", MessageBoxButtons.YesNo);
                        if (result == DialogResult.No)
                        {
                            roastLevelControl1.RoastLevelIntensity = RoastLevelControl.RoastLevel.None;
                            return; 
                        }
                    
                    }


                        ControlClass.stopAt = RoastLevelValues[roastLevelControl1.RoastLevelIntensity];                                              
                }
                else
            {
                ControlClass.stopAt = -1;
                MessageBox.Show("No roast level was defined for this setting");
                    roastLevelControl1.RoastLevelIntensity = RoastLevelControl.RoastLevel.None;
             }
            }
            else
            {
                //Setting Roastlevel mode
                if (ControlClass.elappsedSeconds == null)
                {
                    MessageBox.Show("Please start a roast first to define a roast level");
                }
                else
                {
                    if (roastLevelControl1.RoastLevelIntensity != RoastLevelControl.RoastLevel.None) { 
                        RoastLevelValues[roastLevelControl1.RoastLevelIntensity] = Convert.ToInt32(ControlClass.elappsedSeconds.ElapsedMilliseconds / 1000);
                    }
                }

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

                List<double> rlPointsT = new List<double>();
                List<double> rlPoints = new List<double>();
                foreach(var rl in RoastLevelValues.Values)
                {
                    rlPointsT.Add(ControlClass.roastingProfile[rl]);
                    rlPoints.Add(rl);
                }

                if (roastLevelPoints == null)
                {
                    roastLevelPoints = myPane.AddCurve("RoastLevels", rlPoints.ToArray(), rlPointsT.ToArray(),Color.Brown,SymbolType.XCross);
                    roastLevelPoints.Symbol.Size = 5;
                    roastLevelPoints.Line.IsVisible = false;
                    myPane.AxisChange();
                }
                else
                {
                    roastLevelPoints.Symbol.Size = 7;
                    roastLevelPoints.Symbol.Fill = new Fill(Color.Brown);
                    roastLevelPoints.Symbol.Type = SymbolType.Circle;

                    while (roastLevelPoints.Points.Count > 0) { roastLevelPoints.RemovePoint(0); }


                    if (_SetRoastLevelMode)
                    {
                        //show all roast levels
                        for (int i = 0; i < rlPoints.Count(); i++)
                        {
                            roastLevelPoints.AddPoint(rlPoints[i], rlPointsT[i]);
                        }
                    }
                    else
                    {
                        if (RoastLevelValues.ContainsKey(roastLevelControl1.RoastLevelIntensity)) { 
                        roastLevelPoints.AddPoint(RoastLevelValues[roastLevelControl1.RoastLevelIntensity], ControlClass.roastingProfile[RoastLevelValues[roastLevelControl1.RoastLevelIntensity]]);
                            }
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


                zedGraphControl1.Invalidate();
            }
        }

        double[] realCurveY;
        LineItem keyPointCurve;
        LineItem activeCurve;
        LineItem realCurve;
        LineItem roastLevelPoints;
        LineItem pidLevels;
        LineItem fanCurve;

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
                RoastLevelValues = s.RoastLevels;
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

            string[] lines = File.ReadAllLines(filename);

            Dictionary<string, string> datadict = new Dictionary<string, string>();
            foreach (string line in lines)
            {
                var key = line.Split(':')[0];
                var value = line.Split(':')[1];

                datadict.Add(key, value);
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


            if (datadict.ContainsKey("RoastLevel_Light"))
            {
                RoastLevelValues[RoastLevelControl.RoastLevel.Light] = Convert.ToInt32(datadict["RoastLevel_Light"]);
            }
            if (datadict.ContainsKey("RoastLevel_City"))
            {
                RoastLevelValues[RoastLevelControl.RoastLevel.City] = Convert.ToInt32(datadict["RoastLevel_City"]);
            }
            if (datadict.ContainsKey("RoastLevel_FullCity"))
            {
                RoastLevelValues[RoastLevelControl.RoastLevel.FullCity] = Convert.ToInt32(datadict["RoastLevel_FullCity"]);
            }
            if (datadict.ContainsKey("RoastLevel_French"))
            {
                RoastLevelValues[RoastLevelControl.RoastLevel.French] = Convert.ToInt32(datadict["RoastLevel_French"]);
            }
            if (datadict.ContainsKey("RoastLevel_Italian"))
            {
                RoastLevelValues[RoastLevelControl.RoastLevel.Italian] = Convert.ToInt32(datadict["RoastLevel_Italian"]);
            }




            ControlClass.keyPoints.Clear();

            var roastProfilestr = datadict["roast_profile"].Split(',');
            List<PointF> roastProfile = new List<PointF>();
            //roastProfile.Add(new PointF(0, 160));
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

        Dictionary<RoastLevelControl.RoastLevel, int> RoastLevelValues = new Dictionary<RoastLevelControl.RoastLevel, int>();

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
            else { label3.Text = "Elappsed Time: " + TimeSpan.FromSeconds(ControlClass.elappsedSeconds.ElapsedMilliseconds / 1000).ToString(@"mm\:ss"); }


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
            else if (ControlClass.State == "ready")
            {
                button1.BackColor = Color.LightGreen;
                button1.Text = "Run";
            }
            else if(ControlClass.State == "failsafe")
            {
    
            }
            else
            {
               
            }
            button1.Update();
        }

        private void checkBox1_CheckedChanged(object sender, EventArgs e)
        {
            ControlClass.simulation = checkBox1.Checked;
        }

     

        private void button2_Click(object sender, EventArgs e)
        {
            SettingsWindow settings = new SettingsWindow();
            settings.Show();
        }

        private void comboBox2_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (comboBox2.Text.Length != 0)
            {
                readFile("./Recipes/" + comboBox2.Text + ".kpro");
            }
        }

        Boolean _SetRoastLevelMode = false;
        private void button3_Click(object sender, EventArgs e)
        {
            _SetRoastLevelMode = !_SetRoastLevelMode;

            if (_SetRoastLevelMode) {
                button3.BackColor = Color.Yellow;
                ControlClass.stopAt = -1;
            }
            else
            {
                button3.BackColor = Color.Transparent;
            }
        }

        class SettingSaveFile
        {
            public Dictionary<RoastLevelControl.RoastLevel, int> RoastLevels;
            public string Recipe;
            public double defaultFanSpeed;
            public  SettingSaveFile(Dictionary<RoastLevelControl.RoastLevel, int> roastLevelvalues, string recipefile, double fanspeed ) 
            {
                this.RoastLevels = roastLevelvalues;
                this.Recipe = recipefile;
                this.defaultFanSpeed = fanspeed;
            }

        }

        protected override void OnClosing(CancelEventArgs e)
        {
         

            var tempFolder = Path.GetTempPath() + "/iRoastControl";

            if (!Directory.Exists(tempFolder))
            {
                Directory.CreateDirectory(tempFolder);
            }

            var settingsPath = tempFolder + "/default.roast";

            SettingSaveFile settings = new SettingSaveFile(RoastLevelValues, comboBox2.Text + ".kpro", ControlClass.initFanSpeed);
               string json = Newtonsoft.Json.JsonConvert.SerializeObject(settings);
                File.WriteAllText(settingsPath, json);

        }

        private void button4_Click(object sender, EventArgs e)
        {
            SaveFileDialog saveFileDialog = new SaveFileDialog();
            saveFileDialog.DefaultExt = ".roast";
            if (saveFileDialog.ShowDialog() == DialogResult.OK)
            {
                SettingSaveFile settings = new SettingSaveFile(RoastLevelValues, comboBox2.Text + ".kpro", ControlClass.initFanSpeed);


                string fileName = saveFileDialog.FileName;
                string json = Newtonsoft.Json.JsonConvert.SerializeObject(settings);
                File.WriteAllText(fileName, json);

                MessageBox.Show("Roast levels saved to " + fileName);
            }

        }

        private void button5_Click(object sender, EventArgs e)
        {
            SettingsWindow settings = new SettingsWindow();
            settings.Show();
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
    }
}
