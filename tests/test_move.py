"""Tests on fake folders. Run: python3 -m unittest discover tests

The Windows tests run the Windows code path (copy + delete, locked-file check, hidden
attributes) on any OS by switching move.WINDOWS on; they cannot test Task Scheduler or
the real G: drive.
"""
import contextlib, importlib.util, io, os, shutil, sys, tempfile, time, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("move", os.path.join(HERE, "..", "move.py"))
move = importlib.util.module_from_spec(spec)
spec.loader.exec_module(move)

OLD = time.time() - 3 * 86400


def make(root, name, text="data", age=OLD):
    path = os.path.join(root, name)
    if name.endswith("/"):
        os.makedirs(path)
        open(os.path.join(path, "inside.txt"), "w").close()
        os.utime(os.path.join(path, "inside.txt"), (age, age))
    else:
        with open(path, "w") as f:
            f.write(text)
    os.utime(path.rstrip("/"), (age, age))
    return path.rstrip("/")


class Base(unittest.TestCase):
    windows = False

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.src = os.path.join(self.tmp, "Desktop")
        self.drive = os.path.join(self.tmp, "My Drive")
        tool = os.path.join(self.tmp, "tool")
        for d in (self.src, self.drive, tool):
            os.makedirs(d)
        os.environ["SRC"], os.environ["DEST"] = self.src, self.drive
        self.saved = {k: getattr(move, k) for k in
                      ("WINDOWS", "DEST_NAME", "LOG", "GROUPS_FILE", "KEEP_FILE", "PAUSE_FILE", "SETTINGS_FILE", "PREVIEW", "FORCE")}
        move.WINDOWS = self.windows
        move.DEST_NAME = "Windows Desktop" if self.windows else "Mac Desktop"
        move.LOG = os.path.join(tool, "log.txt")
        move.GROUPS_FILE = os.path.join(tool, "groups.json")
        move.KEEP_FILE = os.path.join(tool, "keep.txt")
        move.PAUSE_FILE = os.path.join(tool, "PAUSE")
        move.SETTINGS_FILE = os.path.join(tool, "settings.json")
        move.PREVIEW = move.FORCE = False
        self.root = os.path.join(self.drive, move.DEST_NAME)

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(move, k, v)
        del os.environ["SRC"], os.environ["DEST"]
        shutil.rmtree(self.tmp)

    def desktop(self):
        return sorted(os.listdir(self.src))

    def log(self):
        if not os.path.exists(move.LOG):
            return ""
        with open(move.LOG, encoding="utf-8") as f:
            return f.read()


