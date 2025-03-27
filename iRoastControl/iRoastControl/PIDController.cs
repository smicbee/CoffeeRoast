using System;

public class PIDController
{
    private double _kp, _ki, _kd;
    private double _integral;
    private double _previousError;
    private double _outputMin, _outputMax;

    public PIDController(double kp, double ki, double kd, double outputMin, double outputMax)
    {
        _kp = kp;
        _ki = ki;
        _kd = kd;
        _outputMin = outputMin;
        _outputMax = outputMax;
        _integral = 0;
        _previousError = 0;
    }

    public double Compute(double setpoint, double measuredValue, double deltaTime)
    {
        double error = setpoint - measuredValue;

        // Proportional term
        double Pout = _kp * error;

        // Integral term
        _integral += error * deltaTime;
        double Iout = _ki * _integral;

        // Derivative term
        double derivative = (error - _previousError) / deltaTime;
        double Dout = _kd * derivative;

        // Compute final output
        double output = Pout + Iout + Dout;

        // Constrain output
        output = Clamp(output, _outputMin, _outputMax);

        // Save error for next iteration
        _previousError = error;

        return output;
    }

    private double Clamp(double value, double min, double max)
    {
        if (value < min) return min;
        if (value > max) return max;
        return value;
    }
}
