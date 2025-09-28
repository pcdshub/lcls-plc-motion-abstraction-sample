import epics
import time

MOTOR = "TST:MOTION:M1:PLC:"

PVS = {
    "bMoveCmd":      MOTOR + "bMoveCmd",
    "fPosition":     MOTOR + "fPosition",
    "fVelocity":     MOTOR + "fVelocity",
    "fAcceleration": MOTOR + "fAcceleration",
    "fDeceleration": MOTOR + "fDeceleration",
    "nCommand":      MOTOR + "nCommand",
    "bDone":         MOTOR + "AxisStatus:PLC:bDone_RBV",
    "bBusy":         MOTOR + "AxisStatus:PLC:bBusy_RBV",
    "fActPosition":  MOTOR + "AxisStatus:PLC:fActPosition_RBV",
}

PVs = {key: epics.PV(val) for key, val in PVS.items()}

def assert_true(cond, msg):
    if not cond:
        print("[FAIL]", msg)
        raise AssertionError(msg)
    print("[PASS]", msg)

def check_connected():
    for key, pv in PVs.items():
        if not pv.wait_for_connection(timeout=2.0):
            raise Exception(f"PV {key} ({pv.pvname}) not connected!")

def debug_move_and_done_rising_edge(target):
    got_rising_edge = [False]
    prev_val = [PVs["bDone"].get(timeout=1.0)]  # Initial state (could be 1 or 0)

    def cb_done(pvname=None, value=None, **kws):
        prev, curr = prev_val[0], value
        # Print both prev and curr so you can debug unexpected behavior.
        print(f"[CALLBACK] bDone: prev={prev}, curr={curr}")
        # Look for 0 -> 1 transition only
        if prev == 0 and curr == 1:
            got_rising_edge[0] = True
            print(f"[EVENT] Rising edge on bDone detected (move complete)!")
        prev_val[0] = curr

    PVs["bDone"].add_callback(cb_done)
    PVs["bDone"].use_monitor = True

    # --- Command Absolute Move
    PVs["fPosition"].put(target, timeout=1.0)
    PVs["fVelocity"].put(50.0, timeout=1.0)
    PVs["fAcceleration"].put(100.0, timeout=1.0)
    PVs["fDeceleration"].put(100.0, timeout=1.0)
    PVs["nCommand"].put(1, timeout=1.0)
    PVs["bMoveCmd"].put(1, timeout=1.0)
    time.sleep(0.1)
    PVs["bMoveCmd"].put(0, timeout=1.0)

    print("[INFO] Waiting for bDone rising edge after move command...")

    t0 = time.time()
    timeout = 5.0 # (5 seconds is more than enough for test)
    while not got_rising_edge[0]:
        if time.time() - t0 > timeout:
            raise AssertionError("Timeout waiting for bDone rising edge")
        time.sleep(0.01)

    # Final assertion: that we truly are at target
    pos = PVs["fActPosition"].get(timeout=1.0)
    assert_true(abs(pos - target) < 0.05, f"Final position {pos} matches target {target}")

print("[INFO] Connecting to all required PVs...")
check_connected()

print("[TEST] Starting absolute move and waiting for bDone rising edge...")
debug_move_and_done_rising_edge(120.0)

print("Finished move and bDone test.")
