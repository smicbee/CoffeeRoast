
using MathNet.Numerics.Interpolation;
using System;
using System.Collections.Generic;
using System.Drawing;
using ZedGraph;



public class SplineInterpolator
{
    private IInterpolation _spline;

    public SplineInterpolator(List<PointF> fixedValues)
    {
        int numOfValues = fixedValues.Count;
        double[] xValues = new double[numOfValues];
        double[] yValues = new double[numOfValues];

        for (int i = 0; i < numOfValues; i++)
        {
            xValues[i] = fixedValues[i].X;
            yValues[i] = fixedValues[i].Y;
        }

        if (xValues.Length != yValues.Length || xValues.Length < 2)
            throw new ArgumentException("Arrays must have the same length and contain at least two points.");

        _spline = CubicSpline.InterpolateNatural(xValues, yValues);
    }

    public double Interpolate(double xQuery)
    {
        return _spline.Interpolate(xQuery);
    }


}
