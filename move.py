#!/usr/bin/python3
"""Desktop to Drive: moves (cut, not copy) old items from the Desktop into Google Drive.

Related files share the start of their name (e.g. "Report-final.pdf" and "Report.docx",
"فاتورة.psd" and "فاتورة لوحة.pdf"). Groups of 2+ get their own folder; the rest go to a folder by type.
Works on macOS and Windows (Google Drive for desktop must be installed and signed in).

Usage: move.py                 move for real (what the hourly schedule runs)
       move.py --preview       only print the plan, move nothing
       move.py --now           move for real even if the PAUSE file exists (manual run)
       move.py --stats         print totals from log.txt
       move.py --where         print the Google Drive folder items go to
       move.py --set-age DAYS  move only items unchanged for at least DAYS (saved in settings.json)
Pause: create a file named PAUSE next to this script. Keep items on the Desktop: add their
names to keep.txt (one per line). Everything the tool does is written to log.txt.
"""
import argparse, json, os, re, shutil, subprocess, sys, time
from datetime import datetime

WINDOWS = os.name == "nt"
HOME = os.path.expanduser("~")
TOOL = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(TOOL, "log.txt")
GROUPS_FILE = os.path.join(TOOL, "groups.json")
KEEP_FILE = os.path.join(TOOL, "keep.txt")
PAUSE_FILE = os.path.join(TOOL, "PAUSE")
SETTINGS_FILE = os.path.join(TOOL, "settings.json")
PREVIEW = FORCE = False  # set from the command line


def load_settings():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


SETTINGS = load_settings()
DEST_NAME = SETTINGS.get("dest_folder") or ("Windows Desktop" if WINDOWS else "Mac Desktop")
MIN_AGE_DAYS = float(SETTINGS.get("min_age_days", 1))
MIN_AGE = int(float(os.environ.get("MIN_AGE_MIN", MIN_AGE_DAYS * 1440)) * 60)

SKIP_SUFFIXES = (".download", ".crdownload", ".part", ".partial", ".tmp", ".tmp$$", ".conf")
if WINDOWS:
    SKIP_SUFFIXES += (".lnk", ".url")  # shortcuts belong on the Desktop
SKIP_NAMES = {"desktop.ini", "thumbs.db", "icon\r"}
TYPES = [
    ("تصاميم", "psd psb ai eps af svg indd cdr xd sketch fig tif tiff"),
    ("صور", "jpg jpeg png gif heic webp bmp"),
    ("فيديو", "mp4 mov avi mkv m4v"),
    ("PDF", "pdf"),
    ("ملفات مضغوطة", "zip rar 7z"),
    ("كود", "js jsx ts tsx html css py json"),
    ("مستندات", "doc docx rtf txt xls xlsx ppt pptx"),
]
NO_GROUP = ("screen recording", "screenshot", "img", "whatsapp", "gemini", "untitled folder")
TWO_WORD = {"untitled", "شركة", "عرض", "رسم", "كتاب", "طلب", "خطاب"}
SIZE = re.compile(r"^\d+(\.\d+)?x\d+(\.\d+)?(cm)?$")
SIZE_FOLDER = "تصاميم بالمقاس"

# Cloud placeholders (file not downloaded): moving one would download it first.
MAC_DATALESS = 0x40000000  # SF_DATALESS (iCloud)
WIN_HIDDEN, WIN_SYSTEM = 0x2, 0x4
WIN_CLOUD_ONLY = 0x1000 | 0x40000 | 0x400000  # OFFLINE | RECALL_ON_OPEN | RECALL_ON_DATA_ACCESS (OneDrive)


def log(msg):
    if PREVIEW:
        return
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")


# ---------- paths ----------

def desktop_dir():
    if os.environ.get("SRC"):
        return os.environ["SRC"]
    if WINDOWS:
        try:  # follows a Desktop moved by OneDrive or by the user
            import winreg
            key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
                path = os.path.expandvars(winreg.QueryValueEx(k, "Desktop")[0])
            if os.path.isdir(path):
                return path
        except OSError:
            pass
    return os.path.join(HOME, "Desktop")


def drive_dirs():
    """Possible "My Drive" folders of Google Drive for desktop, best first."""
    if os.environ.get("DEST"):  # set by hand or for testing
        return [os.environ["DEST"]]
    if WINDOWS:
        letters = "GHIJKLMNOPQRSTUVWXYZDEF"
        found = [f"{l}:\\My Drive" for l in letters]
    else:
        cloud = os.path.join(HOME, "Library", "CloudStorage")
        names = sorted(os.listdir(cloud)) if os.path.isdir(cloud) else []
        found = [os.path.join(cloud, d, "My Drive") for d in names if d.startswith("GoogleDrive-")]
    return [d for d in found if os.path.isdir(d)]


# ---------- grouping ----------

def base_name(path):
    name = os.path.basename(path)
    if not os.path.isdir(path) and "." in name[1:]:
        name = name.rsplit(".", 1)[0]
    return name.replace("ـ", "")


