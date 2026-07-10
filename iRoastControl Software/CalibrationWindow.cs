using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;
using ZedGraph;
using Artisan;

namespace iRoastControl
{
    public class CalibrationWindow : Form
    {
        private PIDAutoTuner _tuner;
        private Timer _uiTimer;
        private ZedGraphControl _graph;
        private System.Windows.Forms.Label _lblStatus;
        private Button _btnAction;
        private Button _btnApply;
        private System.Windows.Forms.Label _lblResults;

        // Data for graph
        private PointPairList _tempList = new PointPairList();
        private PointPairList _heatList = new PointPairList();
        private double _startTime;

        public CalibrationWindow()
        {
            InitializeUI();

            _tuner = new PIDAutoTuner();
            // Optional: Get user fan speed logic
            _tuner.FanSpeedPct = ControlClass.initFanSpeed;
            _tuner.StatusUpdated += msg => 
            {
                if (this.IsHandleCreated)
                    this.Invoke((MethodInvoker)(() => _lblStatus.Text = msg));
            };

            _tuner.TuningCompleted += () => 
            {
                if (this.IsHandleCreated)
                    this.Invoke((MethodInvoker)(() => 
                    {
                        _btnAction.Text = "Schließen";
                        _btnApply.Visible = true;
                        _lblResults.Text = $"Ergebnis:\nKp: {_tuner.Kp} | Ki: {_tuner.Ki} | Kd: {_tuner.Kd}";
                        _lblStatus.Text = "Fertig! Speichere Parameter oder schließe das Fenster.";
                    }));
            };

            ControlClass.autoTuner = _tuner;

            _uiTimer = new Timer();
            _uiTimer.Interval = 1000;
            _uiTimer.Tick += UiTimer_Tick;
        }

        private void InitializeUI()
        {
            this.Text = "PID Auto-Calibration";
            this.Size = new Size(800, 600);
            this.StartPosition = FormStartPosition.CenterParent;
            this.Font = new Font("Segoe UI", 10);
            
            this.Load += (s, e) => ThemeManager.ApplyTheme(this);

            var titleLabel = new System.Windows.Forms.Label();
            titleLabel.Text = "⚙️ Röster Kalibrierung (Setup Roast)";
            titleLabel.Font = new Font("Segoe UI", 16, FontStyle.Bold);
            titleLabel.Location = new Point(20, 10);
            titleLabel.Size = new Size(500, 35);
            this.Controls.Add(titleLabel);

            var descLabel = new System.Windows.Forms.Label();
            descLabel.Text = "Ermittelt die idealen PID-Parameter für deinen angeschlossenen Röster.";
            descLabel.Location = new Point(20, 45);
            descLabel.Size = new Size(600, 25);
            this.Controls.Add(descLabel);

            _lblStatus = new System.Windows.Forms.Label();
            _lblStatus.Text = "Bereit zum Start. (Röster sollte auskühlt sein <60°C)";
            _lblStatus.Font = new Font("Segoe UI", 11, FontStyle.Bold);
            _lblStatus.Location = new Point(20, 80);
            _lblStatus.Size = new Size(700, 25);
            this.Controls.Add(_lblStatus);

            _graph = new ZedGraphControl();
            _graph.Location = new Point(20, 110);
            _graph.Size = new Size(740, 360);
            _graph.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right | AnchorStyles.Bottom;
            this.Controls.Add(_graph);

            SetupGraph();

            _btnAction = new Button();
            _btnAction.Text = "▶ Kalibrierung Starten";
            _btnAction.Font = new Font("Segoe UI", 12, FontStyle.Bold);
            _btnAction.FlatStyle = FlatStyle.Flat;
            _btnAction.Location = new Point(20, 490);
            _btnAction.Size = new Size(220, 45);
            _btnAction.Click += BtnAction_Click;
            _btnAction.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            this.Controls.Add(_btnAction);

            _btnApply = new Button();
            _btnApply.Text = "💾 PIDs übernehmen";
            _btnApply.Font = new Font("Segoe UI", 12, FontStyle.Bold);
            _btnApply.FlatStyle = FlatStyle.Flat;
            _btnApply.Location = new Point(260, 490);
            _btnApply.Size = new Size(220, 45);
            _btnApply.Visible = false;
            _btnApply.Click += BtnApply_Click;
            _btnApply.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            this.Controls.Add(_btnApply);

            _lblResults = new System.Windows.Forms.Label();
            _lblResults.Text = "";
            _lblResults.Font = new Font("Segoe UI", 12, FontStyle.Bold);
            _lblResults.Location = new Point(500, 490);
            _lblResults.Size = new Size(250, 50);
            _lblResults.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            this.Controls.Add(_lblResults);
        }

