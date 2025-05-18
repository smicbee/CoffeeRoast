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
    public partial class RoastLevelControl : UserControl
    {
        public RoastLevelControl()
        {
            InitializeComponent();

            List<Control> list = new List<Control>();
            list.Add(pictureBox1);  
            list.Add(pictureBox2);
            list.Add(pictureBox3);
            list.Add(pictureBox4);
            list.Add(pictureBox5);
            pbArray = list.ToArray();

        }

        public Action RoastLevelChanged;
  

        private Control[] pbArray;
        private RoastLevel _RoastLevel;
        public RoastLevel RoastLevelIntensity 
        { 
        get { return _RoastLevel; }
        set { _RoastLevel = value;

                Image bean = Properties.Resources.coffee_bean_256;
                Image beansw = Properties.Resources.coffee_bean_sw_256;
            

                for (int i = 0; i < 5; i++)
                {
                    if (i < (int)_RoastLevel)
                    {
                        pbArray[i].BackgroundImage = bean;
                    }
                    else
                    {
                        pbArray[i].BackgroundImage = beansw;
                    }
                }

                label1.Text = _RoastLevel.ToString();

                if (RoastLevelChanged != null)
                {
                    RoastLevelChanged();
                }
            } 
        
        }

        public enum RoastLevel : int
        {
            None = 0,
            Light = 1,
            City = 2,
            FullCity = 3,
            French = 4,
            Italian = 5
        }
        private void pictureBox1_Click(object sender, EventArgs e)
        {
            var rl = RoastLevel.Light;
            if (RoastLevelIntensity == rl)
            {
                RoastLevelIntensity = RoastLevel.None;
            }
            else
            {
                RoastLevelIntensity = rl;
            }
        }

        private void pictureBox2_Click(object sender, EventArgs e)
        {
            var rl = RoastLevel.City;
            if (RoastLevelIntensity == rl)
            {
                RoastLevelIntensity = RoastLevel.None;
            }
            else
            {
                RoastLevelIntensity = rl;
            }
        }

        private void pictureBox3_Click(object sender, EventArgs e)
        {
            var rl = RoastLevel.FullCity;
            if (RoastLevelIntensity == rl)
            {
                RoastLevelIntensity = RoastLevel.None;
            }
            else
            {
                RoastLevelIntensity = rl;
            }
        }

        private void pictureBox4_Click(object sender, EventArgs e)
        {
            var rl = RoastLevel.French;
            if (RoastLevelIntensity == rl)
            {
                RoastLevelIntensity = RoastLevel.None;
            }
            else
            {
                RoastLevelIntensity = rl;
            }
        }

        private void pictureBox5_Click(object sender, EventArgs e)
        {
            var rl = RoastLevel.Italian;
            if (RoastLevelIntensity == rl)
            {
                RoastLevelIntensity = RoastLevel.None;
            }
            else
            {
                RoastLevelIntensity = rl;
            }
        }

        private void RoastLevelControl_Load(object sender, EventArgs e)
        {

        }
    }
}
