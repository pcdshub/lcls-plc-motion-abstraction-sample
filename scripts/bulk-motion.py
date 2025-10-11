from epics import PV
import time
import random
import argparse

def get_args():
    parser = argparse.ArgumentParser(
        description="EPICS Axis Batch Motion/Homing/Compensation Test Script"
    )
    parser.add_argument("--motor", type=str, required=True,
                        help="EPICS PV prefix for the axis, e.g. 'TST:MOTION:M1:'")
    parser.add_argument("--num-moves", type=int, default=5,
                        help="Number of normal moves to batch test (default: 5)")
    parser.add_argument("--offset", type=float, default=15.0,
                        help="User-specified magnitude (float) for all normal moves (default: 15.0). Sign alternates automatically.")
    parser.add_argument("--num-backlash", type=int, default=5,
                        help="Number of backlash compensation tests (default: 2)")
    parser.add_argument("--num-halt", type=int, default=0,
                        help="Number of halt-in-motion tests (default: 1)")
    parser.add_argument("--num-reset", type=int, default=0,
                        help="Number of reset-in-motion tests (default: 1)")
    parser.add_argument("--num-home", type=int, default=0,
                        help="Number of home-to-position tests (default: 1)")
    parser.add_argument("--avg-motion-time", type=float, default=2.5,
                        help="Average motion time (s) for normal/backlash moves")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="Print detailed debug info")
    return parser.parse_args()

args = get_args()
MOTOR = args.motor
num_moves = args.num_moves
user_offset = args.offset
num_backlash = args.num_backlash
num_halt = args.num_halt
num_reset = args.num_reset
num_home = args.num_home
AVG_TIME = args.avg_motion_time
VERBOSE = args.verbose

def vprint(*a, **kw):
    if VERBOSE:
        print(*a, **kw)

