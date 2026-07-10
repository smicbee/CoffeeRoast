using System;
using System.Drawing;
using System.Windows.Forms;
using ZedGraph;

namespace iRoastControl
{
    public static class ThemeManager
    {
        public static bool IsDarkMode { get; set; } = false;

        // Colors for Light Mode
        private static readonly Color LightBg = Color.White;
        private static readonly Color LightFg = Color.Black;
        private static readonly Color LightPanel = SystemColors.Control;
        private static readonly Color LightGridBg = Color.White;
        private static readonly Color LightGridFg = Color.Black;
        private static readonly Color LightGridSelBg = Color.LightSkyBlue;
        private static readonly Color LightGraphBorder = Color.Black;
        
        // Colors for Dark Mode
        private static readonly Color DarkBg = Color.FromArgb(30, 30, 35);
        private static readonly Color DarkFg = Color.White;
        private static readonly Color DarkPanel = Color.FromArgb(40, 40, 45);
        private static readonly Color DarkGridBg = Color.FromArgb(40, 40, 45);
        private static readonly Color DarkGridFg = Color.White;
        private static readonly Color DarkGridSelBg = Color.FromArgb(60, 60, 65);
        private static readonly Color DarkGraphBorder = Color.LightGray;

        public static void ApplyTheme(Control control)
        {
            Color bg = IsDarkMode ? DarkBg : LightBg;
            Color fg = IsDarkMode ? DarkFg : LightFg;
            Color panelBg = IsDarkMode ? DarkPanel : LightPanel;

            // Forms
            if (control is Form form)
            {
                form.BackColor = bg;
                form.ForeColor = fg;
            }

            // Iterate children
            foreach (Control child in control.Controls)
            {
                ApplyControlTheme(child, bg, fg, panelBg);
            }
        }

        private static void ApplyControlTheme(Control ctrl, Color bg, Color fg, Color panelBg)
        {
            if (ctrl is Panel || ctrl is GroupBox || ctrl is TabPage)
            {
                ctrl.BackColor = panelBg;
                ctrl.ForeColor = fg;
            }
            else if (ctrl is System.Windows.Forms.Label lbl)
            {
                // If in Light Mode, replace light/white-ish colors with dark foreground
                if (!IsDarkMode)
                {
                    // Calculate luminance (0.299*R + 0.587*G + 0.114*B)
                    double luminance = (0.299 * lbl.ForeColor.R + 0.587 * lbl.ForeColor.G + 0.114 * lbl.ForeColor.B);
                    if (luminance > 160 || lbl.ForeColor == Color.LightGray || lbl.ForeColor == Color.Silver || lbl.ForeColor == Color.White)
                    {
                        lbl.ForeColor = fg;
                    }
                }
                // If in Dark Mode, ensure very dark colors are visible
                else if (IsDarkMode)
                {
                    double luminance = (0.299 * lbl.ForeColor.R + 0.587 * lbl.ForeColor.G + 0.114 * lbl.ForeColor.B);
                    if (luminance < 60 || lbl.ForeColor == Color.Black)
                    {
                        lbl.ForeColor = fg;
                    }
                }
            }
            else if (ctrl is CheckBox cb)
            {
                cb.ForeColor = fg;
                cb.BackColor = Color.Transparent;
            }
            else if (ctrl is Button btn)
            {
                if (IsDarkMode)
                {
                    // Dark Mode: Custom Flat Style
                    if (btn.BackColor == SystemColors.Control || btn.BackColor == LightBg || btn.BackColor == DarkBg)
                    {
                        btn.BackColor = bg;
                        btn.ForeColor = fg;
                        btn.FlatStyle = FlatStyle.Flat;
                        btn.FlatAppearance.BorderColor = panelBg;
                    }
                }
                else
                {
                    // Light Mode: Standard System Style
                    btn.FlatStyle = FlatStyle.Standard;
                    btn.UseVisualStyleBackColor = true;
                    btn.ForeColor = fg;
                    // Note: resetting BackColor to default often requires setting it to SystemColors.Control
                    if (btn.BackColor == DarkBg || btn.BackColor == bg) 
                    {
                        btn.BackColor = SystemColors.Control;
                    }
                }
            }
            else if (ctrl is TextBox txt)
            {
                txt.BackColor = panelBg;
                txt.ForeColor = fg;
                txt.BorderStyle = BorderStyle.FixedSingle;
            }
            else if (ctrl is ComboBox cmb)
            {
                cmb.BackColor = panelBg;
                cmb.ForeColor = fg;
                cmb.FlatStyle = FlatStyle.Flat;
            }
            else if (ctrl is DataGridView grid)
            {
                grid.BackgroundColor = IsDarkMode ? DarkBg : LightPanel;
                grid.ForeColor = IsDarkMode ? DarkGridFg : LightGridFg;
                grid.DefaultCellStyle.BackColor = IsDarkMode ? DarkGridBg : LightGridBg;
                grid.DefaultCellStyle.ForeColor = IsDarkMode ? DarkGridFg : LightGridFg;
                grid.DefaultCellStyle.SelectionBackColor = IsDarkMode ? DarkGridSelBg : LightGridSelBg;
                grid.ColumnHeadersDefaultCellStyle.BackColor = IsDarkMode ? DarkPanel : LightBg;
                grid.ColumnHeadersDefaultCellStyle.ForeColor = IsDarkMode ? DarkFg : LightFg;
                grid.EnableHeadersVisualStyles = false;
            }
            else if (ctrl is ZedGraphControl zgc)
            {
                ApplyZedGraphTheme(zgc);
            }

            // Recursive
            foreach (Control child in ctrl.Controls)
            {
                ApplyControlTheme(child, bg, fg, panelBg);
            }
        }

        private static void ApplyZedGraphTheme(ZedGraphControl zgc)
        {
            var pane = zgc.GraphPane;
            Color bg = IsDarkMode ? DarkBg : LightBg;
            Color axisC = IsDarkMode ? DarkGraphBorder : LightGraphBorder;
            Color chartBg = IsDarkMode ? DarkPanel : LightBg;

            pane.Fill = new Fill(bg);
            pane.Chart.Fill = new Fill(chartBg);
            pane.Title.FontSpec.FontColor = axisC;

            pane.XAxis.Color = axisC;
            pane.XAxis.Title.FontSpec.FontColor = axisC;
            pane.XAxis.Scale.FontSpec.FontColor = axisC;
            pane.XAxis.MajorGrid.Color = Color.FromArgb(50, axisC);
            pane.XAxis.MinorGrid.Color = Color.FromArgb(20, axisC);

            pane.YAxis.Color = axisC;
            pane.YAxis.Title.FontSpec.FontColor = axisC;
            pane.YAxis.Scale.FontSpec.FontColor = axisC;
            pane.YAxis.MajorGrid.Color = Color.FromArgb(50, axisC);
            pane.YAxis.MinorGrid.Color = Color.FromArgb(20, axisC);

            pane.Y2Axis.Color = axisC;
            pane.Y2Axis.Title.FontSpec.FontColor = axisC;
            pane.Y2Axis.Scale.FontSpec.FontColor = axisC;
            pane.Y2Axis.MajorGrid.Color = Color.FromArgb(50, axisC);
            pane.Y2Axis.MinorGrid.Color = Color.FromArgb(20, axisC);

            pane.Legend.Fill = new Fill(bg);
            pane.Legend.FontSpec.FontColor = axisC;
            pane.Legend.Border.Color = axisC;

            zgc.Refresh();
        }
    }
}