        private void SetupGraph()
        {
            var p = _graph.GraphPane;
            p.Title.Text = "Step Response";
            p.XAxis.Title.Text = "Zeit (s)";
            p.YAxis.Title.Text = "Temperatur (°C)";
            p.Y2Axis.Title.Text = "Heizung (%)";
            p.Y2Axis.IsVisible = true;
            
            var curveTemp = p.AddCurve("Ist-Temperatur", _tempList, Color.Red, SymbolType.None);
            curveTemp.Line.Width = 2;
            
            var curveHeat = p.AddCurve("Heizleistung", _heatList, Color.Orange, SymbolType.None);
            curveHeat.Line.Width = 2;
            curveHeat.Line.Style = DashStyle.Dash;
            curveHeat.IsY2Axis = true;
            
            p.YAxis.Scale.Min = 0;
            p.YAxis.Scale.Max = 250;
            p.Y2Axis.Scale.Min = 0;
            p.Y2Axis.Scale.Max = 110;
        }

        private void BtnAction_Click(object sender, EventArgs e)
        {
            if (_tuner.State == PIDAutoTuner.TuningState.Idle)
            {
                if (ControlClass.State != "idle")
                {
                    MessageBox.Show("Röster muss im Idle-State sein, um die Kalibrierung zu starten.");
                    return;
                }

                // Check Temp
                if (ControlClass.measuredTemp > 60)
                {
                    if (MessageBox.Show("Der Röster ist noch warm (>60°C). Für eine genaue Messung sollte er kalt sein. Trotzdem starten?", "Warnung", MessageBoxButtons.YesNo) == DialogResult.No)
                        return;
                }

                _startTime = (DateTime.UtcNow - new DateTime(1970, 1, 1)).TotalSeconds;
                ControlClass.State = "calibration";
                ControlClass.elappsedSeconds.Restart();
                _tuner.Start();
                _uiTimer.Start();
                _btnAction.Text = "🛑 Abbruch";
            }
            else if (_tuner.State == PIDAutoTuner.TuningState.Finished || _tuner.State == PIDAutoTuner.TuningState.Aborted)
            {
                this.Close(); // Used as close button now
            }
            else
            {
                // Abort
                _tuner.Abort();
                ControlClass.State = "cooling";
                _btnAction.Text = "Schließen";
            }
        }

        private void BtnApply_Click(object sender, EventArgs e)
        {
            if (ControlClass.pid != null)
            {
                ControlClass.pid.Kp = _tuner.Kp;
                ControlClass.pid.Ki = _tuner.Ki;
                ControlClass.pid.Kd = _tuner.Kd;
            }
            MessageBox.Show("Parameter im Speicher übernommen. Vergesse nicht, das SettingsWindow abzuspeichern.");
            this.Close();
        }

        private void UiTimer_Tick(object sender, EventArgs e)
        {
            if (_tuner.State != PIDAutoTuner.TuningState.Idle)
            {
                double nowSecs = (DateTime.UtcNow - new DateTime(1970, 1, 1)).TotalSeconds - _startTime;
                _tempList.Add(nowSecs, ControlClass.measuredTemp);
                
                // Show Heat setting as percentage of 255
                double currentHeatPct = (ControlClass.setPoint / 255.0) * 100.0;
                _heatList.Add(nowSecs, currentHeatPct);
                
                _graph.AxisChange();
                _graph.Invalidate();
            }

            if (_tuner.State == PIDAutoTuner.TuningState.Aborted && _btnAction.Text != "Schließen")
            {
                _btnAction.Text = "Schließen";
                _uiTimer.Stop();
            }
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            _uiTimer.Stop();
            ControlClass.autoTuner = null;
            if (ControlClass.State == "calibration")
            {
                ControlClass.State = "cooling"; // Sicherstellen, dass das System kühlt
            }
            base.OnFormClosing(e);
        }
    }
}
