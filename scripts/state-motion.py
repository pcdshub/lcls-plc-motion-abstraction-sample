from epics import PV import time import sys import random import argparse def get_args():
    parser = argparse.ArgumentParser(
        description="EPICS Axis State Enum/Bulk Move Test Script"
    )
    parser.add_argument(
        "--motor", type=str, required=True,
        help="EPICS PV prefix for the axis, e.g. 'TST:MOTION:M1:'"
    )
    parser.add_argument(
        "--num-moves", type=int, default=5,
        help="Number of random state moves to test (default: 5)"
    )
    parser.add_argument(
        "-v", "--verbose", action='store_true',
        help="Print detailed debug info"
    )
    return parser.parse_args() args = get_args() MOTOR = args.motor num_moves = args.num_moves VERBOSE = args.verbose def vprint(*a, **kw):
    if VERBOSE:
        print(*a, **kw) PVNAMES = {
    "STATES:SET": MOTOR + "STATES:SET",
    "bReset": MOTOR + "bReset",
    "bHalt": MOTOR + "bHalt",
    "fActPosition": MOTOR + "fActPosition_RBV",
    "bDone": MOTOR + "bDone_RBV",
    "bBusy": MOTOR + "bBusy_RBV",
    "bError": MOTOR + "bError_RBV",
    "nErrorId": MOTOR + "nErrorId_RBV",
    "bHomed": MOTOR + "bHomed_RBV",
    "sErrorMessage": MOTOR + "sErrorMessage_RBV",
}
PVs = {key: PV(pvname) for key, pvname in PVNAMES.items()} def assert_true(cond, msg):
    if not cond:
        print('[FAIL]', msg)
        raise AssertionError(msg)
    print('[PASS]', msg) def assert_false(cond, msg):
    assert_true(not cond, msg) def check_connected():
    for key, pv in PVs.items():
        if not pv.wait_for_connection(timeout=2.0):
            raise Exception(f"PV {key} ({pv.pvname}) not connected!") def wait_pv_flag(key, value=1, timeout=14.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = PVs[key].get(timeout=1)
        if v == value:
            return True
        time.sleep(0.2)
    raise AssertionError(f"Timeout waiting for {key} == {value}") def wait_move_done(timeout=10.0):
    done_flag = [False]
    def cb_done(pvname=None, value=None, **_):
        if value: done_flag[0] = True
    PVs["bDone"].add_callback(cb_done)
    PVs["bDone"].use_monitor = True
    t0 = time.time()
    while not done_flag[0]:
        if time.time() - t0 > timeout:
            raise AssertionError("Timeout waiting for bDone")
        time.sleep(0.2)
    vprint("[INFO] Move done detected.") def move_to_state(state_enum):
    print(f"[STEP] Move to state {state_enum}")
    PVs["STATES:SET"].put(int(state_enum), timeout=1.0)
    wait_move_done() def test_halt_or_reset_state(state_enum, do_halt=True):
    print(f"[STEP] Move to state {state_enum} with {'HALT' if do_halt else 'RESET'}")
    PVs["STATES:SET"].put(int(state_enum), timeout=1.0)
    # Wait for busy
    t0 = time.time()
    while not PVs["bBusy"].get(timeout=0.7):
        if time.time() - t0 > 7.0:
            raise AssertionError("Axis never went busy after move start.")
        time.sleep(0.1)
    # After a short move, trigger halt/reset
    time.sleep(0.6)
    if do_halt:
        PVs["bHalt"].put(1, timeout=1.0)
        time.sleep(0.3)
        PVs["bHalt"].put(0, timeout=1.0)
    else:
        PVs["bReset"].put(1, timeout=1.0)
        time.sleep(0.3)
        PVs["bReset"].put(0, timeout=1.0)
    wait_pv_flag("bDone", 1, timeout=10.0)
    assert_true(PVs["bDone"].get(timeout=1.0) == 1,
                f"bDone should be set after {'HALT' if do_halt else 'RESET'}")
    print(f"[PASS] Move with {'HALT' if do_halt else 'RESET'} completed.")
# --- Main test sequence ---
check_connected() print("[INFO] All key PVs connected.") print("[STEP] Performing initial reset...") PVs["bReset"].put(1, timeout=1.0) 
time.sleep(0.4) PVs["bReset"].put(0, timeout=1.0) time.sleep(0.4) err = PVs["bError"].get(timeout=1.0) errmsg = 
PVs["sErrorMessage"].get(as_string=True, timeout=1.0) assert_false(err, f"Error after initial reset. Message: {errmsg}") print('[PASS] Initial 
reset: no error, proceeding with state moves.')
# Assume ENUM_AxisStates values 1..15 for your axis (0 is UNKNOWN)
STATE_ENUMS = list(range(1, 16))
# 1. Move through all defined states
for state in STATE_ENUMS:
    move_to_state(state)
# 2. Test halt/reset at random states
for _ in range(2):
    state = random.choice(STATE_ENUMS)
    test_halt_or_reset_state(state_enum=state, do_halt=True)
    test_halt_or_reset_state(state_enum=state, do_halt=False)
# 3. Batch random moves with errors/halts/resets
print(f"[STEP] Batch testing {num_moves} random state moves/includes halt/errors/resets") for i in range(num_moves):
    state = random.choice(STATE_ENUMS)
    movetype = random.choice(['normal', 'halt', 'reset', 'error'])
    print(f" [BATCH MOVE] #{i+1}: {movetype}, state={state}")
    if movetype == 'normal':
        move_to_state(state)
    elif movetype == 'halt':
        test_halt_or_reset_state(state_enum=state, do_halt=True)
    elif movetype == 'reset':
        test_halt_or_reset_state(state_enum=state, do_halt=False)
    elif movetype == 'error':
        print("[ERROR] Sending to UNKNOWN state to trigger fault")
        PVs["STATES:SET"].put(0, timeout=1.0)
        time.sleep(1.0)
        assert_true(PVs["bError"].get(timeout=1.0),
                    "Should get error for unknown state command")
        PVs["bReset"].put(1, timeout=1.0)
        time.sleep(0.5)
        PVs["bReset"].put(0, timeout=1.0)
        wait_pv_flag("bError", 0, timeout=6)
        print("[PASS] Error/fault recovered after reset.")
print("[PASS] All state move, halt, and reset tests complete.")

