'''
Copyright 2016 Andrey Seliverstov

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
--------------------------------
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
'''

from XPLMUtilities import *
from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMMenu import *
import math

class PythonInterface:
    def XPluginStart(self):
        self.Name = "Python Autopilot"
        self.Sig = "RoundOwl.Autopilot"
        self.Desc = "Basic implementation of autopilot in python. Use and modify as you wish."
                
		self.DrawWindowCB = self.DrawWindowCallback
        self.KeyCB = self.KeyCallback
        self.MouseClickCB = self.MouseClickCallback
		self.WindowId = XPLMCreateWindow(self, 50, 600, 300, 400, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
        
        #----------------
        # Adjust sensitivity here.
        # Cessna 172SP: 1 roll, 1 pitch
        # Boeing 747: 8 roll, 4 pitch
        self.RollSens = 1
        self.PitchSens = 1
        #----------------

        self.landingLightsDR = XPLMFindDataRef("sim/cockpit2/switches/landing_lights_on")
        self.elvTrim = XPLMFindDataRef("sim/flightmodel/controls/elv_trim")

        self.controlsurfaceOvrDR = XPLMFindDataRef("sim/operation/override/override_control_surfaces")
        self.ail1LeftDefDR = XPLMFindDataRef("sim/flightmodel/controls/wing1l_ail1def")
        self.ail1RightDefDR = XPLMFindDataRef("sim/flightmodel/controls/wing1r_ail1def")
        self.ail2LeftDefDR = XPLMFindDataRef("sim/flightmodel/controls/wing2l_ail1def")
        self.ail2RightDefDR = XPLMFindDataRef("sim/flightmodel/controls/wing2r_ail1def")
        self.ail3LeftDefDR = XPLMFindDataRef("sim/flightmodel/controls/wing3l_ail1def")
        self.ail3RightDefDR = XPLMFindDataRef("sim/flightmodel/controls/wing3r_ail1def")
        self.ail4LeftDefDR = XPLMFindDataRef("sim/flightmodel/controls/wing4l_ail1def")
        self.ail4RightDefDR = XPLMFindDataRef("sim/flightmodel/controls/wing4r_ail1def")
        self.elev11DefDR = XPLMFindDataRef("sim/flightmodel/controls/hstab1_elv1def")
        self.elev12DefDR = XPLMFindDataRef("sim/flightmodel/controls/hstab1_elv2def")
        self.elev21DefDR = XPLMFindDataRef("sim/flightmodel/controls/hstab2_elv1def")
        self.elev22DefDR = XPLMFindDataRef("sim/flightmodel/controls/hstab2_elv2def")
        self.rudd11DefDR = XPLMFindDataRef("sim/flightmodel/controls/vstab1_rud1def")
        self.rudd12DefDR = XPLMFindDataRef("sim/flightmodel/controls/vstab1_rud2def")
        self.rudd21DefDR = XPLMFindDataRef("sim/flightmodel/controls/vstab2_rud1def")
        self.rudd22DefDR = XPLMFindDataRef("sim/flightmodel/controls/vstab2_rud2def")
                                                 
        self.autopilotOnDR = XPLMFindDataRef("sim/cockpit/autopilot/autopilot_mode")
        self.FDPitchDR = XPLMFindDataRef("sim/cockpit/autopilot/flight_director_pitch")
        self.FDRollDR = XPLMFindDataRef("sim/cockpit/autopilot/flight_director_roll")
        self.planePitchDR = XPLMFindDataRef("sim/cockpit2/gauges/indicators/pitch_electric_deg_pilot")
        self.planeRollDR = XPLMFindDataRef("sim/cockpit2/gauges/indicators/roll_electric_deg_pilot")
        self.planeSlipDR = XPLMFindDataRef("sim/cockpit2/gauges/indicators/slip_deg")
        self.planeBetaDR = XPLMFindDataRef("sim/flightmodel/position/beta")

        self.RollError = 0.0
        self.PitchError = 0.0
        self.SlipError = 0.0

        self.flightloopCB = self.flightloopCallback
        XPLMRegisterFlightLoopCallback(self, self.flightloopCB, 0.05, 0)
        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        XPLMUnregisterFlightLoopCallback(self, self.flightloopCB, 0)
        XPLMDestroyWindow(self, self.WindowId)
        pass

    def XPluginEnable(self):
        return 1

    def XPluginDisable(self):
        #XPLMUnregisterFlightLoopCallback(self, self.flightloopCB, 0)
        #XPLMDestroyWindow(self, self.WindowId)
        pass

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass
        
    #-----
    #Next section controls window in the sim
    #-----
        
    def DrawWindowCallback(self, inWindowID, inRefcon):
		lLeft = []; lTop = []; lRight = []; lBottom = []
		XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
		left = int(lLeft[0]); top= int(lTop[0]); right = int(lRight[0]); bottom = int(lBottom[0])
		gResult = XPLMDrawTranslucentDarkBox(left, top, right, bottom)
		colour = 1.0, 1.0, 1.0

		Desc = "Hello World 1"

		gResult = XPLMDrawString(colour, left + 5, top - 20, Desc, 0, xplmFont_Basic)
		pass

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass

	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 1
        
    #-----
    #Next section controls in-flight operation
    #-----

    def CalculateCtrlSrfDegInput(self, FDInputDeg, ActualInputDeg, CurrCtrlSrfDefDeg, CtrlSrfImpact, PreviousError):
        errorDeg = math.sqrt((FDInputDeg - ActualInputDeg + PreviousError) ** 2)
        maxCtrlSrfDefDeg = errorDeg/2 if (errorDeg/2 < 20) else 20
        maxCtrlSrfDefDeg = maxCtrlSrfDefDeg * CtrlSrfImpact
        if FDInputDeg + PreviousError < ActualInputDeg:
            maxCtrlSrfDefDeg = maxCtrlSrfDefDeg * (-1)
        desiredInput = CurrCtrlSrfDefDeg + (maxCtrlSrfDefDeg - CurrCtrlSrfDefDeg)
        return desiredInput
            
    def flightloopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        if (XPLMGetDatai(self.autopilotOnDR) == 2) and (XPLMGetDatai(self.landingLightsDR) == 0):
            XPLMSetDatai(self.controlsurfaceOvrDR, 1)
            
            # elvTrim is set because it used to run away and break default AP
            XPLMSetDataf(self.elvTrim, 0.0)
            
            self.RollError = round(self.RollError + (XPLMGetDataf(self.FDRollDR)
                - XPLMGetDataf(self.planeRollDR))/20.0, 4) if (self.RollError ** 2) < 16 else self.RollError * 0.99            
            self.PitchError = round(self.PitchError + (XPLMGetDataf(self.FDPitchDR)
                - XPLMGetDataf(self.planePitchDR))/20.0, 4) if (self.PitchError ** 2) < 16 else self.PitchError * 0.99            
            #self.SlipError = round(self.SlipError + (0.0 - 2*XPLMGetDataf(self.planeSlipDR)
            #    - XPLMGetDataf(self.rudd11DefDR))/20.0, 6) if (self.SlipError ** 2) < 64 else self.SlipError * 0.99

            #desiredRudInput = self.CalculateCtrlSrfDegInput(
            #0.0, XPLMGetDataf(self.planeSlipDR) - XPLMGetDataf(self.rudd11DefDR),
            #XPLMGetDataf(self.rudd11DefDR), 0.125, self.SlipError)

            desiredRudInput = -XPLMGetDataf(self.planeBetaDR)

            desiredRollInput = self.CalculateCtrlSrfDegInput(
            XPLMGetDataf(self.FDRollDR), XPLMGetDataf(self.planeRollDR),
            XPLMGetDataf(self.ail1LeftDefDR), self.RollSens, self.RollError)

            desiredPitchInput = self.CalculateCtrlSrfDegInput(
            XPLMGetDataf(self.FDPitchDR), XPLMGetDataf(self.planePitchDR),
            XPLMGetDataf(self.elev11DefDR), -self.PitchSens, self.PitchError)
            
            XPLMSetDataf(self.rudd11DefDR, desiredRudInput)            
            XPLMSetDataf(self.rudd12DefDR, desiredRudInput)            
            XPLMSetDataf(self.rudd21DefDR, desiredRudInput)            
            XPLMSetDataf(self.rudd22DefDR, desiredRudInput)
                
            XPLMSetDataf(self.ail1LeftDefDR, desiredRollInput)
            XPLMSetDataf(self.ail2LeftDefDR, desiredRollInput)            
            XPLMSetDataf(self.ail3LeftDefDR, desiredRollInput)            
            XPLMSetDataf(self.ail4LeftDefDR, desiredRollInput)            
            XPLMSetDataf(self.ail1RightDefDR, -desiredRollInput)            
            XPLMSetDataf(self.ail2RightDefDR, -desiredRollInput)            
            XPLMSetDataf(self.ail3RightDefDR, -desiredRollInput)            
            XPLMSetDataf(self.ail4RightDefDR, -desiredRollInput)
            
            XPLMSetDataf(self.elev11DefDR, desiredPitchInput)
            XPLMSetDataf(self.elev12DefDR, desiredPitchInput)
            XPLMSetDataf(self.elev21DefDR, desiredPitchInput)
            XPLMSetDataf(self.elev22DefDR, desiredPitchInput)
        else:
            XPLMSetDatai(self.controlsurfaceOvrDR, 0)
            self.RollError = 0.0
            self.PitchError = 0.0
            self.SlipError = 0.0
        return 0.05
