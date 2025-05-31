![alt text](docu/assets/img/rel/headline.webp)

# CoffeeRoast
Self-Build Coffee Roaster from Popcorn Machine by adding temperature control. It follows reproducible a roast curve

![alt text](docu/assets/img/rel/enjoy.webp)

Used components:
================

Micro-Controller: LilyGo T-Display S3 ESP32-S3 (probably overkill but has a nice display and Wifi functionality if needed)
From: [Amazon](https://www.amazon.de/LILYGO-T-Display-S3-Entwicklungsboard-Normalbildschirm-schwarzem/dp/B0BRTT727Z?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&smid=ANWK9D8XV9DLB&th=1)

[Severin Popcorn-Maker](https://popcorn-rezepte.de/severin-pc-3751-popcornautomat-weiss-heissluft)
From: Ebay/Kleinanzeigen for 5-10€, People get this as a gift and use it not or just one times and sell it on ebay again

Temperature Sensor: MAX6675 Temperatur Sensor, K Type
From: [Amazon](https://www.amazon.de/dp/B0DFM7SJ3Z?ref=ppx_yo2ov_dt_b_fed_asin_title)

Solid State Relay: Solid-State-Relaismodul SSR-40DA
From: [Amazon](https://www.amazon.de/dp/B0CDKCBJRT?ref=ppx_yo2ov_dt_b_fed_asin_title)

Cables, Drills, Screwdriver, Soldering Iron


Instructions:
==============

To modify the roaster we had to 
* add a temperature sensor
* add a solid state relais to the heater
* add a PWM transistor to the fan

First of all, take apart the popcorn maker. The popcorn maker basically consists of two elements: Heating coils and the fan for the air.
These popcorn makers are engineered on the point, please be gentle with them as they are made of a lot of plastic. We destroyed a couple of them until we got it right. And even then the plastic melted on the third continous roast

![Open](docu/assets/img/rel/open_case.webp)

The main power switch connects the 230V from the outlet directly to the heating coils. The fan is connected in to the heating coil in a way that ~24V AC going through a rectifier (4 diodes) and is converted from AC to DC.

In a first step we need to decouple the heating coils from the fan and make the heating coil controllable using our solid state relay. We disconnected the fan from the diodes so we can run it from a external power supply providing 24V later on.
The heating coil was then soldered directly to the neutral conductor (blue wire). The red wire was cut and the solid state relay was built inbetween so we can control the power of the heating element using PWM later.

![alt text](docu/assets/img/rel/power_motor_w_24V.webp)

An external power supply or lab power supply was used to provide 24V DC to the fan, so it runs permanently. The fan can take from 4V - 30V. You can adjust the voltage to control the speed or later on use an gpio, a diode and a transistor to control it from the ESP32. The ESP ensures a smooth start of the fan. We broke on of the fans due to rapid spin up/down.

We drilled a hole in the top metal container fitting the thermo couple inside the roasting chamber. 
Note: **If the temperature sensor touches the metal casing it won't work properly.** Insulate the sensor with Kapton tape or some non conductive washer. The temperature reading is 0°C if the motor is spinning and no isolation was used. This is handled by the code to be filtered out but the roaster will go into fail save mode after 30s of nonsensical temperature readings and spins up the fan to 100%

The other 4 pins go into the ESP32. (VCC = 5V, GND = Ground, CLK = GPIO_13, CS = GPIO_12, DO = GPIO_11)

![alt text](docu/assets/img/rel/add_sensor_and_hole.webp)

Also the solid state relay will be connected to the ESP32. (In my case the voltage provided by the GPIO was enough to control the solid state relay, so i directly controlled it via the GPIO. In the case it does not work you need a separate transistor and supply 5V to the SSR).
The SSR uses GPIO_1 in my case.

## Control box

We 3D printed a box containing
* ESP32
* 24V Fan PWM control
* SSR (solid state relais) control
* Temperature sensor readoud board

And thats it!

![alt text](docu/assets/img/rel/assembly.webp)

Initially I wanted to use the ESP32 with Artisan (The software which is used for the comemrcial products, e.g. Coffeelogic Nano) but I had no luck getting it to work with a PID. So I decided to write software myself using C#. The communication is done via simple serial communication. 
You can send "get temp" via serial to the ESP32 and it will respond with the currently measured temperature from the thermo couple.
You can also send "set setpoint 255", which will be interpreted by the ESP32 and set the PWM duty cycle to 100% (255 = 100%, 128 = 50%, 0 = 0%). 
The C# Application can be found in the iRoastControl folder.


# Example usage

![alt text](docu/assets/img/rel/prepare_roast.webp)

Use not more than 100g of beans and roast in a well ventilated area. Prepare for flying coffee skins _everywhere_.
You can stop the roast at any time by flipping the on-off switch, which effectivly disconnects the heater while keeps the cooling fan running

[12s_roast.webm](https://github.com/user-attachments/assets/c60a7ab9-1068-4cd1-9d56-9880ee272cc1)

[12s video of 12min roasting](docu/assets/img/rel/12s_roast.webm)

iRoastControl
=============

iRoastControl is the control software. It comes with pre definded roast curves you can use for your first roast.

![alt text](docu/assets/img/rel/roasting.webp)

Each roasting curve as 3 phases. Pre-heating phase, running, cool-down. When you click "Run" the first time the application will pre-heat the popcorn machine until it reaches 180°. This is the moment you will charge your coffee beans. After that press "Run" again and the button will go yellow. This is where the roasting curve starts. You can follow your roasting temperaturs watching the red graph. Pressing the "Run" Button again will abort and go to the cool down phase where the heating element gets turned off and only the fan will blow. When your temperature is down to room-temperature you are done.

## UI

![alt text](docu/assets/img/rel/iroastcontrol_overview.png)


At the moment the curves are defined by some points in the source code, which get interpolated using a CubicSpline function. You can find the keypoints in ControlClass.cs in the function generateDefaultCurve(). Each point describes the temperature depending on the time in seconds. e.g. targetPoints.Add(new PointF(660, 180)); at 660s of the roasting curve, we should reach 180°C.
Adjust as you like.


# Fails

![alt text](docu/assets/img/rel/fan_blade.webp)

If the popcorn maker is old (like 20 years) the fan blades are rather brittle and may break easily if used on full power. 

Note: If the temperature sensor touches the metal casing it won't work properly. Insulate the sensor with Kapton tape or some non conductive washer.

# Tipps

* Cover any holes on top with capton tape to retain heat better. Plastic might melt a bit, though
* Test the roast with actual popcorn, as its cheaper if anything goes south
* Experiment and change only one setting at a time

![alt text](docu/assets/img/rel/result.webp)
