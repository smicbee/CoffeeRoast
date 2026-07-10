using Artisan;
using System;

public class PIDController
{
    public double Kp {get; set;}
    public double Ki {get; set;}
    public double Kd {get; set;}

    private double integral;
    private double previousError;
    private double previousTime;

    private double[] timeCurve;
    private double[] tempCurve;

    private readonly double targetInFuture;

    private double lastOutput = 0;

    private double updateInterval = 3;

    public double[] pidvalues = new double[1200];

    private int ClampHistoryIndex(double currentTime)
    {
        int index = Convert.ToInt32(currentTime);
        if (index < 0)
        {
            return 0;
        }

        if (index >= pidvalues.Length)
        {
            return pidvalues.Length - 1;
        }

        return index;
    }

    public PIDController(double Kp = 3, double Ki = 0.02, double Kd = 0.2)
    {
        this.Kp = Kp;         // z. B. 5.0
        this.Ki = Ki;         // z. B. 0.05
        this.Kd = Kd;         // z. B. 0.5

        this.integral = 0;
        this.previousError = 0;
        this.previousTime = -1;

        initTimeCurve();
        this.tempCurve = ControlClass.roastingProfile;

        this.targetInFuture = 40;
      
        for (int i = 0; i < pidvalues.Length; i++)
        {
            pidvalues[i] = double.NaN;
        }
    }

    public void reset()
    {
        integral = 0;
        previousError = 0;
        previousTime = -1;
    }
    private void initTimeCurve()
    {
        double[] timeSeries = new double[1200];
        for (int i = 0; i < timeSeries.Length; i++)
        {
            timeSeries[i] = i;
        }


        this.timeCurve = timeSeries;
    }
    public double Set(double currentTime, double currentSetpoint)
    {
        var output = Math.Max(0, Math.Min(255, currentSetpoint));
        pidvalues[ClampHistoryIndex(currentTime)] = output;
        lastOutput = output;
        return output;

    }
    public double Update(double currentTime, double currentTemp)
    {

        double targetTime = currentTime + targetInFuture;
        double targetTemp = InterpolateTargetTemperature(targetTime);

        double error = targetTemp - currentTemp;
        double deltaTime = previousTime >= 0 ? currentTime - previousTime : 0;

        if (deltaTime < updateInterval && previousTime >= 0 && deltaTime > 0)
        {
            pidvalues[ClampHistoryIndex(currentTime)] = lastOutput;
            return lastOutput;
        }

        if (currentTemp > 450 || currentTemp < -50)
        {
            //invalid reading
            pidvalues[ClampHistoryIndex(currentTime)] = lastOutput;
            return lastOutput;

        }

        if (deltaTime > 0)
        {
            integral += error * deltaTime;
        }

        double derivative = deltaTime > 0 ? (error - previousError) / deltaTime : 0;

        // Dynamische Anpassung von Kp mit Temperatur (sanft)
        double baseKp = (currentTemp < 100) ? Kp * 0.6 : Kp;

        double dynamicKp = baseKp * (1 + 0.2 * (currentTemp / 220.0));
        double dynamicKi = Ki;
        double dynamicKd = Kd;

        if (currentTemp > 190 )
        {
            dynamicKp *= 0.8; // sanfter regeln
            dynamicKi = 0.5 * Ki;
            dynamicKd = 1.2*Kd; // Reaktion auf schnelle Temperaturänderungen stärken
        }


        double output = dynamicKp * error + dynamicKi * integral + dynamicKd * derivative;

        previousError = error;
        previousTime = currentTime;


        if (currentTime < 120)
        {
            output = Math.Min(output, 170); // Frühphase stärker deckeln
        }

        output = Math.Max(0, Math.Min(255, output));
        pidvalues[ClampHistoryIndex(currentTime)] = output;
        lastOutput = output;

        return output;
    }

    private double InterpolateTargetTemperature(double targetTime)
    {
        if (targetTime <= timeCurve[0]) return tempCurve[0];
        if (targetTime >= timeCurve[tempCurve.Length - 1]) return tempCurve[tempCurve.Length - 1];

        for (int i = 1; i < timeCurve.Length; i++)
        {
            if (timeCurve[i] >= targetTime)
            {
                double t0 = timeCurve[i - 1], t1 = timeCurve[i];
                double y0 = tempCurve[i - 1], y1 = tempCurve[i];
                return y0 + (targetTime - t0) * (y1 - y0) / (t1 - t0);
            }
        }

        return tempCurve[tempCurve.Length - 1];
    }
}
