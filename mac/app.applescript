-- Desktop to Drive: the macOS app for the tool in ~/DesktopToDrive
-- Build: mac/build-app.sh (uses osacompile, part of macOS)

property toolName : "Desktop to Drive"
property toolVersion : "1.1"
property py : "/usr/bin/python3"

on toolDir()
	return (POSIX path of (path to home folder)) & "DesktopToDrive/"
end toolDir

on sh(cmd)
	return do shell script "cd " & quoted form of toolDir() & " && " & cmd
end sh

on tool(args)
	return sh(py & " move.py " & args)
end tool

on isOn()
	try
		do shell script "launchctl list | grep -q desktop-to-drive"
		return true
	on error
		return false
	end try
end isOn

on info(msg)
	display dialog msg buttons {"حسنًا — OK"} default button 1 with title toolName
end info

on confirm(msg, okLabel)
	display dialog msg buttons {"إلغاء — Cancel", okLabel} default button 1 cancel button 1 with title toolName with icon caution
end confirm

on preview()
	return sh(py & " move.py --preview > preview.txt 2>&1; head -1 preview.txt")
end preview

on addToKeep(chosen)
	repeat with f in chosen
		set p to POSIX path of f
		if p ends with "/" then set p to text 1 thru -2 of p
		set n to do shell script "basename " & quoted form of p
		sh("printf '%s\\n' " & quoted form of n & " >> keep.txt")
	end repeat
end addToKeep

on run
	try
		do shell script "test -f " & quoted form of (toolDir() & "move.py")
	on error
		display alert toolName message "لم يُعثر على الأداة في المجلد ~/DesktopToDrive. شغّل mac/install.sh أولًا." & return & return & "Tool not found in ~/DesktopToDrive. Run mac/install.sh first." as critical
		return
	end try

	set itemPreview to "👀  معاينة ما سيُنقل — Preview"
	set itemMove to "📦  النقل الآن — Move now"
	set itemOn to "▶️  تفعيل النقل التلقائي كل ساعة — Turn on"
	set itemOff to "⏹  إيقاف النقل التلقائي — Turn off"
	set itemStats to "📊  الإحصاءات — Statistics"
	set itemDrive to "☁️  فتح مجلد الوجهة في Google Drive — Open Drive folder"
	set itemKeep to "📌  العناصر المستثناة من النقل — Excluded items"
	set itemAge to "⚙️  الإعدادات: الحد الأدنى لعمر الملف — Settings: minimum age"
	set itemLog to "📄  فتح سجل العمليات — Open log"
	set itemAbout to "ℹ️  حول الأداة — About"
	set allItems to {itemPreview, itemMove, itemOn, itemOff, itemStats, itemDrive, itemKeep, itemAge, itemLog, itemAbout}

	repeat
		if isOn() then
			set state to "النقل التلقائي: مُفعَّل ✅ — Automatic moving: ON"
		else
			set state to "النقل التلقائي: متوقف ⏹ — Automatic moving: OFF"
		end if
		set choice to choose from list allItems with title toolName with prompt state & return & "اختر إجراءً — Choose an action:" OK button name "تنفيذ — Run" cancel button name "خروج — Quit"
		if choice is false then exit repeat
		set choice to item 1 of choice

		try
			if choice is itemPreview then
				preview()
				sh("open -e preview.txt")

			else if choice is itemMove then
				set summary to preview()
				if summary starts with "0 item" then
					info("لا توجد عناصر تستوفي شروط النقل حاليًا." & return & "Nothing to move now.")
				else
					sh("open -e preview.txt")
					confirm("سيتم نقل العناصر التالية (قصّ لا نسخ) من سطح المكتب إلى Google Drive:" & return & summary & return & return & "هل تريد المتابعة؟ — Move them now?", "نقل — Move")
					set res to tool("--now; tail -1 log.txt")
					info("اكتملت العملية ✅ — Done" & return & return & res)
				end if

			else if choice is itemOn then
				confirm("ستنقل الأداة تلقائيًا كل ساعة العناصر التي لم تُعدَّل منذ المدة المحددة في الإعدادات." & return & "Old Desktop items will move every hour by themselves." & return & return & "هل تريد التفعيل؟ — Turn on?", "تفعيل — Turn on")
				sh("./start.sh")
				info("تم تفعيل النقل التلقائي ✅ — Automatic moving is ON")

			else if choice is itemOff then
				sh("./stop.sh")
				info("تم إيقاف النقل التلقائي ⏹ — Automatic moving is OFF")

			else if choice is itemStats then
				info(tool("--stats"))

			else if choice is itemDrive then
				try
					set dest to tool("--where")
				on error
					error "لم يُعثر على Google Drive. تأكد من تشغيل Google Drive for desktop وتسجيل الدخول." & return & "Google Drive not found. Make sure Google Drive for desktop is running and signed in."
				end try
				do shell script "open " & quoted form of dest

			else if choice is itemKeep then
				set b to button returned of (display dialog "العناصر المذكورة في هذه القائمة تبقى على سطح المكتب ولا تُنقل أبدًا." & return & "Items in this list always stay on the Desktop." buttons {"إضافة ملف — Add file", "إضافة مجلد — Add folder", "تحرير القائمة — Edit list"} default button 3 with title toolName)
				if b starts with "إضافة ملف" then
					addToKeep(choose file with prompt "اختر ملفًا أو أكثر — Choose files" default location (path to desktop folder) with multiple selections allowed)
					info("تمت الإضافة ✅ — Added")
				else if b starts with "إضافة مجلد" then
					addToKeep(choose folder with prompt "اختر مجلدًا أو أكثر — Choose folders" default location (path to desktop folder) with multiple selections allowed)
					info("تمت الإضافة ✅ — Added")
				else
					sh("touch keep.txt; open -e keep.txt")
				end if

			else if choice is itemAge then
				set current to sh(py & " -c 'import json; print(json.load(open(\"settings.json\")).get(\"min_age_days\", 1))' 2>/dev/null || echo 1")
				set answer to text returned of (display dialog "يُنقل العنصر فقط إذا لم يُعدَّل منذ عدد الأيام التالي (مثال: 1 أو 7 أو 0.5):" & return & "Move an item only if it has not changed for this many days:" default answer current buttons {"إلغاء — Cancel", "حفظ — Save"} default button 2 cancel button 1 with title toolName)
				try
					tool("--set-age " & quoted form of answer)
				on error
					error "قيمة غير صالحة. أدخل رقمًا أكبر من 0 وحتى 365." & return & "Invalid value. Enter a number above 0, up to 365."
				end try
				info("تم الحفظ ✅ — Saved: " & answer)

			else if choice is itemLog then
				sh("touch log.txt; open -e log.txt")

			else if choice is itemAbout then
				info(toolName & " " & toolVersion & return & return & "أداة مجانية تنقل العناصر القديمة من سطح المكتب إلى Google Drive وتنظّم الملفات المترابطة في مجلدات، دون استبدال أي ملف موجود." & return & return & "A free tool that moves old Desktop items to Google Drive, groups related files, and never overwrites anything." & return & return & "مجلد الأداة — Tool folder: ~/DesktopToDrive")
			end if
		on error errMsg number errNum
			if errNum is not -128 then display alert toolName message errMsg as warning
		end try
	end repeat
end run
