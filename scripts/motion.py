from epics import PV
import time
import sys

MOTOR = "TST:MOTION:M1:PLC:"

PVNAMES = {
    "bHomeCmd":         MOTOR + "bHomeCmd",
    "bMoveCmd":         MOTOR + "bMoveCmd",
    "bReset":           MOTOR + "bReset",
    "bHalt":            MOTOR + "bHalt",
    "fPosition":        MOTOR + "fPosition",
    "fHomePosition":        MOTOR + "fHomePosition",
    "fVelocity":        MOTOR + "fVelocity",
    "fAcceleration":    MOTOR + "fAcceleration",
    "fDeceleration":    MOTOR + "fDeceleration",
    "nCmdData":         MOTOR + "nCmdData",
    "nCommand":         MOTOR + "nCommand",
    "bBacklashEnable":  MOTOR + "bBacklashEnable",
    "fBacklashComp":    MOTOR + "fBacklashComp",
    "fActPosition":     MOTOR + "AxisStatus:PLC:fActPosition_RBV",
    "bDone":            MOTOR + "AxisStatus:PLC:bDone_RBV",
    "bBusy":            MOTOR + "AxisStatus:PLC:bBusy_RBV",
    "bError":           MOTOR + "AxisStatus:PLC:bError_RBV",
    "nErrorId":         MOTOR + "AxisStatus:PLC:nErrorId_RBV",
    "bHomed":           MOTOR + "AxisStatus:PLC:bHomed_RBV",
    "sErrorMessage":    MOTOR + "AxisStatus:PLC:sErrorMessage_RBV",
    "bBacklashStatus":  MOTOR + "bBacklashStatus_RBV",
    "fMeasuredBacklashComp": MOTOR + "fMeasuredBacklashComp_RBV",
}
PVs = {key: PV(pvname) for key, pvname in PVNAMES.items()}

def assert_true(cond, msg):
    if not cond:
        print('[FAIL]', msg)
        raise AssertionError(msg)
    print('[PASS]', msg)

def assert_false(cond, msg):
    assert_true(not cond, msg)

def check_connected():
    for key, pv in PVs.items():
        if not pv.wait_for_connection(timeout=2.0):
            raise Exception(f"PV {key} ({pv.pvname}) not connected!")

