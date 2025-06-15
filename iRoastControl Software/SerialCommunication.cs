using Artisan;
using Microsoft.SqlServer.Server;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO.Ports;
using System.Linq;
using System.Runtime.Remoting.Messaging;

public static class SerialCommunication
{

    public static int baudRate = 115200;

    public static SerialPort serialPort; 

    public static SerialPort newCOMPort(string portName, int baudRate)
    {
        return new SerialPort(portName, baudRate)
        {
            Parity = Parity.None,
            StopBits = StopBits.One,
            DataBits = 8,
            Handshake = Handshake.None,
            ReadTimeout = 1000,
            WriteTimeout = 500
        };
    }


    public static SerialPort findPopCornRoasterCOM()
    {
        string[] ports = SerialPort.GetPortNames();

        foreach (string port in ports)
        {
            SerialPort COMPort = newCOMPort(port, baudRate);
            try
            {
                if (!COMPort.IsOpen)
                {
                    COMPort.Open();
                }
                else
                {
                    break;
                }

                COMPort.Write("hello");
                System.Threading.Thread.Sleep(20);
               
                string response = COMPort.ReadLine();

                if (response == "popcorn roaster\r")
                {
                    Console.WriteLine("Found popcorn roaster on " + port);
                    return COMPort;
                }
            }
            catch { }
            finally { COMPort.Close(); }
        }

        return null;
    }

    public static void AutoConnect()
    { 
        SerialPort port = findPopCornRoasterCOM();
        if (port == null)
        {
            return;
        }
   
        serialPort = port;
  
    
    
    }

    public static string COMRequest(string request, bool ACK = true)
    {
        if (serialPort != null && !serialPort.IsOpen)
            try
            {
                serialPort.Open();
            }
            catch
            {
                serialPort.Close();
                AutoConnect();
                return null;
            }
        else
        {
         if (serialPort == null) { 
            AutoConnect();
            }

            if (serialPort == null)
            {
                Console.WriteLine("No device found");
                return "";
            }
        }

        serialPort.WriteLine(request);
        string response = "";
        if (ACK) { 
        System.Threading.Thread.Sleep(20);
        response= serialPort.ReadLine();

        if (response.ToLower().Contains("failsafe"))
            {
                ControlClass.State = "failsafe";
            }

        }

        if (ACK)
        {
            COMLog = request + " -> " + response + Environment.NewLine + COMLog;
        }
        else
        {
            COMLog = request + Environment.NewLine + COMLog;
        }

        if (COMLog.Length >= 1000)
        {
            COMLog.Substring(0, 1000);
        }

        return response;
    }

    public static string COMLog = "";

    public static void setFanSpeed(double setPoint)
    {
        if (serialPort == null)
        {
            AutoConnect();
        }

        if (serialPort == null) { return; }

        if (!serialPort.IsOpen)
            try
            {
                serialPort.Open();
            }
            catch { return; }

        if (setPoint > 255)
        {
            setPoint = 255;
        }
        else if (setPoint < 0)
        {
            setPoint = 0;
        }

        COMRequest("set fan " + setPoint.ToString(), false);

    }

    private static int errorReadingCounter = 0;

    private static void newReading(double temp)
    {
   
        if (temp > -50 && temp < 450)
        {
            errorReadingCounter--;
        }
        else { errorReadingCounter = errorReadingCounter + 5; }


        if (errorReadingCounter < 0)
        {
            errorReadingCounter = 0;
        }

        if (errorReadingCounter > 100)
        {
            ControlClass.State = "failsafe";
        }

    }

    public static double getTemperature()
    {
        if (serialPort != null && !serialPort.IsOpen)
            try { 
            serialPort.Open();
            }
            catch
            {
                serialPort.Close();
                AutoConnect();
                return -1;
            }

        try
        {


        string response = COMRequest("get temp");

        Double.TryParse(response, out double temperature);          

        newReading(temperature);
        return temperature * 1.1;

        }
        catch
        {
            serialPort.Close();
            AutoConnect();
            return -1;
      
        }

    }

    public static double getFanSpeed()
    {
        if (serialPort != null && !serialPort.IsOpen)
            try
            {
                serialPort.Open();
            }
            catch
            {
                serialPort.Close();
                AutoConnect();
                return -1;
            }

        try
        {


            string response = COMRequest("get fan");

            var fanSpeed = Double.Parse(response,CultureInfo.InvariantCulture);
            ControlClass.fanSpeed = fanSpeed;
            return fanSpeed;


        }
        catch
        {
            //serialPort.Close();
            AutoConnect();
            return -1;

        }

    }
    public static void setSetpoint(double setpoint)
    {
        if (serialPort == null)
        {
            AutoConnect();
        }

        if (serialPort == null) { return; }

        if (!serialPort.IsOpen)
            try
            {
                serialPort.Open();
            }
            catch { return;  }

        if (setpoint > 255)
        {
            setpoint = 255;
        } else if (setpoint < 0) {
            setpoint = 0;
        }


        COMRequest("set setpoint " + setpoint.ToString(), false);

    }

}
