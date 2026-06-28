# -*- coding: utf-8 -*-
"""
Tally Sync Agent - Registration Wizard

Shown during first install (by the Inno Setup installer via /wizard flag)
and can also be re-run standalone to re-register.

Flow:
  1. Check if already registered → show "Already Registered" page
  2. Welcome screen (first install only)
  3. Installation key entry
  4. Validates key with platform
  5. Stores credentials in Windows Credential Manager
  6. Done screen
"""

from __future__ import annotations

import os
import sys
import json
import socket
import platform
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
from tkinter import messagebox
from pathlib import Path
from typing import Dict, Optional

import requests
import keyring

# ---------------------------------------------------------------------------
# Sentry telemetry (optional — disabled if SENTRY_DSN not set)
# ---------------------------------------------------------------------------
def _init_sentry():
    dsn = os.getenv("SENTRY_DSN", "")
    if not dsn:
        return
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
            release=f"tally-sync-agent@{AGENT_VERSION}",
            send_default_pii=False,
            attach_stacktrace=True,
        )
        sentry_sdk.set_tag("component", "wizard")
        sentry_sdk.set_tag("hostname", socket.gethostname())
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Config  (overridable via environment)
# ---------------------------------------------------------------------------
API_BASE_URL = os.getenv("CLOUD_API_URL", "http://localhost:8000")
AGENT_VERSION = "0.5.0"
KEYRING_SERVICE = "TallySyncAgent"
KEYRING_USERNAME = "registration"  # must match agent/registration.py CRED_USERNAME

# Colour palette
BG = "#F8FAFC"
PRIMARY = "#1A56DB"
PRIMARY_DARK = "#1A3DBF"
TEXT = "#111928"
MUTED = "#6B7280"
BORDER = "#D1D5DB"
SUCCESS_BG = "#ECFDF5"
SUCCESS_FG = "#065F46"
ERROR_BG = "#FEF2F2"
ERROR_FG = "#991B1B"
WARNING_BG = "#FFFBEB"
WARNING_FG = "#92400E"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _device_name() -> str:
    return socket.gethostname()


def _os_version() -> str:
    return f"Windows {platform.version()}"


def _get_existing_credentials() -> Optional[dict]:
    """Check if credentials already exist in Windows Credential Manager."""
    try:
        stored = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        if stored:
            return json.loads(stored)
    except Exception:
        pass
    return None


def _register_device(key: str) -> dict:
    """POST to /v1/register-device and return credentials."""
    resp = requests.post(
        f"{API_BASE_URL}/v1/register-device",
        params={
            "installation_key": key,
            "device_name": _device_name(),
            "os_version": _os_version(),
            "agent_version": AGENT_VERSION,
        },
        timeout=15,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail") or resp.text
        except Exception:
            detail = resp.text
        raise ValueError(f"Registration failed ({resp.status_code}): {detail}")
    return resp.json()


def _store_credentials(creds: dict):
    """Persist credentials in Windows Credential Manager."""
    payload = json.dumps({
        "client_id": creds["client_id"],
        "device_id": creds["device_id"],
        "api_key": creds["api_key"],
        "registration_token": creds["registration_token"],
        "api_base_url": API_BASE_URL,
    })
    keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, payload)


def _delete_credentials():
    """Remove credentials from Windows Credential Manager."""
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except keyring.errors.PasswordDeleteError:
        pass


def _sentry_capture(exc: BaseException, **extra):
    """Capture exception to Sentry if initialised."""
    try:
        import sentry_sdk
        with sentry_sdk.new_scope() as scope:
            for k, v in extra.items():
                scope.set_extra(k, v)
            sentry_sdk.capture_exception(exc)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Wizard frames
# ---------------------------------------------------------------------------

class BasePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG)
        self.controller = controller

    def _label(self, text, size=12, bold=False, color=TEXT, **kw):
        weight = "bold" if bold else "normal"
        return tk.Label(
            self, text=text, bg=BG, fg=color,
            font=("Segoe UI", size, weight), **kw
        )

    def _button(self, text, command, primary=True, **kw):
        bg = PRIMARY if primary else "#FFFFFF"
        fg = "#FFFFFF" if primary else TEXT
        btn = tk.Button(
            self, text=text, command=command,
            bg=bg, fg=fg, activebackground=PRIMARY_DARK, activeforeground="#FFFFFF",
            relief="flat", padx=20, pady=8,
            font=("Segoe UI", 11, "bold"), cursor="hand2",
            **kw
        )
        return btn


class AlreadyRegisteredPage(BasePage):
    """Shown when device already has credentials in Credential Manager."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.columnconfigure(0, weight=1)
        self._creds: Optional[dict] = None

    def refresh(self, creds: dict):
        self._creds = creds
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        tk.Label(self, text="ℹ️", bg=BG, font=("Segoe UI", 48)).grid(
            row=0, column=0, pady=(30, 0)
        )
        self._label("Device Already Registered", size=20, bold=True).grid(
            row=1, column=0, pady=(8, 4)
        )
        self._label(
            "This device is already registered with the\n"
            "Tally Sync platform. You can continue using\n"
            "the existing registration or re-register.",
            size=11, color=MUTED, justify="center",
        ).grid(row=2, column=0)

        tk.Frame(self, bg=BORDER, height=1).grid(
            row=3, column=0, sticky="ew", padx=40, pady=16
        )

        # Show existing credentials
        info_frame = tk.Frame(self, bg="#EFF6FF", bd=0)
        info_frame.grid(row=4, column=0, sticky="ew", padx=40)
        info_frame.columnconfigure(1, weight=1)

        rows = [
            ("Client ID", self._creds.get("client_id", "—")),
            ("Device ID", self._creds.get("device_id", "—")),
            ("Server", self._creds.get("api_base_url", "—")),
            ("Device", _device_name()),
        ]
        for i, (k, v) in enumerate(rows):
            tk.Label(
                info_frame, text=k + ":", bg="#EFF6FF", fg=MUTED,
                font=("Segoe UI", 10), anchor="w"
            ).grid(row=i, column=0, sticky="w", padx=12, pady=3)
            tk.Label(
                info_frame, text=str(v), bg="#EFF6FF", fg=TEXT,
                font=("Consolas", 10), anchor="w"
            ).grid(row=i, column=1, sticky="w", padx=4, pady=3)

        # Warning about re-registration
        warn_frame = tk.Frame(self, bg=WARNING_BG, bd=0)
        warn_frame.grid(row=5, column=0, sticky="ew", padx=40, pady=(16, 0))
        tk.Label(
            warn_frame,
            text="Re-registering will replace the existing credentials.\n"
                 "You will need a new installation key from the portal.",
            bg=WARNING_BG, fg=WARNING_FG,
            font=("Segoe UI", 9), justify="left", wraplength=340,
        ).grid(padx=12, pady=8)

        # Buttons
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.grid(row=6, column=0, pady=20)

        tk.Button(
            btn_frame, text="Keep Existing & Close",
            command=self.controller.quit_app,
            bg=PRIMARY, fg="#FFFFFF", activebackground=PRIMARY_DARK,
            activeforeground="#FFFFFF", relief="flat", padx=20, pady=8,
            font=("Segoe UI", 11, "bold"), cursor="hand2",
        ).pack(side="left", padx=(0, 12))

        tk.Button(
            btn_frame, text="Re-register",
            command=self._re_register,
            bg="#FFFFFF", fg=TEXT, relief="flat", padx=20, pady=8,
            font=("Segoe UI", 11, "bold"), cursor="hand2",
        ).pack(side="left")

    def _re_register(self):
        if messagebox.askyesno(
            "Re-register Device",
            "Are you sure you want to re-register?\n\n"
            "This will delete the current credentials and\n"
            "you will need a new installation key.",
        ):
            _delete_credentials()
            self.controller.show("key")


class WelcomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.columnconfigure(0, weight=1)

        tk.Label(self, text="⚡", bg=BG, font=("Segoe UI", 48)).grid(
            row=0, column=0, pady=(40, 0)
        )
        self._label("Tally Sync Agent", size=22, bold=True).grid(
            row=1, column=0, pady=(8, 4)
        )
        self._label("Setup & Registration", size=13, color=MUTED).grid(
            row=2, column=0
        )

        tk.Frame(self, bg=BORDER, height=1).grid(
            row=3, column=0, sticky="ew", padx=40, pady=24
        )

        self._label(
            "This wizard will register your device with the\n"
            "Tally Sync platform so your accounting data\n"
            "is securely synced to the cloud.",
            size=11, color=MUTED, justify="center",
        ).grid(row=4, column=0)

        self._button("Get Started →", lambda: controller.show("key")).grid(
            row=5, column=0, pady=32
        )


class KeyPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.columnconfigure(0, weight=1)

        self._label("Enter Installation Key", size=18, bold=True).grid(
            row=0, column=0, pady=(40, 4), padx=40, sticky="w"
        )
        self._label(
            "You received this key by email when you registered\n"
            "on the Tally Sync portal.",
            size=11, color=MUTED,
        ).grid(row=1, column=0, padx=40, sticky="w")

        tk.Frame(self, bg=BORDER, height=1).grid(
            row=2, column=0, sticky="ew", padx=40, pady=20
        )

        self._label("Installation Key", size=11, bold=True).grid(
            row=3, column=0, padx=40, sticky="w"
        )

        self._key_var = tk.StringVar()
        key_entry = tk.Entry(
            self, textvariable=self._key_var, font=("Consolas", 14),
            relief="solid", bd=1, bg="#FFFFFF", fg=TEXT,
            width=28,
        )
        key_entry.grid(row=4, column=0, padx=40, sticky="ew", ipady=6)
        key_entry.focus_set()
        key_entry.bind("<Return>", lambda e: self._submit())

        self._label(
            "Format: TSA-2026-XXXXX", size=10, color=MUTED
        ).grid(row=5, column=0, padx=40, sticky="w", pady=(4, 0))

        # Status area
        self._status_var = tk.StringVar()
        self._status_label = tk.Label(
            self, textvariable=self._status_var,
            bg=BG, fg=ERROR_FG,
            font=("Segoe UI", 10), wraplength=340, justify="left",
        )
        self._status_label.grid(row=6, column=0, padx=40, sticky="w", pady=(12, 0))

        # Progress bar (hidden until validating)
        self._progress = ttk.Progressbar(self, mode="indeterminate", length=340)
        self._progress.grid(row=7, column=0, padx=40, pady=(8, 0))
        self._progress.grid_remove()

        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.grid(row=8, column=0, pady=24, sticky="e", padx=40)

        back_btn = tk.Button(
            btn_frame, text="<- Back", command=lambda: controller.show("welcome"),
            bg="#FFFFFF", fg=TEXT, relief="flat", padx=20, pady=8,
            font=("Segoe UI", 11, "bold"), cursor="hand2",
        )
        back_btn.pack(side="left", padx=(0, 8))

        self._submit_btn = tk.Button(
            btn_frame, text="Register Device", command=self._submit,
            bg=PRIMARY, fg="#FFFFFF", activebackground=PRIMARY_DARK,
            activeforeground="#FFFFFF", relief="flat", padx=20, pady=8,
            font=("Segoe UI", 11, "bold"), cursor="hand2",
        )
        self._submit_btn.pack(side="left")

    def _submit(self):
        key = self._key_var.get().strip().upper()
        if not key:
            self._set_error("Please enter your installation key.")
            return
        if not key.startswith("TSA-"):
            self._set_error("Key must start with TSA-  (e.g. TSA-2026-XXXXX)")
            return

        self._set_busy(True)
        import threading
        threading.Thread(target=self._do_register, args=(key,), daemon=True).start()

    def _do_register(self, key: str):
        try:
            creds = _register_device(key)
            _store_credentials(creds)
            self.after(0, lambda: self.controller.show("done", data=creds))
        except ValueError as e:
            _sentry_capture(e, stage="register_device", key_prefix=key[:8])
            self.after(0, lambda: self._set_error(str(e)))
        except requests.ConnectionError as e:
            _sentry_capture(e, stage="register_device_connection", server=API_BASE_URL)
            self.after(0, lambda: self._set_error(
                "Cannot reach the Tally Sync server.\n"
                "Check your internet connection and try again."
            ))
        except Exception as e:
            _sentry_capture(e, stage="register_device_unexpected")
            self.after(0, lambda: self._set_error(f"Unexpected error: {e}"))
        finally:
            self.after(0, lambda: self._set_busy(False))

    def _set_error(self, msg: str):
        self._status_label.configure(fg=ERROR_FG)
        self._status_var.set(msg)

    def _set_busy(self, busy: bool):
        self._submit_btn.configure(state="disabled" if busy else "normal")
        if busy:
            self._status_var.set("Validating key…")
            self._status_label.configure(fg=MUTED)
            self._progress.grid()
            self._progress.start(10)
        else:
            self._progress.stop()
            self._progress.grid_remove()


class DonePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.columnconfigure(0, weight=1)
        self._data = {}

    def refresh(self, data: dict):
        """Called by controller after successful registration."""
        self._data = data
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        tk.Label(self, text="✅", bg=BG, font=("Segoe UI", 48)).grid(
            row=0, column=0, pady=(40, 0)
        )
        self._label("Registration Complete!", size=20, bold=True).grid(
            row=1, column=0, pady=(8, 4)
        )
        self._label(
            "Your device has been registered and credentials\n"
            "are stored securely in Windows Credential Manager.",
            size=11, color=MUTED, justify="center",
        ).grid(row=2, column=0)

        tk.Frame(self, bg=BORDER, height=1).grid(
            row=3, column=0, sticky="ew", padx=40, pady=20
        )

        # Credential summary
        info_frame = tk.Frame(self, bg="#EFF6FF", bd=0)
        info_frame.grid(row=4, column=0, sticky="ew", padx=40)
        info_frame.columnconfigure(1, weight=1)

        rows = [
            ("Client ID", self._data.get("client_id", "—")),
            ("Device ID", self._data.get("device_id", "—")),
            ("Device",    _device_name()),
        ]
        for i, (k, v) in enumerate(rows):
            tk.Label(
                info_frame, text=k + ":", bg="#EFF6FF", fg=MUTED,
                font=("Segoe UI", 10), anchor="w"
            ).grid(row=i, column=0, sticky="w", padx=12, pady=3)
            tk.Label(
                info_frame, text=str(v), bg="#EFF6FF", fg=TEXT,
                font=("Consolas", 10), anchor="w"
            ).grid(row=i, column=1, sticky="w", padx=4, pady=3)

        self._label(
            "\nThe Tally Sync Agent service will start automatically\n"
            "and begin syncing your data.",
            size=11, color=MUTED, justify="center",
        ).grid(row=5, column=0, pady=(20, 0))

        self._button("Finish", self.controller.quit_app).grid(row=6, column=0, pady=28)


# ---------------------------------------------------------------------------
# Wizard controller
# ---------------------------------------------------------------------------

class RegistrationWizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tally Sync Agent — Registration")
        self.resizable(False, False)
        self.configure(bg=BG)

        w, h = 480, 560
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")

        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._pages: Dict[str, BasePage] = {}
        for name, cls in [
            ("welcome",    WelcomePage),
            ("key",        KeyPage),
            ("done",       DonePage),
            ("registered", AlreadyRegisteredPage),
        ]:
            page = cls(container, self)
            page.grid(row=0, column=0, sticky="nsew")
            self._pages[name] = page

        # Check if already registered
        existing = _get_existing_credentials()
        if existing:
            self.show("registered", data=existing)
        else:
            self.show("welcome")

    def show(self, name: str, data: Optional[dict] = None):
        page = self._pages[name]
        if name == "done" and data:
            page.refresh(data)
        elif name == "registered" and data:
            page.refresh(data)
        page.tkraise()

    def quit_app(self):
        self.destroy()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    _init_sentry()
    app = RegistrationWizard()
    app.mainloop()


if __name__ == "__main__":
    main()