def group_key(path):
    """Returns (key, is_size) or (None, False) when the item should not be grouped."""
    base = base_name(path).lower()
    if base.startswith(NO_GROUP):
        return None, False
    tokens = [t for t in re.split(r"[\s\-_()\[\]|,]+", base) if t]
    if not tokens:
        return None, False
    first = tokens[0]
    if SIZE.match(first):
        return first, True
    first = re.sub(r"[\d٠-٩]+$", "", first)  # "فاتورة2" -> "فاتورة"
    if len(first) < 2:
        return None, False
    if first in TWO_WORD and len(tokens) > 1:
        return first + " " + tokens[1], False
    return first, False


def nice_name(paths, key):
    names = [base_name(p) for p in paths]
    p = os.path.commonprefix(names)
    if any(len(n) > len(p) and n[len(p)].isalnum() for n in names) and p and p[-1].isalnum():
        p = re.split(r"[\s\-_()\[\]|,]+(?=[^\s\-_()\[\]|,]*$)", p)[0]
    p = p.strip(" -_()[]|,.")
    return p if len(p) >= 2 else key


def type_folder(path):
    name = os.path.basename(path).lower()
    if os.path.isdir(path):
        return "فولدرات"
    if name.startswith("screen recording"):
        return "تسجيلات الشاشة"
    if name.startswith("screenshot"):
        return "صور الشاشة"
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    for folder, exts in TYPES:
        if ext in exts.split():
            return folder
    return "أخرى"


def plan(items, groups):
    by_key = {}
    keys = {}
    for p in items:
        k, is_size = group_key(p)
        keys[p] = (k, is_size)
        if k:
            by_key.setdefault(k, []).append(p)
    out = {}
    for p in items:
        k, is_size = keys[p]
        if k and k in groups:
            folder = groups[k]
        elif k and len(by_key[k]) >= 2:
            name = nice_name(by_key[k], k)
            folder = os.path.join(SIZE_FOLDER, name) if is_size else name
            groups[k] = folder
        elif is_size:
            folder = SIZE_FOLDER
        else:
            folder = type_folder(p)
        out[p] = folder
    return out


# ---------- what may move ----------

def is_hidden_or_placeholder(path):
    st = os.lstat(path)
    if WINDOWS:
        attrs = getattr(st, "st_file_attributes", 0)
        return bool(attrs & (WIN_HIDDEN | WIN_SYSTEM | WIN_CLOUD_ONLY))
    return not os.path.isdir(path) and bool(getattr(st, "st_flags", 0) & MAC_DATALESS)


def open_files_mac(src):
    try:
        out = subprocess.run(["lsof", "-F", "n"], capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return set()
    return {l[1:] for l in out.splitlines() if l.startswith("n" + src)}


def is_locked_windows(path):
    """True when another app holds the file open without sharing it (e.g. Office, Photoshop)."""
    if os.path.isdir(path) or not os.access(path, os.W_OK):
        return False  # read-only files cannot be tested this way
    try:
        with open(path, "r+b"):
            return False
    except OSError:
        return True


def newest_mtime(path):
    newest = os.lstat(path).st_mtime
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for n in dirs + files:
                if n.endswith((".download", ".crdownload", ".part")):
                    return time.time()
                try:
                    newest = max(newest, os.lstat(os.path.join(root, n)).st_mtime)
                except OSError:
                    pass
    return newest


def eligible_items(src):
    keep = set()
    if os.path.exists(KEEP_FILE):
        with open(KEEP_FILE, encoding="utf-8") as f:
            keep = {l.strip() for l in f if l.strip() and not l.startswith("#")}
    busy = set() if WINDOWS else open_files_mac(src)
    now = time.time()
    items = []
    for name in sorted(os.listdir(src)):
        path = os.path.join(src, name)
        if name.startswith((".", "~")) or name.lower() in SKIP_NAMES or name in keep:
            continue
        if name.lower().endswith(SKIP_SUFFIXES):
            continue
        if is_hidden_or_placeholder(path):
            continue
        if now - newest_mtime(path) < MIN_AGE:
            continue
        if WINDOWS:
            in_use = is_locked_windows(path)
        else:
            in_use = any(b == path or b.startswith(path + "/") for b in busy)
        if in_use:
            log(f"SKIP (open in an app): {name}")
            continue
        items.append(path)
    return items


# ---------- moving ----------

def unique_target(folder, name, is_dir):
    target = os.path.join(folder, name)
    if not os.path.exists(target):
        return target
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    if is_dir or "." not in name[1:]:
        new = f"{name} ({stamp})"
    else:
        stem, ext = name.rsplit(".", 1)
        new = f"{stem} ({stamp}).{ext}"
    target = os.path.join(folder, new)
    return None if os.path.exists(target) else target


def move_mac(src, target):
    r = subprocess.run(["/bin/mv", "-n", "--", src, target], capture_output=True, text=True)
    return r.stderr.strip()


def move_windows(src, target):
    """Copy, then delete the original. Never overwrites; never loses the original."""
    if os.path.lexists(target):
        return "target exists"
    try:
        if os.path.isdir(src):
            shutil.copytree(src, target, symlinks=True)
        else:
            shutil.copy2(src, target)
    except OSError as e:
        if os.path.isdir(target):
            shutil.rmtree(target, ignore_errors=True)
        elif os.path.isfile(target):
            os.remove(target)
        return f"copy failed: {e}"
    try:
        if os.path.isdir(src):
            shutil.rmtree(src)
        else:
            os.remove(src)
    except OSError as e:
        if os.path.isfile(src) and os.path.isfile(target):
            os.remove(target)  # file still on the Desktop: drop the copy, try again next run
            return f"could not remove original: {e}"
        return f"copied, but some files could not be removed from the Desktop: {e}"
    return ""


def move_item(src, target):
    return move_windows(src, target) if WINDOWS else move_mac(src, target)


def drive_root():
    """The destination folder, or None when Google Drive is not found."""
    drives = drive_dirs()
    return os.path.join(drives[0], DEST_NAME) if drives else None


def show_stats():
    lines = []
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            lines = f.read().splitlines()
    runs = [l for l in lines if "Run done" in l]
    print(f"العناصر المنقولة (Moved so far): {sum(' MOVED: ' in l for l in lines)}")
    print(f"محاولات لم تنجح (Failed): {sum(' FAILED ' in l for l in lines)}")
    print(f"مرات التشغيل (Runs): {len(runs)}")
    print(f"آخر تشغيل (Last run): {runs[-1][:19] if runs else '-'}")
    print(f"الحد الأدنى للعمر بالأيام (Minimum age, days): {MIN_AGE_DAYS:g}")
    print(f"الوجهة (Destination): {drive_root() or 'Google Drive not found'}")
    return 0


def set_age(days):
    if not 0 < days <= 365:
        print("DAYS must be more than 0 and at most 365", file=sys.stderr)
        return 2
    settings = load_settings()
    settings["min_age_days"] = days
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=1)
    log(f"SETTINGS: minimum age is now {days:g} day(s)")
    print(f"{days:g}")
    return 0


