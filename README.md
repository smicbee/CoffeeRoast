# CoffeeRoast
Self-Build Coffee Roaster from Popcorn Machine

Used components:
================

Micro-Controller: LilyGo T-Display S3 ESP32-S3 (probably overkill but has a nice display and Wifi functionality if needed)
From: https://www.amazon.de/LILYGO-T-Display-S3-Entwicklungsboard-Normalbildschirm-schwarzem/dp/B0BRTT727Z?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&smid=ANWK9D8XV9DLB&th=1

Severin Popcorn-Maker (https://popcorn-rezepte.de/severin-pc-3751-popcornautomat-weiss-heissluft)
From: Ebay/Kleinanzeigen for 5-10€, People get this as a gift and use it no or just one times and sell it on ebay again

Temperature Sensor: MAX6675 Temperatur Sensor, K Type
From: https://www.amazon.de/dp/B0DFM7SJ3Z?ref=ppx_yo2ov_dt_b_fed_asin_title

Solid State Relay: Solid-State-Relaismodul SSR-40DA
From: https://www.amazon.de/dp/B0CDKCBJRT?ref=ppx_yo2ov_dt_b_fed_asin_title

Cables...


Instructions:
==============


First of all, take apart the popcorn maker. The popcorn maker basically consists of two elements: Heating coils and the fan for the air.
The main power switch connects the 230V from the outlet directly to the heating coils. The fan is connected in series to the heating coil after going through a rectifier (4 diodes) and is received 18V DC.

In a first step we need to decouple the heating coils from the fan and make the heating coil controllable using our solid state relay. I disconnected the fan from the diodes so we can run it from a external power supply providing 18V later on.
The heating coil was then soldered directly to the neutral conductor (blue wire). The red wire was cut and the solid state relay was built inbetween so we can control the power of the heating element using PWM later.
(images will follow)

A external power supply or lab power supply was used to provide 18V DC to the fan, so it runs permanently. The fan can take from 4V - 30V. You can adjust the voltage to control the speed.

I drilled a hole in the top metal container fitting the thermo couple inside the roasting chamber. The other 4 pins go into the ESP32. (VCC = 5V, GND = Ground, CLK = GPIO_13, CS = GPIO_12, DO = GPIO_11)
Also the solid state relay will be connected to the ESP32. (In my case the voltage provided by the GPIO was enough to control the solid state relay, so i directly controlled it via the GPIO. In the case it does not work you need a separate transistor and supply 5V to the SSR).
The SSR uses GPIO_1 in my case.

And thats it!
Initially I wanted to use the ESP32 with Artisan but I had no luck getting it to work with a PID. So i decided to write my software myself using C#. The communication is done via simple serial communication. 
You can send "get temp" via serial to the ESP32 and it will respond with the currently measured temperature from the thermo couple.
You can also send "set setpoint 255", which will be interpreted by the ESP32 and set the PWM duty cycle to 100% (255 = 100%, 128 = 50%, 0 = 0%). 
The C# Application can be found in the iRoastControl folder.

iRoastControl
=============

At the moment the curves are defined by some points in the source code, which get interpolated using a CubicSpline function. You can find the keypoints in ControlClass.cs in the function generateDefaultCurve(). Each point describes the temperature depending on the time in seconds. e.g. targetPoints.Add(new PointF(660, 180)); at 660s of the roasting curve, we should reach 180°C.
Adjust as you like.

Each roasting curve as 3 phases. Pre-heating phase, running, cool-down. When you click "Run" the first time the application will pre-heat the popcorn machine until it reaches 180°. This is the moment you will charge your coffee beans. After that press "Run" again and the button will go yellow. This is where the roasting curve starts. You can follow your roasting temperaturs watching the red graph. Pressing the "Run" Button again will abort and go to the cool down phase where the heating element gets turned off and only the fan will blow. When your temperature is down to room-temperature you are done.

