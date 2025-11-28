# -*- coding: utf-8 -*-
import keyboard
import time
import os
from inventory_detector import InventoryScanner, ScanAbortedException
import config
import pyautogui
import win32gui
import win32con
import win32process
import psutil

# Reset log file
if os.path.exists(config.LOG_FILE):
    try:
        os.remove(config.LOG_FILE)
    except:
        pass
if os.path.exists(config.OUTPUT_FILE):
    try:
        os.remove(config.OUTPUT_FILE)
    except:
        pass

def log_print(*args, **kwargs):
    msg = " ".join(map(str, args))
    print(msg, **kwargs)
    try:
        with open(config.LOG_FILE, "a", encoding="utf-8", buffering=1) as f:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass

def switch_to_star_citizen():
    """
    Switches to the Star Citizen window by finding StarCitizen.exe process.
    Returns True if successful, False if process/window not found.
    """
    log_print("\n[WINDOW] Searching for StarCitizen.exe process...")

    # First, check if StarCitizen.exe process is running
    sc_process = None
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == 'starcitizen.exe':
                sc_process = proc
                log_print(f"[WINDOW] Found StarCitizen.exe (PID: {proc.info['pid']})")
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if not sc_process:
        log_print("[WINDOW] StarCitizen.exe is not running!")
        log_print("[WINDOW] Please start Star Citizen first.")
        return False

    # Now find the window belonging to StarCitizen.exe
    hwnd = None
    found_title = None

    def enum_windows_callback(window_hwnd, _):
        nonlocal hwnd, found_title
        try:
            if win32gui.IsWindowVisible(window_hwnd):
                # Get the process ID of this window
                _, window_pid = win32process.GetWindowThreadProcessId(window_hwnd)

                # Check if this window belongs to StarCitizen.exe
                if window_pid == sc_process.pid:
                    window_title = win32gui.GetWindowText(window_hwnd)
                    # Only main windows have titles
                    if window_title:
                        hwnd = window_hwnd
                        found_title = window_title
        except:
            pass
        return True  # Always continue enumeration (returning False causes error)

    try:
        win32gui.EnumWindows(enum_windows_callback, None)
    except:
        pass  # Ignore EnumWindows errors

    if hwnd:
        try:
            # Bring window to foreground
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # Restore if minimized
            win32gui.SetForegroundWindow(hwnd)
            log_print(f"[WINDOW] Switched to: {found_title}")
            time.sleep(0.5)  # Wait for window to be in focus
            return True
        except Exception as e:
            log_print(f"[WINDOW] Error switching to window: {e}")
            return False
    else:
        log_print("[WINDOW] Star Citizen window not found (process is running but no window)!")
        return False

def main():
    log_print("\n=== InvDetect - Star Citizen Universal Inventory Scanner ===")
    log_print("INSERT → Start Scan | DELETE → Stop\n")

    first_run = True
    scan_mode = 1

    while True:
        if first_run:
            log_print("\n" + "="*80)
            log_print("SELECT SCAN MODE")
            log_print("="*80)
            log_print("[1] 1x1 Items (Normal) - 8 rows/block, 97px spacing")
            log_print("[2] 1x2 Items (Undersuits) - 4 rows/block, 180px spacing")
            log_print("="*80 + "\n")

            scan_mode_input = input("Choose mode [1/2] (Enter for default 1x1): ").strip()

            if scan_mode_input == "2":
                scan_mode = 2
                mode_name = "1x2 (Undersuits)"
            else:
                scan_mode = 1
                mode_name = "1x1 (Normal)"

            log_print(f"\n[INFO] Selected mode: {mode_name}")

            log_print("\nWaiting for INSERT to start scan...")
            while True:
                if keyboard.is_pressed('insert'):
                    break
                time.sleep(0.05)

            first_run = False
            time.sleep(0.3)
        else:
            log_print("\nPress INSERT to start another scan...")
            while True:
                if keyboard.is_pressed('insert'):
                    break
                time.sleep(0.05)
            time.sleep(0.3)

        # Switch to Star Citizen window before starting scan
        if not switch_to_star_citizen():
            log_print("\n[ERROR] Cannot start scan without Star Citizen window.")
            log_print("Press ENTER to try again...")
            input()
            continue

        import importlib
        importlib.reload(config)
        log_print("[INFO] Config reloaded")

        scanner = InventoryScanner()

        try:
            scanner.scan_all_tiles(scan_mode)
            log_print("\nSCAN COMPLETE! See detected_items.txt")

            log_print("\nPress ENTER for another scan or close the window to exit.")
            input()

        except (KeyboardInterrupt, ScanAbortedException):
            log_print("\n>>> Scan aborted (DELETE pressed). <<<")

        except pyautogui.FailSafeException:
            log_print("\n>>> PyAutoGUI Fail-Safe triggered (mouse moved to screen corner) <<<")
            log_print("This happens when the mouse is moved to a corner.")

        except Exception as e:
            log_print(f"\nUNEXPECTED ERROR: {e}")
            import traceback
            log_print(traceback.format_exc())
            break

if __name__ == "__main__":
    main()