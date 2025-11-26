This is the complete and updated **SECURITY.md** file in English, incorporating the provided template, the current project structure, and the dependencies listed in your `requirements.txt`.

***

# SECURITY.md

## Supported Versions

The following table lists the project versions that are currently supported with security updates.

| Version | Supported |
| :------ | :-------- |
| 1.0.x | Yes |
| < 1.0 | No |

---

## Reporting a Vulnerability

We take the security of this project seriously. If you discover a vulnerability, please report it immediately to help us address it promptly.

### How to Report

1.  **Do not** open a public GitHub issue.
2.  Send an email to the project maintainer at: **[Insert Maintainer's Email Address or Preferred Contact Method Here]**
3.  Provide a detailed description of the vulnerability, including:
    * The specific files and lines of code affected.
    * The steps required to reproduce the vulnerability.
    * The potential impact of the flaw.

### Our Commitment

* **Response Time:** We aim to acknowledge receipt of your report within **3 business days**.
* **Update Frequency:** We will provide an initial update on the status of the reported vulnerability within **7 business days** of confirmation.
* **Resolution:** Once a vulnerability is accepted, we will work to address it as quickly as possible and will announce a fix upon release.

---

## Project Security Overview

The `InvDetect` project uses automation libraries (`pyautogui`, `keyboard`) which require specific security measures.

### A. Requirement for Administrator Privileges (Windows)

The startup script (`start_scanner.bat`) uses a check to ensure the application is run with **Administrator rights** (`RunAs`).

* **Reason:** Elevated privileges are often necessary for the `keyboard` and `pyautogui` libraries to reliably capture hotkeys and control the mouse while interacting with a full-screen or high-privilege application (like the game itself).
* **Risk Warning:** Any program run with Administrator rights has full access to your operating system. **Users must verify the integrity of the source code before running the script.**

### B. Fail-Safe Mechanism

The `pyautogui` library is configured with a built-in **Fail-Safe** mechanism (`pyautogui.FAILSAFE = True`).

* **Action:** If the mouse cursor is moved into **any of the four corners** of the screen, the script will immediately stop execution. This is the primary method for users to regain control in case of unexpected automation behavior.

### C. Data Handling

* **No External Transmission:** The script only performs local operations (screen capturing, OCR, file writing). Inventory data is stored **locally** in `detected_items.txt`. No information is sent to an external server.
* **Read-Only Database:** The `database.py` component uses a local SQLite file (`inventory.db`) solely for **read-only** operations (loading item names for OCR correction). This minimizes the risk of data corruption or injection attacks.

---

## Dependencies (from `requirements.txt`)

Maintaining the security of the project requires ensuring all dependencies are up-to-date and free of vulnerabilities. The following external libraries are critical components:

| Dependency | Version | Function |
| :--- | :--- | :--- |
| `pyautogui` | `0.9.54` | Mouse control, screen capture (Automation) |
| `Pillow` | `10.4.0` | Image processing for screen captures |
| `keyboard` | `0.13.5` | Hotkey detection and handling |
| `easyocr` | `1.7.2` | Optical Character Recognition (OCR) |
| `opencv-python` | `4.10.0.84` | Image processing for OCR pre-processing |
| `numpy` | `2.1.2` | Numerical operations (used by image libraries) |
| `rapidfuzz` | `3.10.0` | String matching for OCR correction |

**Action Item:** Developers must periodically check the security status of these specific versions against public vulnerability databases (e.g., CVEs).
