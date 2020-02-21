# mbapipy

MercedesME platform as a Custom Component for Home Assistant.

IMPORTANT: 

* Please login once in the MercedesME IOS or Android app before you install this component. 
* For US/CA the app name is "MercedesME Connect" (only newer cars are supported in this region)

Configuration:
```
mercedesmeapi:
  username: YOUR_USERNAME
  password: YOUR_PASSWORD
```

Optional configuration values
```
mercedesmeapi:
  username: YOUR_USERNAME
  password: YOUR_PASSWORD
  pin: XXXX                           # required to open the lock or to start the engine, please use the Mercedes web or app to set-up the pin
  
  country_code: DE                    # two digts country code
  accept_lang: en_DE                  # four digits country code
  save_car_details: true              # save a json to the HA config directory with the features and states, please use this for debug only 
  cars:                               # Optional block to overwrite car specific options
    - vin: FINXXXXXXXXXXXXX1          # required finorvin
      tire_warning: tirewarninglamp   # optional attributname for tire_warning binary sensor. some cars use tireWarningRollup or tirewarninglamp 
    - vin: FINXXXXXXXXXXXXX2
      tire_warning: tireWarningRollup
```

Available components:
* Lock
* Remote Start Switch
* Aux Heat Switch

* Binary Sensors:
```
* warningenginelight
  attributes: warningbrakefluid, warningwashwater, warningcoolantlevellow, warninglowbattery

* parkbrakestatus
  attributes: preWarningBrakeLiningWear

* windowsClosed
  attributes: windowstatusrearleft, windowstatusrearright, windowstatusfrontright, windowstatusfrontleft

* tirewarninglamp
  attributes: tirepressureRearLeft, tirepressureRearRight, tirepressureFrontRight, tirepressureFrontLeft, tirewarningsrdk, tirewarningsprwtireMarkerFrontRight, tireMarkerFrontLeft, tireMarkerRearLeft, tireMarkerRearRight, tireWarningRollup, lastTirepressureTimestamp
```

* Sensors:
```
* lock
  attributes: doorStateFrontLeft, doorStateFrontRight, doorStateRearLeft, doorStateRearRight, frontLeftDoorLocked, frontRightDoorLocked, rearLeftDoorLocked, rearRightDoorLocked, frontLeftDoorClosed, frontRightDoorClosed, rearLeftDoorClosed, rearRightDoorClosed, rearRightDoorClosed, doorsClosed, trunkStateRollup, sunroofstatus, fuelLidClosed, engineHoodClosed

* rangeElectricKm
  attributes: rangeelectric, rangeElectricKm, criticalStateOfSoc, maxrange, stateOfChargeElectricPercent, endofchargetime, criticalStateOfDeparturetimesoc, warninglowbattery, electricconsumptionreset, maxStateOfChargeElectricPercent, supplybatteryvoltage, electricChargingStatus, chargingstatus, soc, showChargingErrorAndDemand, electricconsumptionstart
  
* auxheatstatus
  attributes: auxheatActive, auxheatwarnings, auxheatruntime, auxheatwarningsPush, auxheattimeselection, auxheattime1, auxheattime2, auxheattime3

* tanklevelpercent

* odometer
  attributes: distanceReset, distanceStart, averageSpeedReset, averageSpeedStart, distanceZEReset, drivenTimeZEReset, drivenTimeReset, drivenTimeStart, ecoscoretotal, ecoscorefreewhl, ecoscorebonusrange, ecoscoreconst, ecoscoreaccel, gasconsumptionstart, gasconsumptionreset, gasTankRange, gasTankLevel, liquidconsumptionstart, liquidconsumptionreset, liquidRangeSkipIndication, rangeliquid, serviceintervaldays, tanklevelpercent, tankReserveLamp, batteryState
  
```


Logging:
Set the logging to debug with the following settings in case of problems.
```
logger:
  default: warn
  logs:
    custom_components.mercedesmeapi: debug
    custom_components.mercedesmeapi.sensor: info
    custom_components.mercedesmeapi.apicontroller: debug
    custom_components.mercedesmeapi.OAuth: debug
```


Notes:
- Tested countries: CA, DE, DK, ES, FI, NL, PL, UK, US
- For Canada please use Country Code US currently
- Cars out of North America and Europe can't be used at the same time