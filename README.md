# pi-autopilot
Python Autopilot plugin by Round Owl
Version 0.7

This plugin substitutes flight control surface management.

Problem that this plugin tries to solve:
When you set "override_control_surfaces" to "1", X-Plane drops all
control over the plane, meaning that you can't fly with joystick,
mouse or by using autopilot.

This plugin will start working once both of these are true:
1) Flight director and autopilot are turned on;
2) Landing lights are off.

After plugin starts working, it will constantly try to follow flight
director commands, and counter any yawing with rudder.
