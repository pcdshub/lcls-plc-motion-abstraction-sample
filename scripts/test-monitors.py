import epics
import time

def monitor_and_print_on_change(pvname):
    """
    Registers a monitor and prints each time the PV value changes.
    """
    pv = epics.PV(pvname)
    if not pv.wait_for_connection(timeout=2.0):
        raise RuntimeError(f"Cannot connect to {pvname}")

    print(f"[INFO] Monitoring {pvname} for value changes...")
    def cb(pvname=None, value=None, **kw):
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[MONITOR] {pvname} changed to {value} at {t}")

    # Register the callback and turn on monitoring
    pv.add_callback(cb)
    pv.use_monitor = True

    # Stay alive and print value changes for 30 seconds
    t0 = time.time()
    while time.time() - t0 < 60:
        time.sleep(0.1)
    # Unregister callback (optional cleanup)
    pv.clear_callbacks()
    print("[INFO] Done monitoring.")

# Usage example for your bDone PV:
MOTOR = "TST:MOTION:M1:PLC:"
bDonePV = MOTOR + "AxisStatus:PLC:bDone_RBV"
monitor_and_print_on_change(bDonePV)
