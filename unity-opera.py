########################################################
# Unity Opera
#
# Author:      Kyle Baker (kyleabaker.com)
# Description: Provides several features for Unity users
#              who also use Opera or Opera Next that are
#              not available by default.
# Version:     2011-05-07
# Help:        python unity-opera.py --help
########################################################

from gi.repository import Unity, Gio, GObject, Dbusmenu
from cStringIO import StringIO
import sys, os, commands, subprocess, re

loop = GObject.MainLoop()

# Global variables
home = os.getenv("HOME")
current_tabs = 0
current_speeddial = ""
tab_count_changed = False
is_first_check = True
bool_quicklist = False
bool_speeddial = False
bool_count_tabs = False
bool_urgency = False
bool_progress_bar = False

# Set version of Opera here from command args or assume opera (opera, opera-next)
#         format: python unity-opera.py (opera or opera-next) (-qcup)
if len(sys.argv) > 2:
	opera = sys.argv[1]
	if "q" in sys.argv[2]:
		bool_quicklist = True
	if "s" in sys.argv[2]:
		bool_speeddial = True
	if "c" in sys.argv[2]:
		bool_count_tabs = True
	if "u" in sys.argv[2]:
		bool_urgency = True
	if "p" in sys.argv[2]:
		bool_progress_bar = True
elif len(sys.argv) > 1:
	if "--help" in sys.argv[1]:
		print "Usage: python unity-opera.py [opera channel] [options]\n"
		print "Opera channels:\n"
		print " opera"
		print " opera-next\n"
		print "Options:\n"
		print " q           Enable basic quicklist"
		print " s           Enable Speed Dial entries in quicklist"
		print " c           Enable tab count"
		print " u           Enable urgency notification"
		print " p           Enable progress bar for downloads\n"
		print "Notes:\n"
		print " * Opera channels and Options are both optional"
		print " * Options requires use of Opera channels arg"
		print " * Progress bar for downloads is not functional at"
		print "   this time and may not be possible.\n"
		print "Example usage:\n"
		print " Use all available features"
		print " * python unity-opera.py\n"
		print " Count tabs and use urgency notification"
		print " * python unity-opera.py opera -cu\n"
		print " Use Opera Next and only Quicklist with Speed Dial entries"
		print " * python unity-opera.py opera-next -qs"
		exit()
	opera = sys.argv[1]
	bool_quicklist = True
	bool_speeddial = True
	bool_count_tabs = True
	bool_urgency = True
	bool_progress_bar = True
else:
	opera = "opera"
	bool_quicklist = True
	bool_speeddial = True
	bool_count_tabs = True
	bool_urgency = True
	bool_progress_bar = True

# Pretend to be opera
launcher = Unity.LauncherEntry.get_for_desktop_id (opera + "-browser.desktop")

########################################################
# is_opera_running()
#
# Description: Returns boolean True if Opera is running
########################################################
def is_opera_running():
	output = commands.getoutput("ps -A | grep '" + opera + "' | awk '{print $4}'").split('\n')
	i = 0
	while i < len(output):
		if output[i] == opera:
			return True
		i = i + 1
		pass # do something
	return False


########################################################
# menu_open_new_tab(a, b)
# menu_open_new_private_tab(a, b)
# menu_open_new_window(a, b)
# menu_open_speeddial_item(a, b, url)
# update_quicklist()
#
# Description: List of functions for quicklist menu
########################################################
def menu_open_new_tab(a, b):
	os.popen3(opera + " -newtab")
def menu_open_new_private_tab(a, b):
	os.popen3(opera + " -newprivatetab")
def menu_open_new_window(a, b):
	os.popen3(opera + " -newwindow")
def menu_open_mail(a, b):
	os.popen3(opera + " -mail")
	#TODO: Fix this command so it actually opens M2
def menu_open_speeddial_item(a, b, url):
	os.popen3(opera + " " + url)