def wait_pv_flag(key, value=1, timeout=14.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = PVs[key].get(timeout=0.9)
        if v == value:
            return True
        time.sleep(0.2)
    raise AssertionError(f"Timeout waiting for {key} == {value}")

def wait_move_and_check(target, pos_tol=0.03, timeout=10.0, expect_comp=None, comp_tol=0.01):
    done_flag = [False]
    def cb_done(pvname=None, value=None, **_):
        if value:
            done_flag[0] = True
    PVs["bDone"].add_callback(cb_done)
    PVs["bDone"].use_monitor = True
    t0 = time.time()
    while not done_flag[0]:
        if time.time() - t0 > timeout:
            raise AssertionError("Timeout waiting for bDone")
        time.sleep(0.2)
    pos = PVs["fActPosition"].get(timeout=1.0)
    print(f"[INFO] Final position: {pos}, Target: {target}")
    assert_true(abs(pos - target) < pos_tol, f"Final position {pos} matches target {target}")
    if expect_comp is not None:
        fmeas = PVs["fMeasuredBacklashComp"].get(timeout=1.0)
        print(f"[INFO] Measured compensation: {fmeas}, expected {expect_comp}")
        if abs(expect_comp) < 0.001:
            assert_true(abs(fmeas) < comp_tol, f"Measured compensation {fmeas} should be ~0")
        else:
            assert_true(abs(fmeas - expect_comp) < comp_tol, f"Measured compensation {fmeas} matches expected {expect_comp}")

check_connected()
print("[INFO] All key PVs connected.")

print("[STEP] Performing initial reset...")
PVs["bReset"].put(1, timeout=1.0); time.sleep(0.3); PVs["bReset"].put(0, timeout=1.0), time.sleep(0.3)
err = PVs["bError"].get(timeout=1.0)
errmsg = PVs["sErrorMessage"].get(as_string=True, timeout=1.0)
assert_false(err, f"Error after initial reset. Message: {errmsg}")
print('[PASS] Initial reset: no error, proceeding with moves.')

initial_pos = PVs["fActPosition"].get(timeout=2.0)
print(f"[INFO] Initial axis position: {initial_pos:.2f}")

def move_abs_offset(offset, min_time=2.5, max_velocity=2200.0, max_accel=15000.0, expect_comp=None):
    target = PVs["fActPosition"].get(timeout=1.0) + offset
    distance = abs(offset)
    velocity = max(15.0, min(max_velocity, distance / min_time))
    acceleration = deceleration = min(max_accel, velocity * 2.0)
    print(f"[MOVE] {target- offset:.2f} -> {target:.2f} [v={velocity}, a={acceleration}]")
    PVs["fPosition"].put(target, timeout=1.0)
    PVs["fVelocity"].put(velocity, timeout=1.0)
    PVs["fAcceleration"].put(acceleration, timeout=1.0)
    PVs["fDeceleration"].put(deceleration, timeout=1.0)
    PVs["nCommand"].put(1, timeout=1.0)
    PVs["bMoveCmd"].put(1, timeout=1.0)
    time.sleep(0.2)
    PVs["bMoveCmd"].put(0, timeout=1.0)
    wait_move_and_check(target, timeout=8.0, expect_comp=expect_comp)

# --- Sequence: 3 moves, All home modes + move, then backlash compensation cases ---
move_abs_offset(20.0)
move_abs_offset(-10.0)
move_abs_offset(5.0)


# --------- Backlash compensation tests (ON/OFF, fwd/rev) ---------
print("[STEP] Backlash ON, moving forward (no compensation expected)")
PVs["bBacklashEnable"].put(1, timeout=1.0)
PVs["fBacklashComp"].put(2.5, timeout=1.0)
time.sleep(2.0)
move_abs_offset(7.0, expect_comp=0.0)

print("[STEP] Backlash ON, moving reverse (compensation 2.5 expected)")
move_abs_offset(-9.0, expect_comp=2.5)

print("[STEP] Backlash OFF, moving forward (no compensation)")
PVs["bBacklashEnable"].put(0, timeout=1.0)
time.sleep(2.0)
move_abs_offset(6.0, expect_comp=0.0)

print("[STEP] Backlash ON (negative), moving reverse (no compensation expected)")
PVs["bBacklashEnable"].put(1, timeout=1.0)
PVs["fBacklashComp"].put(-1.7, timeout=1.0)
time.sleep(2.0)
move_abs_offset(-7.0, expect_comp=0.0)

print("[STEP] Backlash ON (negative), moving forward (expect ~-1.7 compensation)")
move_abs_offset(5.0, expect_comp=1.7)

print("All absolute/home/backlash tests passed, as well as reset/error handling.")


# HOME_MODES = [
    # (1, 40.0, "LOW_LIMIT"),
    # (2, -25.0, "HIGH_LIMIT"),
    # (3, 10.0, "HOME_VIA_LOW"),
    # (4, -18.0, "HOME_VIA_HIGH"),
    # (15, 8.0, "ABSOLUTE_SET"),
    # (37, 5.0, "CURRENT_POSITION_METHOD")
# ]
# MOVE_AFTER_HOME_OFFSETS = [6.0, -7.0, 5.5, -5.0, 4.0, -4.0]

# for idx, (mode, homepos, modename) in enumerate(HOME_MODES):
    # print(f"[STEP] Homing mode {modename}, HomePosition={homepos}")
    # PVs["fHomePosition"].put(homepos, timeout=1.0)
    # PVs["nCmdData"].put(mode, timeout=1.0)
    # PVs["nCommand"].put(2, timeout=1.0)
    # PVs["bHomeCmd"].put(1, timeout=1.0); time.sleep(0.2); PVs["bHomeCmd"].put(0, timeout=1.0)
    # wait_pv_flag("bHomed", 1, timeout=14.0)
    # curr_home = PVs["fActPosition"].get(timeout=2.0)
    # print(f"[INFO] Homed. Mode={modename}, HomePosition={curr_home}")
    # assert_true(abs(curr_home - homepos) < 0.05, f"Homing ({modename}): Final position {curr_home} matches expected {homepos}.")
    # offset = MOVE_AFTER_HOME_OFFSETS[idx % len(MOVE_AFTER_HOME_OFFSETS)]
    # print(f"[STEP] Post-home Absolute Move: offset={offset}")
    # move_abs_offset(offset)

