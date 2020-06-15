from homeassistant.const import (
    LENGTH_KILOMETERS)

MERCEDESME_COMPONENTS = [
    "sensor",
    "lock",
    "binary_sensor",
    "device_tracker",
    "switch"
]

BINARY_SENSORS = {

    "liquidRangeCritical": ["Liquid Range Critical",
                            None,
                            "binarysensors",
                            "liquidRangeCritical",
                            "value",
                            None,
                            None],

    "warningbrakefluid": ["Low Brake Fluid Warning",
                          None,
                          "binarysensors",
                          "warningbrakefluid",
                          "value",
                          None,
                          None],

    "warningwashwater": ["Low Wash Water Warning",
                         None,
                         "binarysensors",
                         "warningwashwater",
                         "value",
                         None,
                         None],

    "warningcoolantlevellow": ["Low Coolant Level Warning",
                               None,
                               "binarysensors",
                               "warningcoolantlevellow",
                               "value",
                               None,
                               None],


    "warninglowbattery": ["Low Battery Warning",
                          None,
                          "binarysensors",
                          "warninglowbattery",
                          "value",
                          None,
                          None],

    "warningenginelight": ["Engine Light Warning",
                           None,
                           "binarysensors",
                           "warningenginelight",
                           "value",
                           None,
                           {
                               "warningbrakefluid",
                               "warningwashwater",
                               "warningcoolantlevellow",
                               "warninglowbattery"}],

    "parkbrakestatus": ["Park Brake Status",
                        None,
                        "binarysensors",
                        "parkbrakestatus",
                        "value",
                        None,
                        {
                            "preWarningBrakeLiningWear"}],

    "windowsClosed": ["Windows Closed",
                      None, "windows",
                      "windowsClosed",
                      "value",
                      None,
                      {
                          "windowstatusrearleft",
                          "windowstatusrearright",
                          "windowstatusfrontright",
                          "windowstatusfrontleft"}],

    "tirewarninglamp": ["Tire Warning",
                        None,
                        "tires",
                        "OVERWRITTEN_IN_BINARY_SENSOR",
                        "value",
                        None,
                        {
                            "tirepressureRearLeft",
                            "tirepressureRearRight",
                            "tirepressureFrontRight",
                            "tirepressureFrontLeft",
                            "tirewarningsrdk",
                            "tirewarningsprw",
                            "tireMarkerFrontRight",
                            "tireMarkerFrontLeft",
                            "tireMarkerRearLeft",
                            "tireMarkerRearRight",
                            "tireWarningRollup",
                            "tirewarninglamp",
                            "lastTirepressureTimestamp"}]
}

LOCKS = {
    "lock": ["Lock", None, "doors", "locked", "value", "remote_door_lock"],
}

SWITCHES = {
    "aux_heat": [
        "Aux Heat", None,
        "auxheat", "auxheatActive",
        "value", "aux_heat", None, "heater"],

    "climate_control": [
        "Climate Control", None, "precond",
        "preconditionState", "value",
        "charging_clima_control", None, "climate"],

    "remote_start": [
        "Remote Start", None, "remote_start",
        "remoteEngine", "value",
        "remote_engine_start",
        {
            "remoteEngine",
            "remoteStartEndtime",
            "remoteStartTemperature"},
        "remote_start"],
}

SENSORS = {
    "lock": ["Lock", None, "doors", "locked", "value", None,
             {
                 "fuelLidClosed",
                 "doorStateFrontLeft",
                 "doorStateFrontRight",
                 "doorStateRearLeft",
                 "doorStateRearRight",
                 "frontLeftDoorLocked",
                 "frontRightDoorLocked",
                 "rearLeftDoorLocked",
                 "rearRightDoorLocked",
                 "frontLeftDoorClosed",
                 "frontRightDoorClosed",
                 "rearLeftDoorClosed",
                 "rearRightDoorClosed",
                 "rearRightDoorClosed",
                 "doorsClosed",
                 "trunkStateRollup",
                 "sunroofstatus",
                 "engineHoodClosed", }],

    "rangeElectricKm": ["Range Electric", LENGTH_KILOMETERS,
                        "electric", "rangeElectricKm",
                        "value", "charging_clima_control",
                        {
                            "rangeelectric",
                            "rangeElectricKm",
                            "criticalStateOfSoc",
                            "maxrange",
                            "stateOfChargeElectricPercent",
                            "endofchargetime",
                            "criticalStateOfDeparturetimesoc",
                            "warninglowbattery",
                            "electricconsumptionreset",
                            "maxStateOfChargeElectricPercent",
                            "supplybatteryvoltage",
                            "electricChargingStatus",
                            "chargingstatus",
                            "soc",
                            "showChargingErrorAndDemand",
                            "electricconsumptionstart"}],

    "auxheatstatus": ["Auxheat Status", None, "auxheat", "auxheatstatus",
                      "value", "aux_heat",
                      {
                          "auxheatActive",
                          "auxheatwarnings",
                          "auxheatruntime",
                          "auxheatwarningsPush",
                          "auxheattimeselection",
                          "auxheattime1",
                          "auxheattime2",
                          "auxheattime3"}],

    "tanklevelpercent": ["Fuel Level", "%", "odometer", "tanklevelpercent",
                         "value", None,
                         {
                             "tankLevelAdBlue"
                         }],

    "odometer": ["Odometer", LENGTH_KILOMETERS, "odometer", "odo",
                 "value", None,
                 {
                     "distanceReset",
                     "distanceStart",
                     "averageSpeedReset",
                     "averageSpeedStart",
                     "distanceZEReset",
                     "drivenTimeZEReset",
                     "drivenTimeReset",
                     "drivenTimeStart",
                     "ecoscoretotal",
                     "ecoscorefreewhl",
                     "ecoscorebonusrange",
                     "ecoscoreconst",
                     "ecoscoreaccel",
                     "gasconsumptionstart",
                     "gasconsumptionreset",
                     "gasTankRange",
                     "gasTankLevel",
                     "liquidconsumptionstart",
                     "liquidconsumptionreset",
                     "liquidRangeSkipIndication",
                     "rangeliquid",
                     "serviceintervaldays",
                     "tanklevelpercent",
                     "tankReserveLamp",
                     "batteryState",
                     "tankLevelAdBlue"}],

    "car_alarm": ["Car Alarm", None, "car_alarm", "carAlarm",
                  "value", 'car_alarm',
                  {
                      "lastTheftWarning",
                      "towSensor",
                      "theftSystemArmed",
                      "parkEventType",
                      "parkEventLevel",
                      "carAlarmLastTime",
                      "towProtectionSensorStatus",
                      "theftAlarmActive",
                      "lastTheftWarningReason",
                      "lastParkEvent",
                      "collisionAlarmTimestamp",
                      "interiorSensor",
                      "carAlarmReason"}],

}