class Common:
    """Behaviour that must be the same on macOS and Windows."""

    def test_groups_and_types(self):
        for n in ("Brochure-Review.zip", "Brochure.pdf", "فاتورة.psd", "فاتورة لوحة.pdf",
                  "30x40 banner.ai", "30x40 flyer.pdf", "notes.txt", "Album/"):
            make(self.src, n)
        self.assertEqual(move.main(), 0)
        self.assertEqual(self.desktop(), [])
        for rel in ("Brochure/Brochure.pdf", "Brochure/Brochure-Review.zip", "فاتورة/فاتورة.psd",
                    "تصاميم بالمقاس/30x40/30x40 flyer.pdf", "مستندات/notes.txt",
                    "فولدرات/Album/inside.txt"):
            self.assertTrue(os.path.exists(os.path.join(self.root, rel)), rel)

    def test_skips_new_hidden_partial_and_kept(self):
        make(self.src, "fresh.pdf", age=time.time())
        make(self.src, ".hidden")
        make(self.src, "movie.mp4.crdownload")
        make(self.src, "keep me.pdf")
        make(self.src, "Folder with download/")
        make(os.path.join(self.src, "Folder with download"), "x.part", age=OLD)
        with open(move.KEEP_FILE, "w") as f:
            f.write("# comment\nkeep me.pdf\n")
        move.main()
        self.assertEqual(self.desktop(), [".hidden", "Folder with download", "fresh.pdf",
                                          "keep me.pdf", "movie.mp4.crdownload"])

    def test_never_overwrites(self):
        os.makedirs(os.path.join(self.root, "PDF"))
        make(os.path.join(self.root, "PDF"), "a.pdf", text="old")
        make(self.src, "a.pdf", text="new")
        move.main()
        files = sorted(os.listdir(os.path.join(self.root, "PDF")))
        self.assertEqual(len(files), 2)
        with open(os.path.join(self.root, "PDF", "a.pdf")) as f:
            self.assertEqual(f.read(), "old")
        self.assertIn("NAME EXISTS", self.log())

    def test_preview_moves_nothing(self):
        make(self.src, "a.pdf")
        move.PREVIEW = True
        move.main()
        self.assertEqual(self.desktop(), ["a.pdf"])
        self.assertFalse(os.path.exists(self.root))
        self.assertEqual(self.log(), "")

    def test_pause_and_now(self):
        make(self.src, "a.pdf")
        open(move.PAUSE_FILE, "w").close()
        move.main()
        self.assertEqual(self.desktop(), ["a.pdf"])
        self.assertIn("PAUSED", self.log())
        move.FORCE = True
        move.main()
        self.assertEqual(self.desktop(), [])

    def test_groups_remembered(self):
        make(self.src, "Brand-logo.ai")
        make(self.src, "Brand-card.pdf")
        move.main()
        make(self.src, "Brand-new.pdf")
        move.main()
        self.assertTrue(os.path.exists(os.path.join(self.root, "Brand", "Brand-new.pdf")))

    def test_stats(self):
        make(self.src, "a.pdf")
        make(self.src, "b.pdf")
        move.main()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            move.show_stats()
        self.assertIn("(Moved so far): 2", out.getvalue())
        self.assertIn("(Runs): 1", out.getvalue())

    def test_set_age(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(move.set_age(0), 2)
            self.assertEqual(move.set_age(3), 0)
        self.assertEqual(move.load_settings(), {"min_age_days": 3})


class MacTest(Common, Base):
    windows = False


class WindowsTest(Common, Base):
    windows = True

    def test_skips_shortcuts_and_desktop_ini(self):
        saved = move.SKIP_SUFFIXES
        move.SKIP_SUFFIXES = saved + (".lnk", ".url")
        try:
            make(self.src, "Chrome.lnk")
            make(self.src, "desktop.ini")
            make(self.src, "a.pdf")
            move.main()
            self.assertEqual(self.desktop(), ["Chrome.lnk", "desktop.ini"])
        finally:
            move.SKIP_SUFFIXES = saved

    def test_locked_file_stays(self):
        path = make(self.src, "open.docx")
        saved = move.is_locked_windows
        move.is_locked_windows = lambda p: p == path
        try:
            move.main()
        finally:
            move.is_locked_windows = saved
        self.assertEqual(self.desktop(), ["open.docx"])
        self.assertIn("SKIP (open in an app)", self.log())

    def test_failed_delete_keeps_original_and_drops_copy(self):
        make(self.src, "a.pdf")
        saved = os.remove

        def deny(p, *a, **k):
            if p.startswith(self.src):
                raise PermissionError("in use")
            return saved(p, *a, **k)

        move.os.remove = deny
        try:
            move.main()
        finally:
            move.os.remove = saved
        self.assertEqual(self.desktop(), ["a.pdf"])
        self.assertFalse(os.path.exists(os.path.join(self.root, "PDF", "a.pdf")))
        self.assertIn("FAILED", self.log())

    def test_hidden_attribute(self):
        path = make(self.src, "a.pdf")

        class St:
            st_file_attributes = move.WIN_HIDDEN

        saved = move.os.lstat
        move.os.lstat = lambda p: St() if p == path else saved(p)
        try:
            self.assertTrue(move.is_hidden_or_placeholder(path))
        finally:
            move.os.lstat = saved


if __name__ == "__main__":
    unittest.main()
