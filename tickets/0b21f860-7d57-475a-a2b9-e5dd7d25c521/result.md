# Result

Fixed the control loop timer interval conversion in `iRoastControl Software/ControlClass.cs` so the `deltaTime` value in seconds is converted to milliseconds with `deltaTime * 1000`.

Verification:
- Built `iRoastControl Software/iRoastControl.sln` with `xbuild /p:Configuration=Debug /p:Platform="Any CPU"` successfully.
- Checked the compiled assembly with `deltaTime = 0.5`; `ControlClass.initialize()` now configures the timer interval as `500` milliseconds.
