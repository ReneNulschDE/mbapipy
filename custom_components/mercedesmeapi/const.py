MERCEDESME_COMPONENTS = [
    "sensor",
    "lock",
    "binary_sensor",
    "device_tracker",
    "switch"
]

BINARY_SENSORS = {

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
    "aux_heat": ["AUX HEAT", None,
                 "auxheat", "auxheatActive",
                 "value", "aux_heat", None, "heater"],

    "climate_control": ["CLIMATE CONTROL", None, "precond",
                        "preconditionState", "value",
                        "charging_clima_control", None, "climate"],
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
                 "sunroofstatus"}],

    "rangeElectricKm": ["Range electric", "Km", "electric", "rangeElectricKm",
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

    "auxheatstatus": ["auxheat status", None, "auxheat", "auxheatstatus",
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
                         "value", None, None],

    "odometer": ["Odometer", "Km", "odometer", "odo",
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
                     "batteryState"}],
}
