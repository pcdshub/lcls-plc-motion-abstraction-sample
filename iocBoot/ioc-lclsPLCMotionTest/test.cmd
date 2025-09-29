#!/opt/epics/iocs/ads-ioc/R1.0.0/bin/rhel9-x86_64/adsIoc
################### AUTO-GENERATED DO NOT EDIT ###################
#
#         Project: lcls-motion-test.tsproj
#        PLC name: lclsPLCMotionTest (lclsPLCMotionTest Instance)
# Generated using: pytmc 2.18.3.dev2+g94c62dbb0
# Project version: unknown
#    Project hash: unknown
#     PLC IP/host: 192.168.1.172
#      PLC Net ID: 192.168.1.172.1.1
# ** DEVELOPMENT MODE IOC **
# * Using IOC boot directory for autosave.
# * Archiver settings will not be configured.
#
# Libraries:
#
#   LCLS General: * (SLAC)
#   LCLS_OMotion: * (SLAC)
#   Tc2_MC2: * (Beckhoff Automation GmbH)
#   Tc2_NC: * (Beckhoff Automation GmbH)
#   Tc2_Standard: * -> 3.4.5.0 (Beckhoff Automation GmbH)
#   Tc2_System: * (Beckhoff Automation GmbH)
#   Tc3_Module: * (Beckhoff Automation GmbH)
#
################### AUTO-GENERATED DO NOT EDIT ###################
# Run common startup commands for linux soft IOC's
< envPaths

epicsEnvSet("ADS_IOC_TOP", "$(TOP)" )

epicsEnvSet("ENGINEER", "epics-dev" )
epicsEnvSet("LOCATION", "PLC:lclsPLCMotionTest" )
epicsEnvSet("IOCSH_PS1", "$(IOC)> " )

# Register all support components
dbLoadDatabase("$(ADS_IOC_TOP)/dbd/adsIoc.dbd")
adsIoc_registerRecordDeviceDriver(pdbbase)

epicsEnvSet("ASYN_PORT",        "ASYN_PLC")
epicsEnvSet("IPADDR",           "192.168.1.172")
epicsEnvSet("AMSID",            "192.168.1.172.1.1")
epicsEnvSet("AMS_PORT",         "851")
epicsEnvSet("ADS_MAX_PARAMS",   "1070")
epicsEnvSet("ADS_SAMPLE_MS",    "50")
epicsEnvSet("ADS_MAX_DELAY_MS", "1000")
epicsEnvSet("ADS_TIMEOUT_MS",   "5000")
epicsEnvSet("ADS_TIME_SOURCE",  "0")

# Add a route to the PLC automatically:
system("${ADS_IOC_TOP}/scripts/add_route.sh 192.168.1.172 ^192.*$")

adsAsynPortDriverConfigure("$(ASYN_PORT)", "$(IPADDR)", "$(AMSID)", "$(AMS_PORT)", "$(ADS_MAX_PARAMS)", 0, 0, "$(ADS_SAMPLE_MS)", "$(ADS_MAX_DELAY_MS)", "$(ADS_TIMEOUT_MS)", "$(ADS_TIME_SOURCE)")

cd "$(ADS_IOC_TOP)/db"


epicsEnvSet("MOTOR_PORT",     "PLC_ADS")
epicsEnvSet("PREFIX",         "PLC:lclsPLCMotionTest:")
epicsEnvSet("NUMAXES",        "2")
epicsEnvSet("MOVE_POLL_RATE", "200")
epicsEnvSet("IDLE_POLL_RATE", "1000")

#define ASYN_TRACE_ERROR     0x0001
#define ASYN_TRACEIO_DEVICE  0x0002
#define ASYN_TRACEIO_FILTER  0x0004
#define ASYN_TRACEIO_DRIVER  0x0008
#define ASYN_TRACE_FLOW      0x0010
#define ASYN_TRACE_WARNING   0x0020
#define ASYN_TRACE_INFO      0x0040
#asynSetTraceMask("$(ASYN_PORT)", -1, 0x41)
#asynSetTraceMask("$(ASYN_PORT)", -1, ASYN_TRACEIO_DRIVER|ASYN_TRACE_INFO|ASYN_TRACE_ERROR)

#define ASYN_TRACEIO_NODATA 0x0000
#define ASYN_TRACEIO_ASCII  0x0001
#define ASYN_TRACEIO_ESCAPE 0x0002
#define ASYN_TRACEIO_HEX    0x0004
asynSetTraceIOMask("$(ASYN_PORT)", -1, 2)

#define ASYN_TRACEINFO_TIME 0x0001
#define ASYN_TRACEINFO_PORT 0x0002
#define ASYN_TRACEINFO_SOURCE 0x0004
#define ASYN_TRACEINFO_THREAD 0x0008
asynSetTraceInfoMask("$(ASYN_PORT)", -1, 5)

#define AMPLIFIER_ON_FLAG_CREATE_AXIS  1
#define AMPLIFIER_ON_FLAG_WHEN_HOMING  2
#define AMPLIFIER_ON_FLAG_USING_CNEN   4

epicsEnvSet("AXIS_NO",         "1")
epicsEnvSet("MOTOR_PREFIX",    "TST:MOTION:")
epicsEnvSet("MOTOR_NAME",      "M1")
epicsEnvSet("MOTOR_ADS_PATH",  "MAIN.fbMotionStage")
epicsEnvSet("DESC",            "MAIN.fbMotionStage / Axis 1")
epicsEnvSet("EGU",             "mm")
epicsEnvSet("PREC",            "3")
epicsEnvSet("AXISCONFIG",      "")
epicsEnvSet("ECAXISFIELDINIT", "")
epicsEnvSet("AMPLIFIER_FLAGS", "")

## Load EPICS base, asyn, StreamDevice, and ADS support
epicsEnvSet("STREAM_PROTOCOL_PATH", "$(IOC_TOP)")

cd "$(IOC_TOP)"

## PLC Project Database files ##
dbLoadRecords("lclsPLCMotionTest.db", "PORT=$(ASYN_PORT),PREFIX=PLC:lclsPLCMotionTest:,IOCNAME=$(IOC),IOC=$(IOC)")

## Load DB file for the axis group
dbLoadRecords("motor.db", "PORT=$(ASYN_PORT), ADSPORT=$(AMS_PORT), ADSPATH=$(MOTOR_ADS_PATH), PREFIX=$(MOTOR_PREFIX), M=$(MOTOR_NAME)")


# Total records: 70
callbackSetQueueSize(2140)

# ** Development IOC Settings **
# Development IOC autosave and archive files go in the IOC top directory:
cd "$(IOC_TOP)"

# Initialize the IOC and start processing records
iocInit()


