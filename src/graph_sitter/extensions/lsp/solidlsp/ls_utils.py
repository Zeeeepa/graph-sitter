"""
This file contains various utility functions like I/O operations, handling paths, etc.
"""

import gzip
import logging
import os
import platform
import shutil
import subprocess
import uuid
import zipfile
from enum import Enum
from pathlib import Path, PurePath

import requests

from solidlsp.ls_exceptions import SolidLSPException
from solidlsp.ls_logger import LanguageServerLogger
from solidlsp.ls_types import UnifiedSymbolInformation


class InvalidTextLocationError(Exception):
    pass


class MatchedConsecutiveLines:
    """
    A simple container for consecutive lines from a file with context.
    Replacement for serena.text_utils.MatchedConsecutiveLines
    """

    def __init__(self, lines: list[str], start_line: int, source_file_path: str = ""):
        self.lines = lines
        self.start_line = start_line
        self.source_file_path = source_file_path

    @classmethod
    def from_file_contents(
        cls,
        file_contents: str,
        line: int,
        context_lines_before: int = 0,
        context_lines_after: int = 0,
        source_file_path: str = "",
    ) -> "MatchedConsecutiveLines":
        """
        Create MatchedConsecutiveLines from file contents around a specific line.

        :param file_contents: The full file contents
        :param line: The target line (0-indexed)
        :param context_lines_before: Number of lines before to include
        :param context_lines_after: Number of lines after to include
        :param source_file_path: Path to the source file
        :return: MatchedConsecutiveLines instance
        """
        all_lines = file_contents.splitlines()
        start_line = max(0, line - context_lines_before)
        end_line = min(len(all_lines), line + context_lines_after + 1)
        selected_lines = all_lines[start_line:end_line]

        return cls(lines=selected_lines, start_line=start_line, source_file_path=source_file_path)

    def __str__(self) -> str:
        return "\n".join(self.lines)

    def __repr__(self) -> str:
        return f"MatchedConsecutiveLines(start_line={self.start_line}, lines={len(self.lines)})"


class TextUtils:
    """
    Utilities for text operations.
    """

    @staticmethod
    def get_line_col_from_index(text: str, index: int) -> tuple[int, int]:
        """
        Returns the zero-indexed line and column number of the given index in the given text
        """
        l = 0
        c = 0
        idx = 0
        while idx < index:
            if text[idx] == "\n":
                l += 1
                c = 0
            else:
                c += 1
            idx += 1

        return l, c

    @staticmethod
    def get_index_from_line_col(text: str, line: int, col: int) -> int:
        """
        Returns the index of the given zero-indexed line and column number in the given text
        """
        idx = 0
        while line > 0:
            if idx >= len(text):
                raise InvalidTextLocationError
            if text[idx] == "\n":
                line -= 1
            idx += 1
        idx += col
        return idx

    @staticmethod
    def _get_updated_position_from_line_and_column_and_edit(l: int, c: int, text_to_be_inserted: str) -> tuple[int, int]:
        """
        Utility function to get the position of the cursor after inserting text at a given line and column.
        """
        num_newlines_in_gen_text = text_to_be_inserted.count("\n")
        if num_newlines_in_gen_text > 0:
            l += num_newlines_in_gen_text
            c = len(text_to_be_inserted.split("\n")[-1])
        else:
            c += len(text_to_be_inserted)
        return (l, c)

    @staticmethod
    def delete_text_between_positions(text: str, start_line: int, start_col: int, end_line: int, end_col: int) -> tuple[str, str]:
        """
        Deletes the text between the given start and end positions.
        Returns the modified text and the deleted text.
        """
        del_start_idx = TextUtils.get_index_from_line_col(text, start_line, start_col)
        del_end_idx = TextUtils.get_index_from_line_col(text, end_line, end_col)

        deleted_text = text[del_start_idx:del_end_idx]
        new_text = text[:del_start_idx] + text[del_end_idx:]
        return new_text, deleted_text

    @staticmethod
    def insert_text_at_position(text: str, line: int, col: int, text_to_be_inserted: str) -> tuple[str, int, int]:
        """
        Inserts the given text at the given line and column.
        Returns the modified text and the new line and column.
        """
        try:
            change_index = TextUtils.get_index_from_line_col(text, line, col)
        except InvalidTextLocationError:
            num_lines_in_text = text.count("\n") + 1
            max_line = num_lines_in_text - 1
            if line == max_line + 1 and col == 0:  # trying to insert at new line after full text
                # insert at end, adding missing newline
                change_index = len(text)
                text_to_be_inserted = "\n" + text_to_be_inserted
            else:
                raise
        new_text = text[:change_index] + text_to_be_inserted + text[change_index:]
        new_l, new_c = TextUtils._get_updated_position_from_line_and_column_and_edit(line, col, text_to_be_inserted)
        return new_text, new_l, new_c


