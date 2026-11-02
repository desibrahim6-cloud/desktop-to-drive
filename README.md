# Desktop to Drive

[العربية](#بالعربي) · [English](#english)

---

## بالعربي

أداة مجانية مفتوحة المصدر تحافظ على نظافة سطح المكتب؛ إذ تنقل (قصًّا لا نسخًا) الملفات والمجلدات التي لم تُعدَّل منذ يوم كامل إلى Google Drive، وتجمع الملفات المترابطة التي تبدأ أسماؤها بالكلمة نفسها في مجلد واحد.

### المزايا
- النقل إلى المجلد `My Drive/Mac Desktop` على macOS، أو `My Drive/Windows Desktop` على Windows.
- تجميع الملفات المترابطة (مثل `تقرير.pdf` و`تقرير نهائي.docx`) في مجلد يحمل اسمها، وتصنيف بقية الملفات حسب النوع (صور، PDF، فيديو، تصاميم، مستندات...).
- **لا تستبدل أي ملف موجود**: إذا وُجد الاسم نفسه في Drive، يُضاف التاريخ والوقت إلى اسم الملف الجديد.
- تتجاهل الملفات المخفية، والتنزيلات غير المكتملة، والملفات المفتوحة في أي برنامج، والعناصر التي عُدِّلت حديثًا، وكل ما تضيفه إلى قائمة المستثنيات.
- تتجاهل ملفات iCloud وOneDrive غير المنزَّلة على الجهاز، حتى لا يؤدي النقل إلى تنزيلها.
- تسجّل كل عملية في الملف `log.txt`.

### واجهة البرنامج
| الإجراء | الوصف |
|---|---|
| معاينة ما سيُنقل | يعرض خطة النقل دون نقل أي شيء |
| النقل الآن | ينقل فورًا بعد طلب التأكيد |
| تفعيل النقل التلقائي | يشغّل الأداة تلقائيًا كل ساعة |
| إيقاف النقل التلقائي | يوقف التشغيل التلقائي كليًا |
| الإحصاءات | عدد العناصر المنقولة، وآخر تشغيل، والوجهة |
| فتح مجلد الوجهة | يفتح مجلد الأداة في Google Drive |
| العناصر المستثناة | إضافة ملفات أو مجلدات تبقى دائمًا على سطح المكتب |
| الإعدادات | تحديد الحد الأدنى لعمر الملف بالأيام قبل نقله |
| فتح سجل العمليات | يعرض كل ما نفّذته الأداة |

### المتطلبات
- برنامج [Google Drive for desktop](https://www.google.com/drive/download/) مثبّتًا مع تسجيل الدخول (مجاني).
- Python 3: متوفر في macOS (وافق على تثبيت "Command Line Tools" إذا طُلب منك ذلك). أما في Windows فنزّله مجانًا من [python.org](https://www.python.org/downloads/) مع تفعيل خيار **Add python.exe to PATH**.

### التثبيت على macOS
افتح تطبيق **Terminal على جهاز الماك**، ثم نفّذ الأمر التالي من داخل مجلد المشروع:
```bash
./mac/install.sh
```
يثبّت هذا الأمر الأداة في المجلد `~/DesktopToDrive`، والبرنامج **Desktop to Drive** في مجلد Applications. يبقى النقل التلقائي **متوقفًا** إلى أن تختار "تفعيل النقل التلقائي".

إذا أظهر السجل أن macOS منع الوصول إلى سطح المكتب، فافتح: System Settings > Privacy & Security > Full Disk Access، واضغط زر +، ثم أضف ملف Python المذكور في السجل (غالبًا
`/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9`).

> ⚠️ إذا كان سطح المكتب متزامنًا مع iCloud (خيار "Desktop & Documents Folders")، فيُستحسن إيقاف هذه المزامنة أولًا؛ لأن جهازًا آخر قد يعيد الملفات المنقولة إلى سطح المكتب.

### التثبيت على Windows
1. نزّل المشروع (Code > Download ZIP) ثم فُكّ ضغطه.
2. افتح المجلد `windows` وانقر نقرًا مزدوجًا على `install.bat`.
3. افتح **Desktop to Drive** من قائمة Start، وستظهر نافذة تضم الإجراءات نفسها.

تبحث الأداة عن المجلد `G:\My Drive` (أو أي حرف آخر يحتوي على `My Drive`)، وتستخدم Task Scheduler للتشغيل التلقائي، وتُبقي الاختصارات (`.lnk` و`.url`) على سطح المكتب.

### الإعدادات المتقدمة
- `keep.txt`: كل سطر فيه اسم عنصر يبقى على سطح المكتب.
- `settings.json`: يحفظ الحد الأدنى للعمر (`min_age_days`) واسم مجلد الوجهة (`dest_folder`).
- وجود ملف باسم `PAUSE` بجوار `move.py` يوقف التشغيل التلقائي مؤقتًا.
- أوامر سطر الأوامر: `--preview` و`--now` و`--stats` و`--where` و`--set-age DAYS`.

---

## English

A free tool that keeps your Desktop clean: it **moves** (cut, not copy) files and folders that have not changed for a full day into Google Drive, and puts files whose names start with the same word into one folder.

### What it does
- Moves items to `My Drive/Mac Desktop` (macOS) or `My Drive/Windows Desktop` (Windows).
- Related files (same start of name, e.g. `Report.pdf` and `Report final.docx`) go into a folder named after them. Everything else goes into a folder by type (images, PDF, video, ...).
- **Never overwrites**: if a name already exists in Drive, it adds a date and time to the new name.
- Skips hidden files, unfinished downloads, items open in an app, items changed less than a day ago, and every name listed in `keep.txt`.
- Skips iCloud / OneDrive files that are not downloaded to this computer (moving them would download them).
- Everything it does is written to `log.txt`.

### Requirements
- [Google Drive for desktop](https://www.google.com/drive/download/), installed and signed in (free).
- Python 3. macOS: built in (accept the "Command Line Tools" install if asked). Windows: free from [python.org](https://www.python.org/downloads/); tick **Add python.exe to PATH**.

### Install on macOS
In **Terminal on the Mac**, from the project folder:
```bash
./mac/install.sh
```
This puts the tool in `~/DesktopToDrive` and the **Desktop to Drive** app in Applications. Automatic moving stays **OFF** until you press "Turn on".

The app offers:

| Action | What it does |
|---|---|
| Preview | Shows the plan, moves nothing |
| Move now | Moves right away, after asking you |
| Turn on | Runs every hour by itself (launchd on macOS, Task Scheduler on Windows) |
| Turn off | Stops automatic runs completely |
| Statistics | Items moved, last run, destination |
| Open Drive folder | Opens the destination folder in Google Drive |
| Excluded items | Add files or folders that always stay on the Desktop |
| Settings | Minimum age in days before an item moves |
| Open log | Shows everything the tool did |

If the log says macOS blocked access to the Desktop: System Settings > Privacy & Security > Full Disk Access > + > add the python binary named in the log (usually
`/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9`).

> ⚠️ If your Desktop syncs with iCloud ("Desktop & Documents Folders"), turn that off first. Otherwise another device can bring moved files back.

### Install on Windows
1. Download the project (Code > Download ZIP) and unzip it.
2. Open the `windows` folder and double-click `install.bat`.
3. Open **Desktop to Drive** from the Start menu. A window with the same actions opens.

It looks for `G:\My Drive` (or any drive letter with a `My Drive` folder). Automatic moving uses Task Scheduler. Shortcuts (`.lnk`, `.url`) stay on the Desktop.

### Settings
- `keep.txt`: one name per line to keep on the Desktop.
- `settings.json`: minimum age (`min_age_days`) and destination folder name (`dest_folder`).
- A file named `PAUSE` next to `move.py` pauses automatic runs.
- Command line: `--preview`, `--now`, `--stats`, `--where`, `--set-age DAYS`.
- For testing: `SRC` (instead of the Desktop), `DEST` (instead of My Drive), `MIN_AGE_MIN` (age in minutes, default 1440 = 1 day).

### Tests
```bash
python3 -m unittest discover tests
```
The tests use fake folders. They run the Windows code path too (copy then delete, locked files, hidden attributes), but cannot test Task Scheduler or a real `G:` drive.

### Layout
```
move.py              the tool (macOS + Windows)
mac/                 install.sh, app.applescript (the app), build-app.sh, start.sh, stop.sh
windows/             install.bat, Desktop to Drive.bat, menu.ps1 (the window), start.ps1, stop.ps1, common.ps1
tests/test_move.py
```
