using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO.Ports;
using System.Linq;

public static class SerialCommunication
{

    static string portName = "COM5";
    public static int baudRate = 115200;

    public static SerialPort serialPort = new SerialPort(portName, baudRate)
    {
        Parity = Parity.None,
        StopBits = StopBits.One,
        DataBits = 8,
        Handshake = Handshake.None,
        ReadTimeout = 5000,
        WriteTimeout = 500
    };

    public static double getTemperature()
    {
        if (!serialPort.IsOpen)
            serialPort.Open();
        serialPort.WriteLine("get temp");  // Send command to Arduino

        System.Threading.Thread.Sleep(200);  // Give Arduino time to respond

        string response = serialPort.ReadLine();

        Double.TryParse(response, out double temperature);

        return temperature;
    }

    public static void setSetpoint(double setpoint)
    {
        if (!serialPort.IsOpen)
            serialPort.Open();

        if (setpoint > 255)
        {
            setpoint = 255;
        } else if (setpoint < 0) {
            setpoint = 0;
        }



        serialPort.WriteLine("set setpoint " + setpoint.ToString());  // Send command to Arduino
    }

}
