using Artisan;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace iRoastControl
{
    public partial class SettingsWindow : Form
    {
        public SettingsWindow()
        {
            InitializeComponent();
        }

        private void SettingsWindow_Load(object sender, EventArgs e)
        {
            updateValues();
            timer1.Interval = 1000;
            timer1.Tick += TimerTick;
            timer1.Start();
        }

        private void TimerTick(object sender, EventArgs e)
        {
            updateValues();
        }

        private void button1_Click(object sender, EventArgs e)
        {
            double p; 
            double.TryParse(tb_Kp.Text, out p);

            double i;
            double.TryParse(tb_Ki.Text, out i);

            double d;
            double.TryParse((string)tb_Kd.Text, out d);


            Console.WriteLine("PID set to: " + p.ToString() + " " + i.ToString() + " " + d.ToString());   
        }

    
        private void updateValues()
        {
            if (comboBox1.DroppedDown == false)
            {
                comboBox1.Text = ControlClass.State;
            }

            textBox1.Text = SerialCommunication.COMLog;

            tb_Kp.Text = ControlClass.pid.Kp.ToString();
            tb_Ki.Text = ControlClass.pid.Ki.ToString();
            tb_Kd.Text = ControlClass.pid.Kd.ToString();

            if (ControlClass.elappsedSeconds == null)
            {
                tb_time.Enabled = false;
            }
            else
            {
                tb_time.Enabled = true;
                tb_time.Text = Convert.ToInt32(ControlClass.elappsedSeconds.ElapsedMilliseconds / 1000 + ControlClass.timeOffset).ToString();
            }
        }

        private void button2_Click(object sender, EventArgs e)
        {
            ControlClass.pid.reset();
        }

        private void button3_Click(object sender, EventArgs e)
        {
            ControlClass.pid.Kp += 1;
            updateValues();
        }

        private void button4_Click(object sender, EventArgs e)
        {
            ControlClass.pid.Kp -= 1;
            updateValues();
        }

        private void button6_Click(object sender, EventArgs e)
        {
            ControlClass.pid.Ki += 0.01;
            updateValues();
        }

        private void button5_Click(object sender, EventArgs e)
        {
            ControlClass.pid.Ki -= 0.01;
            updateValues();
        }

        private void button8_Click(object sender, EventArgs e)
        {
            ControlClass.pid.Kd += 0.1;
            updateValues();
        }

        private void button7_Click(object sender, EventArgs e)
        {
            ControlClass.pid.Kd -= 0.1;
            updateValues();
        }

        private void button10_Click(object sender, EventArgs e)
        {

            ControlClass.timeOffset += 10;
            updateValues();
        }

        private void button9_Click(object sender, EventArgs e)
        {
            ControlClass.timeOffset -= 10;
            if (ControlClass.timeOffset < 0) { ControlClass.timeOffset = 0; }

            updateValues();
        }

        private void comboBox1_SelectedIndexChanged(object sender, EventArgs e)
        {
            ControlClass.State = comboBox1.Text;
        }

        private void textBox2_TextChanged(object sender, EventArgs e)
        {
            if (double.TryParse(textBox2.Text, out double value))
            {
                ControlClass.timeMultiplicator = value;
                textBox2.BackColor = Color.White;
            }
            else
            {
                textBox2.BackColor = Color.Red;
            }



        }
    }
}
