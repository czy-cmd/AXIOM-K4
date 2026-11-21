# -*- coding: utf-8 -*-
"""
零依赖创建 Windows 快捷方式 (.lnk)
直接 ctypes 调 IShellLinkW / IPersistFile COM，不依赖 pywin32 / PowerShell。
"""
import ctypes
import os
from ctypes import wintypes, byref, POINTER

CLSCTX_INPROC_SERVER = 1
CLSID_SHELL_LINK = "{00021401-0000-0000-C000-000000000046}"
IID_ISHELLLINKW = "{000214F9-0000-0000-C000-000000000046}"
IID_IPERSISTFILE = "{0000010B-0000-0000-C000-000000000046}"

_ole32 = ctypes.windll.ole32
_HRESULT = ctypes.HRESULT
_ULONG = ctypes.c_ulong


class GUID(ctypes.Structure):
    _fields_ = [("Data1", ctypes.c_ulong),
                ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort),
                ("Data4", ctypes.c_ubyte * 8)]


def _guid(s):
    g = GUID()
    s = s.strip().strip("{}")
    a, b, c, d, e = s.split("-")
    g.Data1 = int(a, 16)
    g.Data2 = int(b, 16)
    g.Data3 = int(c, 16)
    raw = bytes.fromhex(d) + bytes.fromhex(e)
    for i in range(8):
        g.Data4[i] = raw[i]
    return g


def _vtable(ptr):
    """取 COM 对象的虚函数表"""
    return ctypes.cast(ptr, POINTER(POINTER(ctypes.c_void_p))).contents


def _addr(x):
    """ctypes 里 vtable[i] 可能返回 int 也可能返回 c_void_p，统一成 int 地址"""
    return getattr(x, "value", x)


def _fn(vt, idx, proto):
    addr = _addr(vt[idx])
    if not addr:
        raise OSError("vtable entry %d is null" % idx)
    return proto(addr)


# IShellLinkW 虚表下标（IUnknown 占 0/1/2）
_SET_PATH = 20
_SET_WORKDIR = 9
_SET_ICON = 17
_SET_DESC = 7
_SET_ARGS = 11
# IPersistFile
_PF_SAVE = 6


def create_shortcut(target, lnk_path, workdir="", icon="", desc="", args=""):
    """创建 .lnk。成功返回 True。target/lnk_path 均用绝对路径。"""
    try:
        _ole32.CoInitialize(None)
    except Exception:
        pass

    sl = ctypes.c_void_p()
    clsid = _guid(CLSID_SHELL_LINK)
    iid = _guid(IID_ISHELLLINKW)
    hr = _ole32.CoCreateInstance(byref(clsid), None, CLSCTX_INPROC_SERVER,
                                 byref(iid), byref(sl))
    if hr != 0 or not sl.value:
        return False

    vt = _vtable(sl)
    release = ctypes.WINFUNCTYPE(_ULONG, ctypes.c_void_p)

    try:
        # IShellLinkW::SetPath(LPCWSTR)
        P = ctypes.WINFUNCTYPE(_HRESULT, ctypes.c_void_p, ctypes.c_wchar_p)
        _fn(vt, _SET_PATH, P)(sl, os.path.abspath(target))

        if workdir:
            _fn(vt, _SET_WORKDIR, P)(sl, os.path.abspath(workdir))
        if desc:
            _fn(vt, _SET_DESC, P)(sl, desc)
        if args:
            _fn(vt, _SET_ARGS, P)(sl, args)
        if icon:
            PI = ctypes.WINFUNCTYPE(_HRESULT, ctypes.c_void_p,
                                    ctypes.c_wchar_p, ctypes.c_int)
            _fn(vt, _SET_ICON, PI)(sl, os.path.abspath(icon), 0)

        # QueryInterface(IID_IPersistFile)
        pf = ctypes.c_void_p()
        QI = ctypes.WINFUNCTYPE(_HRESULT, ctypes.c_void_p,
                                POINTER(GUID), POINTER(ctypes.c_void_p))
        iid_pf = _guid(IID_IPERSISTFILE)
        hr = _fn(vt, 0, QI)(sl, byref(iid_pf), byref(pf))
        if hr != 0 or not pf.value:
            return False

        pvt = _vtable(pf)
        SAVE = ctypes.WINFUNCTYPE(_HRESULT, ctypes.c_void_p,
                                  ctypes.c_wchar_p, ctypes.c_bool)
        hr = _fn(pvt, _PF_SAVE, SAVE)(pf, os.path.abspath(lnk_path), True)
        release(_addr(pvt[2]))(pf)
        return hr == 0
    except Exception:
        return False
    finally:
        try:
            release(_addr(vt[2]))(sl)
        except Exception:
            pass


def remove_shortcut(lnk_path):
    try:
        if os.path.exists(lnk_path):
            os.remove(lnk_path)
            return True
    except Exception:
        pass
    return False