PVNAMES = {
    "MoveCmd":         MOTOR + "MoveCmd",
    "HomeCmd":         MOTOR + "HomeCmd",
    "bReset":           MOTOR + "bReset",
    "bHalt":            MOTOR + "bHalt",
    "fPosition":        MOTOR + "fPosition",
    "fHomePosition":    MOTOR + "fHomePosition",
    "fVelocity":        MOTOR + "fVelocity",
    "fAcceleration":    MOTOR + "fAcceleration",
    "fDeceleration":    MOTOR + "fDeceleration",
    "nCmdData":         MOTOR + "nCmdData",
    "nCommand":         MOTOR + "nCommand",
    "bBacklashEnable":  MOTOR + "bBacklashEnable",
    "fBacklash":    MOTOR + "fBacklash",
    "fActPosition":     MOTOR + "fActPosition_RBV",
    "bDone":            MOTOR + "bDone_RBV",
    "bBusy":            MOTOR + "bBusy_RBV",
    "bError":           MOTOR + "bError_RBV",
    "nErrorId":         MOTOR + "nErrorId_RBV",
    "bHomed":           MOTOR + "bHomed_RBV",
    "sErrorMessage":    MOTOR + "sErrorMessage_RBV",
    "bBacklashStatus":  MOTOR + "bBacklashStatus_RBV",
    "fCurrentBacklash": MOTOR + "fCurrentBacklash_RBV",
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
        v = PVs[key].get(timeout=1)
        if v == value:
            return True
        time.sleep(0.2)
    raise AssertionError(f"Timeout waiting for {key} == {value}")

def wait_move_and_check(target, pos_tol=0.03, timeout=10.0, expect_comp=None, comp_tol=0.01):
    done_flag = [False]
    fAct_positions = []  # Collect all observed positions

    def cb_fact(pvname=None, value=None, **_):
        fAct_positions.append(value)

    def cb_done(pvname=None, value=None, **_):
        if value:
            done_flag[0] = True

    PVs["fActPosition"].clear_callbacks()
    PVs["bDone"].clear_callbacks()
    PVs["fActPosition"].add_callback(cb_fact)
    PVs["bDone"].add_callback(cb_done)
    PVs["bDone"].use_monitor = True

    t0 = time.time()
    while not done_flag[0]:
        if time.time() - t0 > timeout:
            raise AssertionError("Timeout waiting for bDone")
        time.sleep(0.05)

    pos = PVs["fActPosition"].get(timeout=1.0)
    vprint(f"[INFO] Final position: {pos}, Target: {target}")
    assert_true(abs(pos - target) < pos_tol, f"Final position {pos} matches target {target}")

    if expect_comp is not None:
        fmeas = PVs["fCurrentBacklash"].get(timeout=1.0)
        vprint(f"[INFO] Measured compensation: {fmeas}, expected {expect_comp}")
        if abs(expect_comp) < 0.001:
            assert_true(abs(fmeas) < comp_tol, f"Measured compensation {fmeas} should be ~0")
        else:
            assert_true(abs(fmeas - expect_comp) < comp_tol, f"Measured compensation {fmeas} matches expected {expect_comp}")

    # Return all points history for summary/statistics if desired
    return fAct_positions

def move_abs_offset(
    offset, min_time=2.5, max_velocity=2200.0, max_accel=15000.0, expect_comp=None
):
    target = PVs["fActPosition"].get(timeout=1.0) + offset
    distance = abs(offset)
    velocity = max(15.0, min(max_velocity, distance / min_time))
    acceleration = deceleration = min(max_accel, velocity * 2.0)
    print(f"[MOVE_BULK] {target-offset:.2f} -> {target:.2f} [v={velocity}, a={acceleration}]")
    PVs["fPosition"].put(target, timeout=1.0)
    PVs["fVelocity"].put(velocity, timeout=1.0)
    PVs["fAcceleration"].put(acceleration, timeout=1.0)
    PVs["fDeceleration"].put(deceleration, timeout=1.0)
    PVs["nCommand"].put(1, timeout=1.0)
    PVs["MoveCmd"].put(1, timeout=1.0)
    fAct_points = wait_move_and_check(target, timeout=10.0, expect_comp=expect_comp)
    n_points = len(fAct_points)
    n_unique = len(set(fAct_points))
    print(f"[INFO] move_abs_offset - move offset={offset:.2f}: {n_points} b/w samples, {n_unique} unique fActPosition values till bDone")
    return fAct_points, n_points, n_unique

def exec_home(homepos, homemode, vel=50.0, acc=100.0, dec=100.0):
    PVs["fHomePosition"].put(homepos, timeout=1.0)
    PVs["fVelocity"].put(vel, timeout=1.0)
    PVs["fAcceleration"].put(acc, timeout=1.0)
    PVs["fDeceleration"].put(dec, timeout=1.0)
    PVs["nCmdData"].put(homemode, timeout=1.0)
    PVs["HomeCmd"].put(1, timeout=1.0)
    wait_pv_flag("bHomed", 1, timeout=14.0)
    home_actual = PVs["fActPosition"].get(timeout=2.0)
    print(f"[INFO] Homed to {home_actual} (expected {homepos})")
    assert_true(abs(home_actual - homepos) < 0.05, f"Final position {home_actual} is at expected home {homepos}")

def test_halt_or_reset(offset, do_halt=True):
    target = PVs["fActPosition"].get(timeout=1.0) + offset
    distance = abs(offset)
    velocity = max(15.0, min(2200.0, distance / 2.5))
    acceleration = deceleration = min(15000.0, velocity * 2.0)
    print(f"[MOVE] {target-offset:.2f} -> {target:.2f} [v={velocity}, a={acceleration}]")
    PVs["fPosition"].put(target, timeout=1.0)
    PVs["fVelocity"].put(velocity, timeout=1.0)
    PVs["fAcceleration"].put(acceleration, timeout=1.0)
    PVs["fDeceleration"].put(deceleration, timeout=1.0)
    PVs["nCommand"].put(1, timeout=1.0)
    PVs["MoveCmd"].put(1, timeout=1.0)
    time.sleep(0.3)
    t0 = time.time()
    while not PVs["bBusy"].get(timeout=0.7):
        if time.time() - t0 > 4.0:
            raise AssertionError("Axis never went busy after move start.")
        time.sleep(0.1)
    if do_halt:
        print("[HALT] Issuing HALT mid-move.")
        PVs["bHalt"].put(1, timeout=1.0)
        time.sleep(0.25)
        PVs["bHalt"].put(0, timeout=1.0)
    else:
        print("[RESET] Issuing RESET mid-move.")
        PVs["bReset"].put(1, timeout=1.0)
        time.sleep(0.25)
        PVs["bReset"].put(0, timeout=1.0)
    wait_pv_flag("bDone", 1, timeout=10.0)
    assert_true(PVs["bDone"].get(timeout=1.0) == 1, f"bDone was set after {'HALT' if do_halt else 'RESET'}.")
    print(f"[PASS] {('HALT' if do_halt else 'RESET')} validated: bDone set.")

def batch_move_tests(num_moves=5, num_backlash=2, num_halt=1, num_reset=1, num_home=1, avg_motion_time=2.5, user_offset=15.0):
    """
    Do num_moves normal moves: Each move uses 'user_offset' magnitude, sign alternates.
    Capture number of fActPosition samples for each move.
    """
    offsets = []
    if num_moves > 0:
        for i in range(num_moves):
            sign = 1 if i % 2 == 0 else -1
            offsets.append(sign * user_offset)
        print(f"  [BATCH] {num_moves} normal moves (offsets: {offsets})")
        move_samples = []
        test_num = 1
        for offset in offsets:
            print(f"   [#{test_num}] normal move, offset={offset:.2f}")
            all_points, n_points, n_unique = move_abs_offset(offset, min_time=avg_motion_time)
            move_samples.append((n_points, n_unique))
            print(f"      [REPORT] move #{test_num}: {n_points} sampled, {n_unique} unique fActPosition values till bDone=1")
            test_num += 1
        print("[SUMMARY] Per-move point counts (total, unique):", move_samples)

    if num_backlash > 0:
        print(f"  [BATCH] {num_backlash} backlash compensation moves")
        for i in range(num_backlash):
            BL = random.choice([1.7, -1.7])
            PVs["bBacklashEnable"].put(1, timeout=1.0)
            PVs["fBacklash"].put(BL, timeout=1.0)
            time.sleep(0.3)
            direction = random.choice([-1, 1])
            offset = direction * random.uniform(10.0, 20.0)
            move_dir = "forward" if direction > 0 else "reverse"
            compensated = (BL > 0 and direction < 0) or (BL < 0 and direction > 0)
            expect_comp = abs(BL) if compensated else 0.0
            comp_msg = (
                f"COMPENSATED: expect {expect_comp:.2f}"
                if compensated else "NO compensation"
            )
            print(
                f"   [backlash] move #{i + 1}: offset={offset:.2f}, direction={move_dir}, BL={BL:.2f}, {comp_msg}"
            )
            move_abs_offset(offset, min_time=avg_motion_time, expect_comp=expect_comp)

    if num_halt > 0:
        print(f"  [BATCH] {num_halt} halt-in-motion tests")
        for _ in range(num_halt):
            offset = random.choice([10.0, -10.0, 15.0, -15.0])
            print(f"   [halt] offset={offset:.2f}")
            test_halt_or_reset(offset, do_halt=True)

    if num_reset > 0:
        print(f"  [BATCH] {num_reset} reset-in-motion tests")
        for _ in range(num_reset):
            offset = random.choice([10.0, -10.0, 15.0, -15.0])
            print(f"   [reset] offset={offset:.2f}")
            test_halt_or_reset(offset, do_halt=False)

    if num_home > 0:
        print(f"  [BATCH] {num_home} home tests")
        for _ in range(num_home):
            homepos = random.uniform(-25.0, 25.0)
            print(f"   [home] home to {homepos:.2f}")
            exec_home(homepos=homepos, homemode=1)

# --- Main sequence starts here ---
check_connected()
print("[INFO] All key PVs connected.")

print("[STEP] Performing initial reset...")
PVs["bReset"].put(1, timeout=1.0); time.sleep(0.3); PVs["bReset"].put(0, timeout=1.0); time.sleep(0.3)
err = PVs["bError"].get(timeout=1.0)
errmsg = PVs["sErrorMessage"].get(as_string=True, timeout=1.0)
assert_false(err, f"Error after initial reset. Message: {errmsg}")
print('[PASS] Initial reset: no error, proceeding with batch moves.')

initial_pos = PVs["fActPosition"].get(timeout=2.0)
print(f"[INFO] Initial axis position: {initial_pos:.2f}")

batch_move_tests(
    num_moves=num_moves,
    num_backlash=num_backlash,
    num_halt=num_halt,
    num_reset=num_reset,
    num_home=num_home,
    avg_motion_time=AVG_TIME,
    user_offset=user_offset
)

print("[PASS] Batch move, error, halt, reset, and home simulation complete.")