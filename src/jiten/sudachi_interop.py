import ctypes
import os
import platform
import re
import threading
from typing import Optional, Callable

try:
    import wanakana
except ImportError:
    raise RuntimeError("'wanakana-python' not found. Install it with 'pip install wanakana-python'.")

from .string_helpers import to_full_width_digits

_lib_handle: Optional[ctypes.CDLL] = None
_free_string: Optional[Callable] = None
_process_text_ffi: Optional[Callable] = None
_run_cli_ffi: Optional[Callable] = None

_PROCESS_TEXT_LOCK = threading.Lock()

def _get_sudachi_lib_path() -> str:
    """Determines the path to the native Sudachi library based on the OS."""
    base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
    
    system = platform.system()
    if system == "Windows":
        return os.path.join(base_path, "sudachi_lib.dll")
    elif system == "Linux":
        return os.path.join(base_path, "libsudachi_lib.so")
    elif system == "Darwin":  # macOS
        return os.path.join(base_path, "libsudachi_lib.dylib")
    else:
        raise OSError(f"Unsupported platform: {system}")

def _initialize_library():
    """Loads the native library and sets up function signatures."""
    global _lib_handle, _free_string, _process_text_ffi, _run_cli_ffi
    if _lib_handle:
        return

    # Load the appropriate native library for the current platform
    lib_path = _get_sudachi_lib_path()
    if not os.path.exists(lib_path):
        raise FileNotFoundError(f"Sudachi native library not found at {lib_path}")

    _lib_handle = ctypes.CDLL(lib_path)

    # Define function signatures (argtypes and restype)
    _run_cli_ffi = _lib_handle.run_cli_ffi
    _run_cli_ffi.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
    _run_cli_ffi.restype = ctypes.c_void_p

    _process_text_ffi = _lib_handle.process_text_ffi
    _process_text_ffi.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char, ctypes.c_bool, ctypes.c_bool]
    _process_text_ffi.restype = ctypes.c_void_p

    _free_string = _lib_handle.free_string
    _free_string.argtypes = [ctypes.c_void_p]
    _free_string.restype = None

# Initialize the library when the module is imported.
_initialize_library()

def run_cli(config_path: str, file_path: str, dictionary_path: str, output_path: str) -> str:
    """Wraps the native `run_cli_ffi` function."""
    # Call the FFI function
    result_ptr = _run_cli_ffi(
        config_path.encode('utf-8'),
        file_path.encode('utf-8'),
        dictionary_path.encode('utf-8'),
        output_path.encode('utf-8')
    )

    # Convert the result to a Python string
    result_bytes = ctypes.cast(result_ptr, ctypes.c_char_p).value
    result = result_bytes.decode('utf-8') if result_bytes else ""

    # Free the string allocated in Rust
    _free_string(result_ptr)

    return result

def process_text(config_path: str, input_text: str, dictionary_path: str, mode: str = 'C', print_all: bool = True, wakati: bool = False) -> str:
    """
    Processes a string of text using the Sudachi native library.
    """
    with _PROCESS_TEXT_LOCK:
        # Clean up text
        cleaned_text = to_full_width_digits(input_text)
        valid_chars_pattern = re.compile(
            r"[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\uFF21-\uFF3A\uFF41-\uFF5A"
            r"\uFF10-\uFF19\u3005\u3001-\u3003\u3008-\u3011\u3014-\u301F\uFF01-\uFF0F"
            r"\uFF1A-\uFF1F\uFF3B-\uFF3F\uFF5B-\uFF60\uFF62-\uFF65．\n…\u3000―\u2500() 」]"
        )
        cleaned_text = re.sub(valid_chars_pattern, "", cleaned_text)

        # if there's no kanas or kanjis, abort
        if not cleaned_text or wanakana.is_romaji(cleaned_text):
            return ""

        result_ptr = _process_text_ffi(
            config_path.encode('utf-8'),
            cleaned_text.encode('utf-8'),
            dictionary_path.encode('utf-8'),
            mode.encode('ascii'),
            print_all,
            wakati
        )

        result_bytes = ctypes.cast(result_ptr, ctypes.c_char_p).value
        result = result_bytes.decode('utf-8') if result_bytes else ""
        _free_string(result_ptr)
        return result