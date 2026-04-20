import sys
import os
if sys.platform == "win32":
    import win32com.client as win32c
    import win32job
    import win32process
    import win32api
    import win32con
from visioplot.debug_utils import error_print


class VisioApp:
    _instance = None
    _job = None

    @classmethod
    def _bind_lifecycle(cls, visio):
        if cls._job is None:
            cls._job = win32job.CreateJobObject(None, f"VisioJob_{os.getpid()}")
            if cls._job is None:
                error_print("Failed to create Job object.")
                return

            info = win32job.QueryInformationJobObject(
                cls._job, win32job.JobObjectExtendedLimitInformation
            )
            info["BasicLimitInformation"]["LimitFlags"] |= (
                win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            )
            win32job.SetInformationJobObject(
                cls._job, win32job.JobObjectExtendedLimitInformation, info
            )

        hwnd = visio.Application.WindowHandle32
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        handle = win32api.OpenProcess(
            win32con.PROCESS_TERMINATE | win32con.PROCESS_SET_QUOTA,
            False,
            pid,
        )
        try:
            win32job.AssignProcessToJobObject(cls._job, handle)
        finally:
            win32api.CloseHandle(handle)

    @classmethod
    def get(cls):
        if cls._instance is not None:
            try:
                _ = cls._instance.Version
                return cls._instance
            except Exception:
                cls._instance = None
        visio = win32c.DispatchEx("Visio.Application")
        visio.Visible = False
        cls._bind_lifecycle(visio)
        cls._instance = visio
        return visio

    @classmethod
    def quit(cls):
        if cls._instance:
            try:
                cls._instance.AlertResponse = 6  # IDYES 保存剪切板数据
                cls._instance.Quit()
            except Exception:
                pass
            finally:
                cls._instance = None
        if cls._job:
            win32api.CloseHandle(cls._job)
            cls._job = None