class PathUtils:
    """
    Utilities for platform-agnostic path operations.
    """

    @staticmethod
    def uri_to_path(uri: str) -> str:
        """
        Converts a URI to a file path. Works on both Linux and Windows.

        This method was obtained from https://stackoverflow.com/a/61922504
        """
        try:
            from urllib.parse import unquote, urlparse
            from urllib.request import url2pathname
        except ImportError:
            # backwards compatibility
            from urllib import unquote, url2pathname

            from urlparse import urlparse
        parsed = urlparse(uri)
        host = f"{os.path.sep}{os.path.sep}{parsed.netloc}{os.path.sep}"
        path = os.path.normpath(os.path.join(host, url2pathname(unquote(parsed.path))))
        return path

    @staticmethod
    def path_to_uri(path: str) -> str:
        """
        Converts a file path to a file URI (file:///...).
        """
        return str(Path(path).absolute().as_uri())

    @staticmethod
    def is_glob_pattern(pattern: str) -> bool:
        """Check if a pattern contains glob-specific characters."""
        return any(c in pattern for c in "*?[]!")

    @staticmethod
    def get_relative_path(path: str, base_path: str) -> str | None:
        """
        Gets relative path if it's possible (paths should be on the same drive),
        returns `None` otherwise.
        """
        if PurePath(path).drive == PurePath(base_path).drive:
            rel_path = str(PurePath(os.path.relpath(path, base_path)))
            return rel_path
        return None