def main():
    if os.path.exists(PAUSE_FILE) and not (PREVIEW or FORCE):
        log("PAUSED (PAUSE file exists), nothing done")
        return 0
    src = desktop_dir()
    root = drive_root()
    if not root:
        if not PREVIEW:
            log("ERROR: Google Drive folder not found (is Google Drive for desktop running?). Nothing moved.")
            return 1
        root = os.path.join("<Google Drive>", "My Drive", DEST_NAME)

    groups = {}
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, encoding="utf-8") as f:
            groups = json.load(f)
    try:
        moves = plan(eligible_items(src), groups)
    except PermissionError:
        log("ERROR: access to the Desktop was blocked (macOS: give python3 Full Disk Access, see README). Nothing moved.")
        return 1

    if PREVIEW:
        by_folder = {}
        for p, f in moves.items():
            by_folder.setdefault(f, []).append(os.path.basename(p))
        print(f"{len(moves)} item(s) would move to: {root}\n")
        for f in sorted(by_folder):
            print(f"[{f}]  ({len(by_folder[f])})")
            for n in by_folder[f]:
                print("    " + n)
        return 0

    moved = 0
    for p, f in moves.items():
        name = os.path.basename(p)
        folder = os.path.join(root, f)
        os.makedirs(folder, exist_ok=True)
        target = unique_target(folder, name, os.path.isdir(p))
        if not target:
            log(f"SKIP (name taken twice): {name}")
            continue
        if os.path.basename(target) != name:
            log(f"NAME EXISTS in Drive, saving as: {os.path.basename(target)}")
        err = move_item(p, target)
        if not os.path.lexists(p) and os.path.lexists(target):
            log(f"MOVED: {name} -> {DEST_NAME}/{f}/{os.path.basename(target)}")
            moved += 1
        else:
            log(f"FAILED (still on Desktop): {name} {err}")
    with open(GROUPS_FILE, "w", encoding="utf-8") as fh:
        json.dump(groups, fh, ensure_ascii=False, indent=1)
    log(f"Run done, moved {moved} item(s)")
    return 0


def cli():
    global PREVIEW, FORCE
    ap = argparse.ArgumentParser(description="Desktop to Drive: move old Desktop items to Google Drive.")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--preview", action="store_true", help="print the plan, move nothing")
    mode.add_argument("--now", action="store_true", help="move now, even when paused")
    mode.add_argument("--stats", action="store_true", help="print totals from log.txt")
    mode.add_argument("--where", action="store_true", help="print the destination folder")
    mode.add_argument("--set-age", type=float, metavar="DAYS", help="minimum age before an item moves")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Arabic names, also when redirected on Windows
    if a.stats:
        return show_stats()
    if a.set_age is not None:
        return set_age(a.set_age)
    if a.where:
        root = drive_root()
        if not root:
            print("Google Drive folder not found", file=sys.stderr)
            return 1
        os.makedirs(root, exist_ok=True)
        print(root)
        return 0
    PREVIEW, FORCE = a.preview, a.now
    return main()


if __name__ == "__main__":
    sys.exit(cli())