def update_quicklist():
	# Set quicklist menu items from speeddial
	global current_speeddial, bool_quicklist
	title = ""
	url = ""

	# Make sure the speed dial file exists before attempting to read it
	if not os.path.isfile(home + "/." + opera + "/speeddial.ini"):
		print "Error: Unable to open " + home + "/." + opera + "/speeddial.ini"
		exit()
	else:
		if bool_speeddial:
			try:
				file = open(home + "/." + opera + "/speeddial.ini")
				temp = file.read()
				if temp == current_speeddial:
					return True
				else:
					current_speeddial = temp
					print "Updating Quicklist with Speed Dial entries:"
				file.close()
			except IOError:
				pass
		
		#TODO: Clear items previously added to menu so we can add new updated items
		
		# Set default quicklist items
		ql = Dbusmenu.Menuitem.new()
		item1 = Dbusmenu.Menuitem.new()
		item1.property_set (Dbusmenu.MENUITEM_PROP_LABEL, "New Tab")
		item1.property_set_bool (Dbusmenu.MENUITEM_PROP_VISIBLE, True)
		item1.connect ("item-activated", menu_open_new_tab)
		item2 = Dbusmenu.Menuitem.new()
		item2.property_set (Dbusmenu.MENUITEM_PROP_LABEL, "New Private Tab")
		item2.property_set_bool (Dbusmenu.MENUITEM_PROP_VISIBLE, True)
		item2.connect ("item-activated", menu_open_new_private_tab)
		item3 = Dbusmenu.Menuitem.new()
		item3.property_set (Dbusmenu.MENUITEM_PROP_LABEL, "New Window")
		item3.property_set_bool (Dbusmenu.MENUITEM_PROP_VISIBLE, True)
		item3.connect ("item-activated", menu_open_new_window)
		ql.child_append (item1)
		ql.child_append (item2)
		ql.child_append (item3)
		
		# Add Mail to menu if an account exists
		if os.path.isfile(home + "/." + opera + "/mail/accounts.ini"):
			file = open(home + "/." + opera + "/mail/accounts.ini")
			if "Count=" in file.read():
				item4 = Dbusmenu.Menuitem.new()
				item4.property_set (Dbusmenu.MENUITEM_PROP_LABEL, "Mail")
				item4.property_set_bool (Dbusmenu.MENUITEM_PROP_VISIBLE, True)
				item4.connect ("item-activated", menu_open_mail)
				ql.child_append (item4)
		
		if bool_speeddial:
			# Reread speeddial.ini since it was flush on the diff
			file = open(home + "/." + opera + "/speeddial.ini")
			
			# Set Speed Dial menu items for quicklist
			while 1:
				line = file.readline()
				if not line:
					break
				if "Custom Title=" in line:
					pass
				elif "Title=" in line:
					title = str(line[line.find("=")+1:len(line)]).rstrip('\n')
				elif "Url=" in line:
					url = str(line[line.find("=")+1:len(line)]).rstrip('\n')
					item5 = Dbusmenu.Menuitem.new ()
					item5.property_set (Dbusmenu.MENUITEM_PROP_LABEL, title)
					item5.property_set_bool (Dbusmenu.MENUITEM_PROP_VISIBLE, True)
					item5.connect ("item-activated", menu_open_speeddial_item, url)
					ql.child_append (item5)
					print "  " + title + " " + url
				pass # do something
			file.close

		# Activate quicklist
		launcher.set_property("quicklist", ql)
		
		# If current_speeddial is empty, then its disabled. Change it to stop processing
		if current_speeddial == "":
			bool_quicklist = False


########################################################
# update_tabs()
#
# Description: Get number of open tabs across all windows
########################################################
def update_tabs():
	global current_tabs, tab_count_changed
	tabs = 0
	windows = 0
	
	# Make sure the session file exists before attempting to read it
	if not os.path.isfile(home + "/." + opera + "/sessions/autosave.win"):
		print "Error: Unable to open " + home + "/." + opera + "/sessions/autosave.win"
		exit()
	
	try:
		file = open(home + "/." + opera + "/sessions/autosave.win")
	except IOError:
		pass
	
	while 1:
		line = file.readline()
		if not line:
			break
		if "window count" in line:
			tabs = int(line[line.find("=")+1:len(line)])
		elif "type=0" in line:
			windows = windows + 1
		pass # do something
	file.close
	tabs = tabs - windows

	# Set number of open tabs across all windows
	if tabs == current_tabs:
		tab_count_changed = False
		return True
	elif tabs > 0:
		if bool_count_tabs:
			launcher.set_property("count", tabs)
			launcher.set_property("count_visible", True)
		if tabs > current_tabs:
			tab_count_changed = True
		current_tabs = tabs
		print "Updating tab count"
	else:
		launcher.set_property("count", 0)
		launcher.set_property("count_visible", False)
		current_tabs = 0
		tab_count_changed = False
	return True


########################################################
# update_progress()
#
# Description: Get number of open tabs across all windows
########################################################
def update_progress():
	return True
#	# Set progress to 42% done 
#	launcher.set_property("progress", 0.42)
#	launcher.set_property("progress_visible", True)


########################################################
# update_progress()
#
# Description: Get number of open tabs across all windows
########################################################
def update_urgency():
	if not is_opera_focused():
		if tab_count_changed:
			launcher.set_property("urgent", True)
			return
	else:
		launcher.set_property("urgent", False)


########################################################
# get_active_window_title()
#
# Description: Get the currently focused window. Used by
#              update_urgency() to check for Opera.
########################################################
def is_opera_focused():
	global is_first_check
	if is_first_check:
		is_first_check = False
		return True
	
	root_check = ''
	root = subprocess.Popen(['xprop', '-root'],  stdout=subprocess.PIPE)

	if root.stdout != root_check:
		root_check = root.stdout

		for i in root.stdout:
			if '_NET_ACTIVE_WINDOW(WINDOW):' in i:
				id_ = i.split()[4]
				id_w = subprocess.Popen(['xprop', '-id', id_], stdout=subprocess.PIPE)
		id_w.wait()
		buff = []
		for j in id_w.stdout:
			buff.append(j)

		for line in buff:
			match = re.match("WM_NAME\((?P<type>.+)\) = (?P<name>.+)", line)
			if match != None:
				type = match.group("type")
				if type == "STRING" or type == "COMPOUND_TEXT":
					if " - Opera" in match.group("name"):
						return True
	return False

		
########################################################
# get_updates()
#
# Description: Check for updates to apply
########################################################
def get_updates():
	global current_tabs, is_first_check
	
	if bool_quicklist:
		update_quicklist()
	
	if not is_opera_running():
		launcher.set_property("count_visible", False)
		launcher.set_property("urgent", False)
		
		#initialize some settings so it works properly next time Opera's opened
		current_tabs = 0
		is_first_check = True
		return True
	else:
		if bool_count_tabs or bool_urgency:
			update_tabs()
		#if bool_progress_bar:
			#update_progress()
		if bool_urgency:
			update_urgency()
	return True


# Call tab updates
GObject.timeout_add_seconds(1, get_updates)

loop.run()