class FileUtils:
    """
    Utility functions for file operations.
    """

    @staticmethod
    def match_path(path: str, spec: "pathspec.PathSpec", root_path: str = "") -> bool:
        """
        Check if a path matches a pathspec pattern.
        Replacement for serena.util.file_system.match_path

        :param path: The path to check
        :param spec: The pathspec to match against
        :param root_path: Optional root path for relative matching
        :return: True if path matches the spec, False otherwise
        """
        import pathspec as ps

        if not isinstance(spec, ps.PathSpec):
            return False

        # Normalize path for matching
        if root_path and os.path.isabs(path):
            path = os.path.relpath(path, root_path)

        return spec.match_file(path)

    @staticmethod
    def read_file(logger: LanguageServerLogger, file_path: str) -> str:
        """
        Reads the file at the given path and returns the contents as a string.
        """
        if not os.path.exists(file_path):
            logger.log(f"File read '{file_path}' failed: File does not exist.", logging.ERROR)
            raise SolidLSPException(f"File read '{file_path}' failed: File does not exist.")
        try:
            with open(file_path, encoding="utf-8") as inp_file:
                return inp_file.read()
        except Exception as exc:
            logger.log(f"File read '{file_path}' failed to read with encoding 'utf-8': {exc}", logging.ERROR)
            raise SolidLSPException("File read failed.") from None

    @staticmethod
    def download_file(logger: LanguageServerLogger, url: str, target_path: str) -> None:
        """
        Downloads the file from the given URL to the given {target_path}
        """
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        try:
            response = requests.get(url, stream=True, timeout=60)
            if response.status_code != 200:
                logger.log(f"Error downloading file '{url}': {response.status_code} {response.text}", logging.ERROR)
                raise SolidLSPException("Error downloading file.")
            with open(target_path, "wb") as f:
                shutil.copyfileobj(response.raw, f)
        except Exception as exc:
            logger.log(f"Error downloading file '{url}': {exc}", logging.ERROR)
            raise SolidLSPException("Error downloading file.") from None

    @staticmethod
    def download_and_extract_archive(logger: LanguageServerLogger, url: str, target_path: str, archive_type: str) -> None:
        """
        Downloads the archive from the given URL having format {archive_type} and extracts it to the given {target_path}
        """
        try:
            tmp_files = []
            tmp_file_name = str(PurePath(os.path.expanduser("~"), "multilspy_tmp", uuid.uuid4().hex))
            tmp_files.append(tmp_file_name)
            os.makedirs(os.path.dirname(tmp_file_name), exist_ok=True)
            FileUtils.download_file(logger, url, tmp_file_name)
            if archive_type in ["tar", "gztar", "bztar", "xztar"]:
                os.makedirs(target_path, exist_ok=True)
                shutil.unpack_archive(tmp_file_name, target_path, archive_type)
            elif archive_type == "zip":
                os.makedirs(target_path, exist_ok=True)
                with zipfile.ZipFile(tmp_file_name, "r") as zip_ref:
                    for zip_info in zip_ref.infolist():
                        extracted_path = zip_ref.extract(zip_info, target_path)
                        ZIP_SYSTEM_UNIX = 3  # zip file created on Unix system
                        if zip_info.create_system != ZIP_SYSTEM_UNIX:
                            continue
                        # extractall() does not preserve permissions
                        # see. https://github.com/python/cpython/issues/59999
                        attrs = (zip_info.external_attr >> 16) & 0o777
                        if attrs:
                            os.chmod(extracted_path, attrs)
            elif archive_type == "zip.gz":
                os.makedirs(target_path, exist_ok=True)
                tmp_file_name_ungzipped = tmp_file_name + ".zip"
                tmp_files.append(tmp_file_name_ungzipped)
                with gzip.open(tmp_file_name, "rb") as f_in, open(tmp_file_name_ungzipped, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                shutil.unpack_archive(tmp_file_name_ungzipped, target_path, "zip")
            elif archive_type == "gz":
                with gzip.open(tmp_file_name, "rb") as f_in, open(target_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            else:
                logger.log(f"Unknown archive type '{archive_type}' for extraction", logging.ERROR)
                raise SolidLSPException(f"Unknown archive type '{archive_type}'")
        except Exception as exc:
            logger.log(f"Error extracting archive '{tmp_file_name}' obtained from '{url}': {exc}", logging.ERROR)
            raise SolidLSPException("Error extracting archive.") from exc
        finally:
            for tmp_file_name in tmp_files:
                if os.path.exists(tmp_file_name):
                    Path.unlink(Path(tmp_file_name))


class PlatformId(str, Enum):
    """
    multilspy supported platforms
    """

    WIN_x86 = "win-x86"
    WIN_x64 = "win-x64"
    WIN_arm64 = "win-arm64"
    OSX = "osx"
    OSX_x64 = "osx-x64"
    OSX_arm64 = "osx-arm64"
    LINUX_x86 = "linux-x86"
    LINUX_x64 = "linux-x64"
    LINUX_arm64 = "linux-arm64"
    LINUX_MUSL_x64 = "linux-musl-x64"
    LINUX_MUSL_arm64 = "linux-musl-arm64"

    def is_windows(self):
        return self.value.startswith("win")


class DotnetVersion(str, Enum):
    """
    multilspy supported dotnet versions
    """

    V4 = "4"
    V6 = "6"
    V7 = "7"
    V8 = "8"
    V9 = "9"
    VMONO = "mono"


class PlatformUtils:
    """
    This class provides utilities for platform detection and identification.
    """

    @classmethod
    def get_platform_id(cls) -> PlatformId:
        """
        Returns the platform id for the current system
        """
        system = platform.system()
        machine = platform.machine()
        bitness = platform.architecture()[0]
        if system == "Windows" and machine == "":
            machine = cls._determine_windows_machine_type()
        system_map = {"Windows": "win", "Darwin": "osx", "Linux": "linux"}
        machine_map = {
            "AMD64": "x64",
            "x86_64": "x64",
            "i386": "x86",
            "i686": "x86",
            "aarch64": "arm64",
            "arm64": "arm64",
            "ARM64": "arm64",
        }
        if system in system_map and machine in machine_map:
            platform_id = system_map[system] + "-" + machine_map[machine]
            if system == "Linux" and bitness == "64bit":
                libc = platform.libc_ver()[0]
                if libc != "glibc":
                    platform_id += "-" + libc
            return PlatformId(platform_id)
        else:
            raise SolidLSPException(f"Unknown platform: {system=}, {machine=}, {bitness=}")

    @staticmethod
    def _determine_windows_machine_type():
        import ctypes
        from ctypes import wintypes

        class SYSTEM_INFO(ctypes.Structure):
            class _U(ctypes.Union):
                class _S(ctypes.Structure):
                    _fields_ = [("wProcessorArchitecture", wintypes.WORD), ("wReserved", wintypes.WORD)]

                _fields_ = [("dwOemId", wintypes.DWORD), ("s", _S)]
                _anonymous_ = ("s",)

            _fields_ = [
                ("u", _U),
                ("dwPageSize", wintypes.DWORD),
                ("lpMinimumApplicationAddress", wintypes.LPVOID),
                ("lpMaximumApplicationAddress", wintypes.LPVOID),
                ("dwActiveProcessorMask", wintypes.LPVOID),
                ("dwNumberOfProcessors", wintypes.DWORD),
                ("dwProcessorType", wintypes.DWORD),
                ("dwAllocationGranularity", wintypes.DWORD),
                ("wProcessorLevel", wintypes.WORD),
                ("wProcessorRevision", wintypes.WORD),
            ]
            _anonymous_ = ("u",)

        sys_info = SYSTEM_INFO()
        ctypes.windll.kernel32.GetNativeSystemInfo(ctypes.byref(sys_info))

        arch_map = {
            9: "AMD64",
            5: "ARM",
            12: "arm64",
            6: "Intel Itanium-based",
            0: "i386",
        }

        return arch_map.get(sys_info.wProcessorArchitecture, f"Unknown ({sys_info.wProcessorArchitecture})")

    @staticmethod
    def get_dotnet_version() -> DotnetVersion:
        """
        Returns the dotnet version for the current system
        """
        try:
            result = subprocess.run(["dotnet", "--list-runtimes"], capture_output=True, check=True)
            available_version_cmd_output = []
            for line in result.stdout.decode("utf-8").split("\n"):
                if line.startswith("Microsoft.NETCore.App"):
                    version_cmd_output = line.split(" ")[1]
                    available_version_cmd_output.append(version_cmd_output)

            if not available_version_cmd_output:
                raise SolidLSPException("dotnet not found on the system")

            # Check for supported versions in order of preference (latest first)
            for version_cmd_output in available_version_cmd_output:
                if version_cmd_output.startswith("9"):
                    return DotnetVersion.V9
                if version_cmd_output.startswith("8"):
                    return DotnetVersion.V8
                if version_cmd_output.startswith("7"):
                    return DotnetVersion.V7
                if version_cmd_output.startswith("6"):
                    return DotnetVersion.V6
                if version_cmd_output.startswith("4"):
                    return DotnetVersion.V4

            # If no supported version found, raise exception with all available versions
            raise SolidLSPException(
                f"No supported dotnet version found. Available versions: {', '.join(available_version_cmd_output)}. Supported versions: 4, 6, 7, 8"
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            try:
                result = subprocess.run(["mono", "--version"], capture_output=True, check=True)
                return DotnetVersion.VMONO
            except (FileNotFoundError, subprocess.CalledProcessError):
                raise SolidLSPException("dotnet or mono not found on the system")


class SymbolUtils:
    @staticmethod
    def symbol_tree_contains_name(roots: list[UnifiedSymbolInformation], name: str) -> bool:
        for symbol in roots:
            if symbol["name"] == name:
                return True
            if SymbolUtils.symbol_tree_contains_name(symbol["children"], name):
                return True
        return False
