# -*- coding: utf-8 -*-
import os
import re
import ctypes
import gettext
import controlTypes
import addonHandler
import keyboardHandler
import speech
import wx
import oleacc
import scriptHandler
import NVDAObjects
from NVDAObjects.IAccessible import IAccessible
from NVDAObjects.window import Window
import api
import winUser
import gui
import appModuleHandler
import ui
import time

previousFocus=None
previousFore=None

idPlayList=1000
idVolume=1001
idPlayModeCombo=1003
idTreeView=1004
idJinglesPagesCombo=1008
idUpcomingEventsLabel=1012
idMenuToolBar=-208
idMainToolBar=-209
idMediaToolBar=-213
idUpcomingEventsList=-229
idEventsToolBar=-230
idActualTrackLabel=-231
idNextTrackLabel=-232
idActualTrackEdit=-240
idNextTrackEdit=-241

addonHandler.initTranslation()
controlNames={
	6042:_(u'Play list'),
	1000:_(u'Play list'),
	-229:_(u"Upcoming Events List"),
	1003:_(u'Play mode'),
	1008:_(u'Selected jingle page'),
	-240:_("On the air - Now playing "),
	-241:_(u"Next"),
	400:_("File name"),
	401:_(u'Expiration of satellite event'),
	402:_("Folder name"),
	403:_("URL"),
	404:_(u'Expiration of internet radio event'),
	413:_("Browse folder"),
	412:_("Browse file"),
	452:_("Results"),
	453:_("Find"),
	455:_("Folder")
}

mainWindow=None
tbMenu=1
tbMain=2
tbPlayModeCombo=3
tbTracks=4
tbEvents=5
tbMedia=6

wnJingles = _("Jingles")
wnFindInFolders = _("Find in folders")
auxKeys = {"control+n":1, "control+o":2, "control+s":3, "control+shift+s":4, "control+shift+a":6}

def showDialog(self,tbList, title, labelCaption=_('Choose an item to activate')):
	global mainWindow
	mainWindow=api.getForegroundObject()
	if ToolBarListDialog is not None:
		self._ToolBarListDialog = ToolBarListDialog(gui.mainFrame, tbList,_("%s toolbar") %(title), labelCaption=labelCaption)
	self._ToolBarListDialog.updateToolBar(tbList,0)
	if not self._ToolBarListDialog.IsShown():
		gui.mainFrame.prePopup()
		self._ToolBarListDialog.Show()
		self._ToolBarListDialog.Centre()
		gui.mainFrame.postPopup()

def SendEvent(window, PyEventBinder):
	cmd = wx.CommandEvent(PyEventBinder.evtType[0])
	cmd.SetEventObject(window)
	cmd.SetId(window.GetId())
	window.GetEventHandler().ProcessEvent(cmd)

def clickToolBarItem1 (location):
	(left, top, width, height) = (int(location[0]), int(location[1]), int(location[2]), int (location[3]))
	if (left+top+width+height)>0:
		x = left + (width // 2)
		y = top + (height // 2)
		old_pos = winUser.getCursorPos()
		winUser.setCursorPos (x,y)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
		winUser.mouse_event (winUser.MOUSEEVENTF_LEFTUP,0,0,0,0)
		winUser.setCursorPos(old_pos[0], old_pos[1])

def getToolBar (tb):
	ancestor=winUser.getAncestor(api.getFocusObject().windowHandle,3)
	main = NVDAObjects.IAccessible.getNVDAObjectFromEvent(ancestor, -4,0)
	ret=main.firstChild.next.next.firstChild.firstChild.firstChild.firstChild.next.next.next
	if tb == tbMenu:
		pass
	elif tb ==tbMain:
		ret=ret.previous
	elif tb == tbPlayModeCombo:
		r=[ret.previous.firstChild.firstChild,ret.firstChild.firstChild]
		for ret in r:
			if ret.windowClassName == u'ComboBox':
				break
	elif tb == tbTracks:
		ret=main.firstChild.firstChild.firstChild.firstChild.firstChild.next.next
	elif tb == tbEvents:
		ret=main.firstChild.firstChild.firstChild.firstChild.firstChild.next.next.next.next.next.next
		if ret.windowClassName!="ToolbarWindow32":
			ret=ret.previous
	elif tb == tbMedia:
		ret=main.lastChild.lastChild.firstChild.next
		if ret.windowClassName!="ToolbarWindow32":
			ret=ret.next
	return ret

def fixFocus (obj):
	try:
		h = obj.windowHandle
		o=oleacc.AccessibleObjectFromWindow(h,-4)
		o.accselect(1,0)
		api.setFocusObject(obj)
		obj.setFocus()
		api.moveMouseToNVDAObject(obj)
		api.setMouseObject(obj)
	except:
		pass

# As janelas são reconhecidas pelos IDs dos controles, não pelo título,
# para funcionar com qualquer tradução do ZaraRadio.
def isJinglesDialog(h):
	return bool(h) and winUser.getClassName(h) == u'#32770' and ctypes.windll.user32.GetDlgItem(h, 205) != 0 and ctypes.windll.user32.GetDlgItem(h, 209) != 0

def firstNumber(text):
	m = re.search(r'\d+', text or '')
	return m.group() if m else None

class AppModule(appModuleHandler.AppModule):

	def isPlayerDialog(self, obj):
		if not obj or not obj.windowHandle:
			return False
		if obj.windowClassName != u'#32770':
			return False
		
		h_651 = ctypes.windll.user32.GetDlgItem(obj.windowHandle, 651)
		h_652 = ctypes.windll.user32.GetDlgItem(obj.windowHandle, 652)
		return (h_651 != 0 or h_652 != 0)

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if isinstance(obj, IAccessible) and obj.IAccessibleRole==oleacc.ROLE_SYSTEM_RADIOBUTTON:
			clsList.insert(0, EnhancedRadioButton)
		elif isinstance(obj, IAccessible) and obj.windowControlID == 1001 and obj.role == controlTypes.ROLE_SLIDER:
			clsList.insert(0, Volume)
		elif isinstance(obj, IAccessible) and obj.windowControlID == 452 and obj.role == controlTypes.ROLE_LISTITEM:
			clsList.insert(0, ZaraSearchResultsItem)

	def event_NVDAObject_init(self,obj):
		for x in range (10):
			self.bindGesture("kb:alt+%d" %x, "changeJinglesPage")

		for gesture in auxKeys.keys():
			self.bindGesture("kb:%s" %gesture, "activateAuxMenuToolBar")
		self._ToolBarListDialog=None
		controlID=obj.windowControlID
		role=obj.role

		try:
			if obj.role == controlTypes.ROLE_SLIDER and not controlID in [1001, -407, -300] :
				obj.shouldAllowIAccessibleFocusEvent = False
		except:
			pass
		if controlID==6042 and role==controlTypes.ROLE_LIST:
			obj.name=obj.parent.parent.name+', '+'\n'+controlNames[6042]
			return
		elif ((controlID in [1000,-229, 452] and role==controlTypes.ROLE_LIST) or (controlID in [-240, -241, 453, 455] and role==controlTypes.ROLE_EDITABLETEXT) or (controlID in [1003, 1008] and role==controlTypes.ROLE_COMBOBOX) or (controlID in [-231, -232])):
			try:
				if controlID in [-231, -232]:
					obj.name=''
				else:
					obj.name=controlNames[obj.windowControlID]
			except KeyError:
				pass
		elif (role==controlTypes.ROLE_DROPLIST or ((role==controlTypes.ROLE_BUTTON or role==controlTypes.ROLE_EDITABLETEXT) and (400<=controlID<=413)) and self.isInEventsWindow()):
			try:
				if obj.role==controlTypes.ROLE_DROPLIST and obj.windowControlID<0 and obj.parent.parent.parent.windowClassName==u'#32770':
					if obj.simpleNext.role == controlTypes.ROLE_DROPLIST:
						obj.name=_('Start time')
					else:
						obj.name=_('Start date')
				elif obj.windowControlID in [400, 401, 402, 403, 404, 412, 413]:
					obj.name=controlNames[obj.windowControlID]
			except KeyError:
				pass

		elif obj.role==controlTypes.ROLE_LIST and obj.windowControlID==205:
			try:
				jinglesPage=obj.simplePrevious.simplePrevious.firstChild.firstChild
				obj.name=_("List of jingles %s page") %(jinglesPage.value)
			except:
				pass

	def script_activateJingles (self, gesture):
		if self.isInMainWindow():
			api.copyToClip ('entrou')
			focus = api.getFocusObject()
			gesture.send()
			focus.setFocus()
			fixFocus (focus)
		gesture.send()

	def getObject (self,t):
		fg=api.getForegroundObject()
		panel = t[0]
		ControlID=t[1]
		if not panel:
			obj=fg.firstChild.firstChild.firstChild.firstChild.firstChild
		elif panel == 1:
			obj=fg.firstChild.next.next.firstChild.firstChild.firstChild.firstChild
		elif panel == 2:
			obj=fg.firstChild.next.next.next.firstChild.firstChild.firstChild.firstChild
		elif panel == 3:
			obj=fg.firstChild.firstChild.firstChild.firstChild.firstChild.next.next.next.next.next.next.next.next.next.firstChild.firstChild

		ret=None
		x=0
		while obj is not None and ret==None:
			try:
				if obj.windowControlID==ControlID:
					ret=obj
				elif obj.firstChild.windowControlID==ControlID:
					ret=obj.firstChild
				elif obj.firstChild.simpleNext==ControlID:
					ret=obj.firstChild.simpleNext
				elif obj.simpleNext.firstChild.windowControlID==ControlID:
					ret=obj.simpleNext.firstChild
				elif obj.simpleNext.firstChild.windowControlID==ControlID:
					ret=obj.simpleNext.firstChild

			except:
				pass
			x+=1
			if 0 < panel < 3:
				obj=obj.simpleNext
			else:
				obj=obj.next

		return ret

	def isInMainWindow (self):
		try:
			role=api.getFocusObject().role
			controlID=api.getFocusObject().windowControlID
			return ((controlID in [1000,-229] and (role==controlTypes.ROLE_LIST or role==controlTypes.ROLE_LISTITEM)) or (controlID in [-240, -241] and role==controlTypes.ROLE_EDITABLETEXT) or (controlID==1001 and role==controlTypes.ROLE_SLIDER) or (controlID in [1003, 1008] and role==controlTypes.ROLE_COMBOBOX) or (controlID==1004))
		except:
			return False

	def isInEventsWindow (self):
		try:
			return (api.getForegroundObject().firstChild.next.windowControlID==415)
		except:
			return False

	def isInJinglesWindow (self):
		ancestor =winUser.getAncestor(api.getFocusObject().windowHandle, 2)
		return isJinglesDialog(ancestor)

	def isInAuxiliarPlayer(self):
		focus = api.getFocusObject()
		if not focus: return False
		obj = focus
		for x in range(3):
			if self.isPlayerDialog(obj):
				return True
			if not obj.parent: break
			obj = obj.parent
		return (focus.windowControlID==6042 and focus.windowClassName == u"SysListView32") or (focus.windowControlID == 6048 and focus.windowClassName == u'msctls_trackbar32')

	def isInFindInFoldersWindow (self):
		fg=api.getForegroundObject()
		if not fg or fg.windowClassName != u'#32770':
			return False
		h_452 = ctypes.windll.user32.GetDlgItem(fg.windowHandle, 452)
		h_453 = ctypes.windll.user32.GetDlgItem(fg.windowHandle, 453)
		return (h_452 != 0 and h_453 != 0)

	def event_valueChange(self, obj, nextHandler):
		if self.isInAuxiliarPlayer():
			nextHandler()
			return

		global previousFocus

		if obj.windowControlID in [-246, -247, 1007]:
			return
		elif obj.windowControlID==650:
			speech.pauseSpeech(0.5)
			fixFocus (previousFocus)
			return

		nextHandler()

	def event_stateChange (self,obj, nextHandler):
		global previousFocus
		if obj.windowControlID in range (-223, -214) and obj.windowClassName == u'ToolbarWindow32':
			if obj.IAccessibleStates == 16:
				import time
				time.sleep(0.15)
				speech.cancelSpeech()
				fixFocus (previousFocus)
				speech.speechMode = 0
			else:
				speech.speechMode = 2
			return

		if obj.windowControlID==-209:
			aux=NVDAObjects.IAccessible.getNVDAObjectFromEvent(obj.parent.windowHandle,-4,19)
			for x in range(4):
				if obj==aux:
						l=self.getActivesAuxs()
						for h in l:
							if obj.IAccessibleStates==16:
								o=NVDAObjects.IAccessible.getNVDAObjectFromEvent(h,-4,0)
								# o botão x da barra liga o player x+1; o título do player traz esse número
								if firstNumber(o.name) == str(x+1):
									fixFocus(o.firstChild)
							elif api.getFocusObject().windowControlID==6042:
								index=len(l)-1
								if winUser.getClassName(l[index])=='#32770':
									index-=1
								focus=NVDAObjects.IAccessible.getNVDAObjectFromEvent(l[index],0,-4)
								fixFocus(focus.firstChild)
							else:
								ui.message(_("%s disabled.") %obj.name)
						break
				aux=aux.next
			return
		nextHandler()

	def event_gainFocus(self, obj, nextHandler):
		if self.isInAuxiliarPlayer():
			global previousFocus
			previousFocus = obj
			nextHandler()
			return

		global mainWindow
		controlID=obj.windowControlID
		className=obj.windowClassName
		role=obj.role

		try:
			if controlID==1000:
				mainWindow=api.getForegroundObject()
			elif self.isInEventsWindow() and previousFocus.windowControlID==200:
						speech.speechMode=0
						obj=api.getForegroundObject().firstChild
						fixFocus(obj)
						speech.pauseSpeech(1.8)
						keyboardHandler.KeyboardInputGesture.fromName('tab').send()
						speech.speechMode=2
						previousFocus=obj
						return
			elif (role==14 and obj.firstChild.role==15) :
				speech.speakObjectProperties (obj, name=True, role=True)
				fixFocus (obj.firstChild)
				return
			if (obj.windowClassName in [u'#32770', u'wxWindowClassNR'] or obj.windowControlID== 650):
				if self.isPlayerDialog(obj):
					nextHandler()
					return
				fixFocus(previousFocus)
				return

		except:
			pass

		previousFocus=obj
		nextHandler()

	def script_focusPlayList(self,gesture):
		if not self.isInMainWindow():
			return
		playList=api.getForegroundObject().firstChild.firstChild.firstChild.firstChild.firstChild
		if api.getFocusObject().parent.parent==playList:
			return

		playList.setFocus()
		api.moveMouseToNVDAObject(playList)
		api.setMouseObject(playList)

	def previousWindow (self, obj):
		h=obj.windowHandle
		hPrevious=winUser.getWindow(h,3)
		return hPrevious

	def nextWindow ( self, obj):
		h=obj.windowHandle
		hNext=winUser.getWindow(h,2)
		return hNext

	def script_playModeCombo(self, gesture):
		if not self.isInMainWindow():
			return
		focus=getToolBar(tbPlayModeCombo)
		if focus is not None:
			fixFocus(focus)

	def script_tab(self, gesture):
		main=api.getForegroundObject()
		focus=api.getFocusObject()
		controlID = focus.windowControlID
		if controlID in [451, 453] and self.isInFindInFoldersWindow():
			fixFocus(focus.parent)
		elif controlID==1 and not winUser.isWindowEnabled(focus.windowHandle):
			fixFocus(main.firstChild.next)
			return
		elif self.isInMainWindow():
			if controlID == 1000:
				focus = self.getObj('SysListView32', -229)
				if focus: fixFocus(focus)
				else: gesture.send()
				return
			elif controlID == -229:
				focus = self.getObj('SysTreeView32', 1004)
				if focus: fixFocus(focus)
				else: gesture.send()
				return
			elif controlID == 1004:
				focus = self.getObj('SysListView32', 1000)
				if focus: fixFocus(focus)
				else: gesture.send()
				return
			elif controlID==1003:
				focus=self.getObj('Edit',-240)
				if focus: fixFocus(focus)
				else: gesture.send()
				return
			elif controlID==1008:
				focus=getToolBar (tbPlayModeCombo)
				if focus: fixFocus(focus)
				else: gesture.send()
				return
			elif controlID in [-241, 1001] and len(self.getActivesAuxs())>1 :
				if not winUser.isWindowEnabled(self.getObj('msctls_trackbar32',1001,0).windowHandle) or controlID==1001:
					fixFocus(api.getForegroundObject().firstChild.firstChild.firstChild.firstChild.firstChild)
				else:
					gesture.send()
				return
		elif self.isInAuxiliarPlayer():
			if controlID==6042 :
				return
		elif self.isInEventsWindow():
			next=self.nextWindow(focus)
			getControl=winUser.getControlID
			if focus.parent.windowClassName!= u'#32770' and 400<=getControl(next)<=413:
				focus=NVDAObjects.IAccessible.getNVDAObjectFromEvent(next,-4,0)
				o=oleacc.AccessibleObjectFromWindow(next,-4)
				o.accselect(1,0)
				api.setFocusObject(focus)
				focus.setFocus()
				api.moveMouseToNVDAObject(focus)
				api.setMouseObject(focus)
				return
		elif self.isInJinglesWindow():
				h=winUser.getAncestor(focus.windowHandle, 2)
				obj=NVDAObjects.IAccessible.getNVDAObjectFromEvent(h,-4,0)
				main=obj.firstChild
				if controlID==1001:
					focus=main.next.next.next.next
					fixFocus(focus)
					return

		gesture.send()

	def script_shiftTab(self, gesture):
		main=api.getForegroundObject()
		focus=api.getFocusObject()
		controlID = focus.windowControlID
		if controlID in [451, 453] and self.isInFindInFoldersWindow():
			fixFocus(focus.parent)
		elif controlID==1 and not winUser.isWindowEnabled(focus.windowHandle):
			fixFocus(main.firstChild.next)
			return

		if self.isInMainWindow():
			if controlID == 1004:
				focus = self.getObj('SysListView32', -229)
				if focus: fixFocus(focus)
				else: gesture.send()
				return
			elif controlID == -229:
				focus = self.getObj('SysListView32', 1000)
				if focus: fixFocus(focus)
				else: gesture.send()
				return
			elif controlID == 1000:
				if len(self.getActivesAuxs())>1:
					if winUser.isWindowEnabled(self.getObj('msctls_trackbar32',1001,0).windowHandle):
						h=api.getForegroundObject().firstChild.firstChild.firstChild.firstChild.windowHandle
						h=ctypes.windll.user32.FindWindowExW(h,0,'msctls_trackbar32', None)
						focus=NVDAObjects.IAccessible.getNVDAObjectFromEvent(h,-4,0)
					else:
						focus=self.getObject((0, -241))
					if focus: fixFocus(focus)
					else: gesture.send()
					return
				else:
					focus = self.getObj('SysTreeView32', 1004)
					if focus: fixFocus(focus)
					else: gesture.send()
					return
			elif controlID==-240:
				focus=getToolBar(3)
				if focus: fixFocus (focus)
				else: gesture.send()
				return
			elif controlID==1003:
				focus=main.lastChild.firstChild.firstChild.firstChild.lastChild
				if focus: fixFocus (focus)
				else: gesture.send()
				return
			elif controlID==1008:
				focus=main.firstChild.firstChild.firstChild.firstChild.firstChild.next.next.next.next.firstChild.firstChild.next
				if focus:
					api.setFocusObject(focus)
					focus.setFocus()
				else: gesture.send()
				return
			elif focus.parent.parent.parent.parent.simpleNext.windowControlID== 6042 and controlID!=1000:
				focus=api.getForegroundObject().firstChild.firstChild.firstChild.firstChild.firstChild
				if focus: fixFocus(focus)
				else: gesture.send()
				return
		elif controlID==6042:
			return
		elif self.isInEventsWindow():
			previous=self.previousWindow(focus)
			getControl=winUser.getControlID
			if focus.parent.windowClassName!= u'#32770' and 400<=getControl(previous)<=413 and controlID>0:
				focus=NVDAObjects.IAccessible.getNVDAObjectFromEvent(previous,-4,0)
				o=oleacc.AccessibleObjectFromWindow(previous,-4)
				o.accselect(1,0)
				api.setFocusObject(focus)
				focus.setFocus()
				api.moveMouseToNVDAObject(focus)
				api.setMouseObject(focus)
				return
			elif (400<=controlID<=413) and getControl(previous)<0 :
				focus=NVDAObjects.IAccessible.getNVDAObjectFromEvent(previous,-4,0)
				o=oleacc.AccessibleObjectFromWindow(previous,-4)
				o.accselect(1,0)
				api.setFocusObject(focus)
				focus.setFocus()
				api.moveMouseToNVDAObject(focus)
				api.setMouseObject(focus)
				return
		elif controlID==1001 and focus.role==controlTypes.ROLE_EDITABLETEXT:
			focus=focus.parent.parent.parent.parent.lastChild
			fixFocus(focus)
			return

		gesture.send()

	def getJinglesList (self):
		ret=[]
		obj = self.getObj ("Static", 89, 2)
		while str(obj.windowClassName)=="Static":
			ret.append (obj.name)
			obj= obj.simpleNext.simpleNext

	def getFindInFoldersWindowName (self):
		h = getToolBar (tbMain).windowHandle
		obj = NVDAObjects.IAccessible.getNVDAObjectFromEvent (h, -4, 10)
		return obj.name

	def script_temperature (self, gesture):
		# na árvore de pastas a letra vai para a busca do próprio ZaraRadio
		if not self.isInMainWindow () or api.getFocusObject().windowControlID == idTreeView:
			gesture.send()
			return
		obj = self.getObject ((3, 1022))

		if obj is None:
			return
		ui.message (obj.name)
		if scriptHandler.getLastScriptRepeatCount() == 1:
			speech.cancelSpeech()
			clickToolBarItem1 (obj.previous.location)

	def script_humidity (self, gesture):
		if not self.isInMainWindow () or api.getFocusObject().windowControlID == idTreeView:
			gesture.send()
			return
		obj = self.getObject ((3, 1023))
		if obj is None:
			return
		ui.message (obj.name)
		if scriptHandler.getLastScriptRepeatCount() == 1:
			speech.cancelSpeech()
			clickToolBarItem1 (obj.previous.location)

	def script_teste(self, gesture):
		global previousFocus
		getAncestor = winUser.getAncestor
		text = winUser.getWindowText
		gw=winUser.getWindow
		gc = winUser.getControlID
		cl = winUser.getClassName
		focus = api.getFocusObject()
		h = focus.windowHandle
		obj=api.getForegroundObject().firstChild.firstChild.firstChild.firstChild.firstChild.next.next.next.next.next.next.next.next.next.firstChild.firstChild.next.next.next.next
		ui.message (obj.windowClassName)
		ui.message(str(obj.windowControlID))
		ui.message (obj.name)

		focus = self.getObject((0, -232))
		if focus is not None:
			focus = focus.next.simpleFirstChild.simpleNext.simpleNext.simpleNext
			ui.message(str(focus.windowControlID))
			ui.message(focus.windowClassName)
			ui.message (focus.name)
			o = oleacc.AccessibleObjectFromWindow(focus.windowHandle, -4)
			ui.message (o.accname(2))
		if True:
			return

		if 256 in focus.states:
			fixFocus (focus.simpleFirstChild)
		elif index < total:
			fixFocus (next)
		elif nextParent:
			fixFocus (nextParent)
			fixFocus (nextParent)
		if True:
			return
		name = self.getFindInFoldersWindowName()
		h = ctypes.windll.user32.FindWindowExW (0, 0, u'#32770', self.getFindInFoldersWindowName())
		ui.message (str(h))
		if True:
			return
		h=1
		next = 0
		while h!=0:
			h = ctypes.windll.user32.FindWindowExW (0, next, u'#32770', None)
			ui.message(str(gc(gw(h,5))))
			if text(h) == (name):
				break
			next=h
		ui.message (str(h))
		if True:
			return
		focus=api.getFocusObject()
		parent=focus.parent
		h=parent.windowHandle

		while h!=0:
			try:
				ui.message(str(winUser.getControlID(h)))
				ui.message(str(winUser.getClassName(h)))
				if winUser.getControlID(h) in [-251,-252]:
					o=oleacc.AccessibleObjectFromWindow(h,-4)
					o=NVDAObjects.IAccessible.getNVDAObjectFromEvent(h,-4,1)
					while o is not None:
						ui.message(o.name)
						o=o.next
			except:
				pass
			h=winUser.getWindow(h,2)
		if True:
			return
		parent=self.getObject((0,60420))
		ui.message(str(parent.windowControlID))
		gw=winUser.getWindow
		h=winUser.getAncestor(focus.parent.parent.parent.parent.windowHandle,3)
		ui.message(str(parent.windowClassName))
		ui.message(str(focus.windowControlID))
		ui.message(str(parent.name))
		ui.message(str(parent.windowHandle))

	def script_times (self, gesture):
		if not self.isInMainWindow():
			gesture.send ()
			return

		remainingTime = self.getObj ('Static', -242, 0)
		remainingTimeLabel = remainingTime.simpleNext
		endTime = remainingTime.simpleNext.simpleNext
		endTimeLabel = remainingTime.simpleNext.simpleNext.simpleNext
		totalLength = self.getObj ('Static', 1005, 0)
		ui.message ("%s: %s" %(remainingTimeLabel.name, remainingTime.name))
		if scriptHandler.getLastScriptRepeatCount() == 1:
			ui.message ("%s: %s, %s" %(endTimeLabel.name, endTime.name, totalLength.name))

	def script_events(self, gesture):
		if not self.isInMainWindow():
			return
			
		ancestor = winUser.getAncestor(api.getFocusObject().windowHandle, 3)
		
		def _find_events_bar(parent_hwnd):
			h = ctypes.windll.user32.FindWindowExW(parent_hwnd, 0, None, None)
			while h != 0:
				cls = winUser.getClassName(h)
				cid = winUser.getControlID(h)
				if cls == u"ToolbarWindow32" and cid == -230:
					return h
				res = _find_events_bar(h)
				if res != 0:
					return res
				h = ctypes.windll.user32.FindWindowExW(parent_hwnd, h, None, None)
			return 0

		h = _find_events_bar(ancestor)
		
		if h == 0:
			ui.message(_("Barra de eventos não encontrada no NVDA."))
			return

		obj = NVDAObjects.IAccessible.getNVDAObjectFromEvent(h, -4, 1)
		tbList = []
		
		while obj is not None:
			try:
				if obj.role != controlTypes.ROLE_SEPARATOR and obj.IAccessibleStates != controlTypes.STATE_UNAVAILABLE:
					if obj.role != controlTypes.ROLE_CHECKBOX:
						name = obj.name
					else:
						if (obj.IAccessibleStates == controlTypes.STATE_CHECKED or obj.IAccessibleStates == 0):
							name = _("Activate events")
						else:
							name = _("Disable events")
					
					if name:
						tbList.append((name, obj.location))
				obj = obj.next
			except:
				break

		if len(tbList) > 0:
			showDialog(self, tbList, _("events"))
		else:
			ui.message(_("Barra encontrada, mas botões não puderam ser lidos."))

	def script_tracks(self, gesture):
		if not self.isInMainWindow():
			return
		obj=NVDAObjects.IAccessible.getNVDAObjectFromEvent(getToolBar(tbTracks).windowHandle,-4,1)
		tbList=[]
		while obj is not None:
			name=obj.name
			tbList.append ((name, obj.location, not (obj.IAccessibleStates==0 or obj.IAccessibleStates==128)))
			obj=obj.next
		showDialog (self, tbList,_("Tracks"), _('Mark the items you want to activate'))

	def script_pause(self, gesture):
		if self.isInAuxiliarPlayer():
			findControlID = api.getFocusObject().parent.parent.parent.windowControlID -2
			self.activateToolbarItemsInAuxPlayers(findControlID, 3)
			return
		elif self.isInMainWindow():
			h=getToolBar(tbMedia).windowHandle
			o=NVDAObjects.IAccessible.getNVDAObjectFromEvent(h,-4,3)
			clickToolBarItem1(o.location)
			return

		gesture.send()

	def script_cue(self, gesture):
		gesture.send()
		time.sleep(0.7)
		root_h = winUser.getAncestor(api.getForegroundObject().windowHandle, 3)
		h_child = 0
		found = False
		while True:
			h_child = ctypes.windll.user32.FindWindowExW(root_h, h_child, u'#32770', None)
			if h_child == 0: break
			if not winUser.isWindowVisible(h_child): continue
			
			if ctypes.windll.user32.GetDlgItem(h_child, 651) != 0 or ctypes.windll.user32.GetDlgItem(h_child, 652) != 0:
				obj = NVDAObjects.IAccessible.getNVDAObjectFromEvent(h_child, -4, 0)
				fixFocus(obj)
				if obj.firstChild: fixFocus(obj.firstChild)
				ui.message(_("Pré-escuta"))
				found = True
				break
		if not found:
			ui.message(_("Player não encontrado"))

	def script_playAux (self, gesture):
		focus = api.getFocusObject()
		if focus.windowClassName == u'#32770' or focus.parent.windowClassName == u'#32770':
			try:
				h=ctypes.windll.user32.FindWindowExW(focus.windowHandle, 0, u'ToolbarWindow32', None)
				if h == 0: h = ctypes.windll.user32.FindWindowExW(focus.parent.windowHandle, 0, u'ToolbarWindow32', None)
				o=NVDAObjects.IAccessible.getNVDAObjectFromEvent(h,-4,1)
				clickToolBarItem1(o.location)
				return
			except: pass
		
		findControlID = api.getFocusObject().parent.parent.parent.windowControlID -2
		if self.activateToolbarItemsInAuxPlayers(findControlID, 1):
			return
		gesture.send()

	def script_stopAux (self, gesture):
		focus = api.getFocusObject()
		if focus.windowClassName == u'#32770' or focus.parent.windowClassName == u'#32770':
			try:
				h=ctypes.windll.user32.FindWindowExW(focus.windowHandle, 0, u'ToolbarWindow32', None)
				if h == 0: h = ctypes.windll.user32.FindWindowExW(focus.parent.windowHandle, 0, u'ToolbarWindow32', None)
				o=NVDAObjects.IAccessible.getNVDAObjectFromEvent(h,-4,2)
				clickToolBarItem1(o.location)
				return
			except: pass

		findControlID = api.getFocusObject().parent.parent.parent.windowControlID -2
		if self.activateToolbarItemsInAuxPlayers(findControlID, 2):
			return
		gesture.send()

	def script_stopAfterCurrentAux (self, gesture):
		findControlID = api.getFocusObject().parent.parent.parent.windowControlID -2
		if self.activateToolbarItemsInAuxPlayers(findControlID, 9):
			return
		gesture.send()

	def script_nextAux (self, gesture):
		findControlID = api.getFocusObject().parent.parent.parent.windowControlID -2
		if self.activateToolbarItemsInAuxPlayers(findControlID, 5):
			return
		gesture.send()

	def script_addTrackAux(self, gesture):
		findControlID = api.getFocusObject().parent.parent.parent.windowControlID -1
		if self.activateToolbarItemsInAuxPlayers(findControlID, 6):
			return
		gesture.send()

	def activateToolbarItemsInAuxPlayers (self, controlID, item):
		if not self.isInAuxiliarPlayer():
			return False
		try:
			h=self.getObj('ToolbarWindow32', controlID,3).windowHandle
			o=NVDAObjects.IAccessible.getNVDAObjectFromEvent(h,-4,item)
			if o.IAccessibleStates!=1 and o.IAccessibleStates!=129:
				ui.message(o.name)
			clickToolBarItem1(o.location)
			return True
		except:
			return False

	def script_leftArrow(self, gesture):
		focus = api.getFocusObject()
		if focus and focus.windowControlID == 1004:
			if controlTypes.STATE_EXPANDED in focus.states:
				gesture.send()
				ui.message(controlTypes.stateLabels[controlTypes.STATE_COLLAPSED])
			else:
				gesture.send()
			return

		if self.isInAuxiliarPlayer():
			h_dlg = winUser.getAncestor(api.getFocusObject().windowHandle, 2)
			h_btn = ctypes.windll.user32.GetDlgItem(h_dlg, 652)
			if h_btn != 0:
				winUser.sendMessage(h_btn, 0x00F5, 0, 0)
			return
		if self.isInMainWindow():
			h = getToolBar(tbMedia).windowHandle
			o = NVDAObjects.IAccessible.getNVDAObjectFromEvent(h, -4, 6)
			try:
				o.doAction()
			except:
				clickToolBarItem1(o.location)
			return
		gesture.send()

	def script_rightArrow(self, gesture):
		focus = api.getFocusObject()
		if focus and focus.windowControlID == 1004:
			if controlTypes.STATE_COLLAPSED in focus.states:
				gesture.send()
				ui.message(controlTypes.stateLabels[controlTypes.STATE_EXPANDED])
			else:
				gesture.send()
			return

		if self.isInAuxiliarPlayer():
			h_dlg = winUser.getAncestor(api.getFocusObject().windowHandle, 2)
			h_btn = ctypes.windll.user32.GetDlgItem(h_dlg, 653)
			if h_btn != 0:
				winUser.sendMessage(h_btn, 0x00F5, 0, 0)
			return
		if self.isInMainWindow():
			h = getToolBar(tbMedia).windowHandle
			o = NVDAObjects.IAccessible.getNVDAObjectFromEvent(h, -4, 7)
			try:
				o.doAction()
			except:
				clickToolBarItem1(o.location)
			return
		gesture.send()

	def script_arrowAux(self, gesture):
		focus = api.getFocusObject()
		gesture.send()
		
		if focus.windowClassName == u'Edit' and focus.role == controlTypes.ROLE_EDITABLETEXT:
			def read_spin_value():
				val = api.getFocusObject().value
				if val:
					ui.message(str(val))
			wx.CallLater(100, read_spin_value)

		if self.isInAuxiliarPlayer():
			time.sleep(0.15)
			new_focus = api.getFocusObject()
			if new_focus and new_focus.windowControlID != 6042:
				h_dlg = winUser.getAncestor(focus.windowHandle, 2)
				h_list = ctypes.windll.user32.GetDlgItem(h_dlg, 6042)
				if h_list != 0:
					o = NVDAObjects.IAccessible.getNVDAObjectFromEvent(h_list, -4, 0)
					if o:
						fixFocus(o)

	def script_jinglesList(self, gesture):
		if not self.isInMainWindow():
			return
		l=[]
		jinglePage=self.getObject((2,1008))
		o=oleacc.AccessibleObjectFromWindow(jinglePage.windowHandle,-4)
		pageName=(str(o.accvalue(1)))
		for x in range (89,98):
			try:
				obj=self.getObject((2,x))
				l.append ('%s - %s' %(x-88,obj.name))

			except:
				pass
		if len (l)>0:
			msg = _('%d jingles of %s page: ')
			ui.message(msg %(len(l),pageName))
			for jingles in l:
				ui.message(jingles)
		else:
			ui.message(_('Jingles were not registered to page % s') %(pageName))

	def script_space(self, gesture):
		focus=api.getFocusObject()
		if self.isInEventsWindow() and focus.windowControlID==417:
			o = oleacc.AccessibleObjectFromWindow(focus.windowHandle,-4)
			o.accselect(2,0)
			return

		gesture.send()

	def script_sayActualTrack(self, gesture):
		if not self.isInMainWindow():
			return
		actualTrack = self.getObject((0,-240)).firstChild.value
		if actualTrack!='':
			ui.message(_('Current track: %s') %actualTrack)
		else:
			ui.message(_('There is no track playing'))

	def script_sayNextTrack(self, gesture):
		if not self.isInMainWindow():
			return
		nextTrack=self.getObject((0,-241)).firstChild.value
		if nextTrack!='':
			ui.message(_('Next track: %s') %nextTrack)
		else:
			ui.message(_('No next track'))

	def script_statusAux(self, gesture):
		if not self.isInMainWindow()and not self.isInAuxiliarPlayer ():
			return
		self.getStatusAux()

	def getActivesAuxs (self):
		global mainWindow

		gw=winUser.getWindow
		gc=winUser.getControlID
		findWindow=ctypes.windll.user32.FindWindowExW
		l=[]
		h=winUser.getAncestor(api.getForegroundObject().windowHandle,3)
		h=gw(gw(h,5),5)
		while h!=0:
			if winUser.isWindowVisible(h) and (gc(gw(h,5))==1000 or gc(gw(h,5))==6042 or gc(h)==0):
				l.append(h)
			h=gw(h,2)

		find=self.findFindInFoldersWindow()
		if find:
			l.append(find)
		return l

	def findFindInFoldersWindow (self):
		# procura a janela Encontrar em pastas pelos controles 452 e 453
		found = []
		pid = ctypes.c_ulong()
		getDlgItem = ctypes.windll.user32.GetDlgItem
		@ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
		def callback(h, lParam):
			ctypes.windll.user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
			if pid.value == self.processID and winUser.getClassName(h) == u'#32770' and getDlgItem(h, 452) != 0 and getDlgItem(h, 453) != 0:
				found.append(h)
				return False
			return True
		ctypes.windll.user32.EnumWindows(callback, 0)
		return found[0] if found else 0

	def getStatusAux(self, index=0):
		obj=oleacc.AccessibleObjectFromWindow(getToolBar(tbMain).windowHandle,-4)
		status={0:_("Disabled"),16:_('activated')}
		if index==0:
			for x in range(19,23):
				ui.message(obj.accname(x))
				ui.message(str(status[obj.accstate(x)]))
		else:
			return (obj.accstate(index+18)==16)

	def script_nextPlayList(self, gesture):
		l=self.getActivesAuxs()
		total=len(l)

		if total==1:
			return

		if api.getForegroundObject().windowClassName==u'#32770':
			h=winUser.getAncestor(api.getFocusObject().windowHandle,2)
			ctypes.windll.user32.ShowWindow(api.getForegroundObject().windowHandle,6)
			return
		else:
			obj=api.getFocusObject().parent.parent.parent
			h=obj.windowHandle
		try:
			index=l.index(h)
		except:
			index=0

		index=index+1-total*(index==total-1)
		h=l[index]
		obj=NVDAObjects.IAccessible.getNVDAObjectFromEvent(h,-4,0)
		if obj.windowClassName != '#32770':
			obj=obj.firstChild
			ctypes.windll.user32.ShowWindow(winUser.getAncestor(h,2),3)
		else:
			ctypes.windll.user32.ShowWindow(h,10)
			ui.message(winUser.getWindowText(h))

		fixFocus(obj)
		return

		gesture.send()

	def script_previousPlayList(self, gesture):
		l=self.getActivesAuxs()
		total=len(l)
		if total==1:
			return
		if api.getForegroundObject().windowClassName==u'#32770':
			obj=NVDAObjects.IAccessible.getNVDAObjectFromEvent(winUser.getAncestor(api.getFocusObject().windowHandle,2),-4,0)
		else:
			obj=api.getFocusObject().parent.parent.parent

		try:
			index=l.index(obj.windowHandle)
		except:
			index=0

		index=index-1+total*(index==0)
		fixFocus(obj)
		obj=NVDAObjects.IAccessible.getNVDAObjectFromEvent(l[index],-4,0)
		if obj.windowClassName!=u'#32770':
			obj=obj.firstChild
		else:
			ui.message(obj.name)
		fixFocus(obj)
		return

		gesture.send()

	def script_escape(self, gesture):
		if self.isInAuxiliarPlayer():
			fixFocus(api.getForegroundObject().firstChild.firstChild.firstChild.firstChild.firstChild)
			return
		if self.isInFindInFoldersWindow():
			winUser.sendMessage(api.getForegroundObject().windowHandle, 16, 0, 0)
			return

		gesture.send()

	def getObj (self, className, controlID, start=0):
		findWindow=ctypes.windll.user32.FindWindowExW
		gc=winUser.getControlID
		gw=winUser.getWindow
		s=gw(gw(api.getForegroundObject().windowHandle,5),5)
		if start==0:
			start=s
		elif start==1:
			start=findWindow(s,0,'wxWindowClassNR',None)
		elif start==2:
			start=api.getForegroundObject().windowHandle
			start=gw(gw(gw(start,5),1),5)
		elif start==3:
			start=api.getFocusObject().parent.parent.parent.windowHandle
		h=start
		hNext=0
		while h!=0 and gc(h)!=controlID:
			h=findWindow(start, hNext, className, None)
			if h!=0 and controlID==0:
				controlID=gc(h)
			elif h!=0 and gc(h)!=controlID:
				hNext=h

		if h==0:
			return None
		else:
			return NVDAObjects.IAccessible.getNVDAObjectFromEvent(h,-4,0)

	def script_applications (self, gesture):
		if api.getFocusObject().windowClassName==u'SysListView32' or api.getFocusObject().windowClassName == u"SysTreeView32":
			api.moveMouseToNVDAObject(api.getFocusObject())
			winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTDOWN,0,0,0,0)
			winUser.mouse_event (winUser.MOUSEEVENTF_RIGHTUP,0,0,0,0)
			return
		gesture.send()

	def script_changeVolume (self, gesture):
		if not self.isInMainWindow():
			gesture.send()
			return
		h = self.getObj ("msctls_trackbar32", 1001, 0).windowHandle
		if not h or not winUser.isWindowVisible (h):
			return
		sendMessage = winUser.sendMessage
		sendMessage (h, 0x100, 0x22 - (gesture.mainKeyName.lower() == "uparrow"), 0)
		if api.getFocusObject().windowHandle != h:
			volumeValue = NVDAObjects.IAccessible.getNVDAObjectFromEvent(h, -4,0).value
			ui.message(_("Volume - %s" %volumeValue))

	def script_changeJinglesPage (self, gesture):
		if not self.isInMainWindow():
			return
		h = self.getObj ("ComboBox", 1008, 2).windowHandle
		if h == 0:
			return
		sendMessage = winUser.sendMessage
		newIndex = int (gesture.mainKeyName) - 1
		if newIndex < 0:
			newIndex = 9
		selectedIndex = sendMessage (h, 0x147, 0, 0)
		if newIndex == selectedIndex:
			ui.message (_("Page %d of jingles is already selected") %(selectedIndex + 1))
			return

		sendMessage (h, 0x14E, newIndex, 0)
		sendMessage (h, 0x100, 0x28 - 2*(newIndex==9), 0)
		sendMessage (h, 0x100, 0x26 + 2*(newIndex==9), 0)
		ui.message (_('Page %d of jingles was selected') %(newIndex + 1))

	def script_activateAuxMenuToolBar (self, gesture):
		if self.isInAuxiliarPlayer ():
			keyName = "+".join(gesture.modifierNames)+"+"+gesture.mainKeyName
			toolbarItem = auxKeys[keyName]
			controlID = api.getFocusObject().parent.parent.parent.windowControlID -1
			if self.activateToolbarItemsInAuxPlayers(controlID, toolbarItem):
				return

		gesture.send()

	def script_copyPlaylist(self, gesture):
		focus = api.getFocusObject()
		if focus.windowControlID not in [1000, 6042] or focus.windowClassName != u'SysListView32':
			gesture.send()
			return
			
		gesture.send()
		ui.message(_("Copiado"))

	def script_cutPlaylist(self, gesture):
		focus = api.getFocusObject()
		if focus.windowControlID not in [1000, 6042] or focus.windowClassName != u'SysListView32':
			gesture.send()
			return
			
		keyboardHandler.KeyboardInputGesture.fromName("control+c").send()
		import time
		time.sleep(0.2)
		
		ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)
		ctypes.windll.user32.keybd_event(0xA2, 0, 2, 0)
		ctypes.windll.user32.keybd_event(0xA3, 0, 2, 0)
		
		keyboardHandler.KeyboardInputGesture.fromName("delete").send()
		time.sleep(0.1)
		
		fixFocus(focus)
		ui.message(_("Recortado"))

	__gestures = {
		"kb:control+p": "cue",
		"kb:Control+shift+l": "focusPlayList",
		"kb:Control+shift+x": "statusAux",
		"kb:Control+tab": "nextPlayList",
		"kb:Control+shift+tab": "previousPlayList",
		"kb:Escape": "escape",
		"kb:Control+m": "playModeCombo",
		"kb:Control+j": "sayActualTrack",
		"kb:Control+k": "sayNextTrack",
		"kb:tab": "tab",
		"kb:Shift+tab": "shiftTab",
		"kb:control+shift+t": "times",
		"kb:applications": "applications",
		"kb:control+shift+p": "pause",
		"kb:p": "playAux",
		"kb:s": "stopAux",
		"kb:b": "stopAfterCurrentAux",
		"kb:n": "nextAux",
		"kb:leftArrow": "leftArrow",
		"kb:rightArrow": "rightArrow",
		"kb:upArrow": "arrowAux",
		"kb:downArrow": "arrowAux",
		"kb:control+shift+v": "jinglesList",
		"kb:space": "space",
		"kb:f8": "events",
		"kb:f9": "tracks",
		"kb:alt+upArrow": "changeVolume",
		"kb:alt+downArrow": "changeVolume",
		"kb:control+shift+k": "teste",
		"kb:e": "temperature",
		"kb:u": "humidity",
		"kb:control+c": "copyPlaylist",
		"kb:control+x": "cutPlaylist",
		}

class Volume(IAccessible):
	def _get_value(self):
		return"%s%%" %(str(100 - int (super(Volume,self)._get_value())))

	def _get_name(self):
		return _("Volume")

	def script_volumeKeysChange (self, gesture):
		keyboardHandler.KeyboardInputGesture.fromName(self.__changeItemGestures[gesture.mainKeyName]).send()

	__changeItemGestures = {
		"leftArrow":"rightArrow",
		"rightArrow":"leftArrow",
		"upArrow":"downArrow",
		"downArrow":"upArrow",
		"home":"end",
		"end":"home",
		"pageUp":"pageDown",
		"pageDown":"pageUp",
		}

	def initOverlayClass(self):
		for gesture in self.__changeItemGestures.keys():
			self.bindGesture("kb:%s" %gesture, "volumeKeysChange")

class EnhancedRadioButton(IAccessible):
	def moveToEventType (self, direction):
		hFirstControl=winUser.user32.GetParent(self.windowHandle)
		hFirstControl=winUser.getWindow(hFirstControl,5)
		hLastControl=winUser.getWindow(hFirstControl,1)
		limits=[hLastControl, hFirstControl]
		h=self.windowHandle
		if h == limits[direction]:
			h=limits[not direction]
		else:
			findID=winUser.getControlID(h)-1+2*(direction==1)
			h=winUser.getWindow(h,direction+2)
			while h>0 and winUser.getControlID(h)!=findID :
				try:
					h=winUser.getWindow(h,(direction+2))
				except:
					h=0
		if h==0:
			return

		focus=NVDAObjects.IAccessible.getNVDAObjectFromEvent(h,4,0)
		o=oleacc.AccessibleObjectFromWindow(h,-4)
		o.accselect(2,0)
		o.accselect(1,0)
		api.setFocusObject(focus)
		focus.setFocus()
		api.moveMouseToNVDAObject(focus)
		api.setMouseObject(focus)

	def script_previous(self, gesture):
		controlID=self.windowControlID
		if controlID in range (415, 418):
			if controlID != 415:
				newFocus=self.simplePrevious
			else:
				keyboardHandler.KeyboardInputGesture.fromName('leftarrow').send()
				return

			obj=oleacc.AccessibleObjectFromWindow(newFocus.windowHandle,-4)
			api.setFocusObject(newFocus)
			newFocus.setFocus()
			obj.accselect(2,0)
			api.moveMouseToNVDAObject(newFocus)
			api.setMouseObject(newFocus)
			return
		elif self.parent.parent.windowClassName==u'wxWindowClassNR' and controlID<0:
			self.moveToEventType(1)
			return
		gesture.send()

	def script_next(self, gesture):
		controlID=self.windowControlID
		if controlID in range (415, 418):
			if controlID==417:
				newFocus=self.simplePrevious.simplePrevious
			elif controlID==416:
				keyboardHandler.KeyboardInputGesture.fromName('rightarrow').send()
				return
			else:
				newFocus=self.simpleNext

			obj=oleacc.AccessibleObjectFromWindow(newFocus.windowHandle,-4)
			obj.accselect(1,0)
			obj.accselect(2,0)
			newFocus.setFocus()
			api.moveMouseToNVDAObject(newFocus)
			api.setMouseObject(newFocus)
			return
		elif self.parent.parent.windowClassName==u'wxWindowClassNR' and controlID<0:
			self.moveToEventType(0)
			return
		gesture.send()

	__gestures = {
		"kb:leftArrow": "previous",
		"kb:downArrow": "previous",
		"kb:rightArrow": "next",
		"kb:upArrow": "next",}

class ToolBarListDialog(wx.Dialog):
	def __init__(self, parent, tbList, title, labelCaption = _('Choose an item to activate')):
		self.tbList = tbList
		self.states=[]
		if len(self.tbList[0])>2:
			self.states=([obj[2] for obj in self.tbList])
		super(ToolBarListDialog, self).__init__(parent, title=title)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		tasksSizer = wx.BoxSizer(wx.VERTICAL)
		tasksLabel = wx.StaticText(self, -1, label=labelCaption)
		tasksSizer.Add(tasksLabel)
		self.listBox = wx.ListCtrl(self, size=(550, 250),style=wx.LC_REPORT|wx.BORDER_SUNKEN)
		tasksSizer.Add(self.listBox, proportion=8)
		buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.okButton = wx.Button(self, wx.ID_OK)
		buttonsSizer.Add(self.okButton)
		cancelButton = wx.Button(self, wx.ID_CANCEL)
		buttonsSizer.Add(cancelButton)
		tasksSizer.Add(buttonsSizer)
		mainSizer.Add(tasksSizer)
		self.Bind(wx.EVT_BUTTON,self.onOk,id=wx.ID_OK)
		self.listBox.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)

	def onOk (self, evt):
		self.Hide()
		evt.Skip()
		import winUser
		try:
			if mainWindow!=api.getForegroundObject() and winUser.isWindowVisible(mainWindow.windowHandle):
				ctypes.windll.user32.ShowWindow(mainWindow.windowHandle,3)
				import time
				time.sleep (0.05)

			if len(self.states)==0:
				index=self.listBox.GetFocusedItem()
				clickToolBarItem1(self.tbList[index][1])
			else:
				for item in self.tbList:
					x=self.tbList.index(item)
					if self.states[x] != item[2]:
						clickToolBarItem1(item[1])
						import time
						time.sleep (0.1)
		except:
			pass

	def onKeyPress(self, event):
		keycode = event.GetKeyCode()
		if keycode==wx.WXK_RETURN:
			SendEvent(self.okButton,wx.EVT_BUTTON)
		elif keycode == wx.WXK_SPACE:
			if len(self.states)>0:
				index=self.listBox.GetFocusedItem()
				self.states[index] = not self.states[index]
				self.updateToolBar(self.tbList,index)
		event.Skip()

	def updateToolBar(self, tbList, index):
		self.tbList = tbList
		self.listBox.ClearAll()
		self.listBox.InsertColumn(0, 'Item')
		if len(self.states)==0:
			for item in self.tbList:
				self.listBox.Append ([item[0]])
		else:
			self.listBox.InsertColumn(1, 'Status')
			op=[_("not Checked"),_("Checked")]
			for x in self.tbList:
				self.listBox.Append ([x[0], op[self.states[self.tbList.index(x)]]])

		self.listBox.Focus(index)
		self.listBox.Select(index)

class ZaraSearchResultsItem(IAccessible):
	def script_copy(self, gesture):
		try:
			selectedItems = []
			if hasattr(self, 'parent') and self.parent:
				for child in self.parent.children:
					if controlTypes.STATE_SELECTED in child.states:
						selectedItems.append(child)
			
			if not selectedItems:
				selectedItems.append(self)
			
			filesToCopy = []
			
			for item in selectedItems:
				raw_text = item.name or ""
				
				if "; " in raw_text and ":\\" in raw_text:
					partes = raw_text.split("; ")
					nome_arquivo = partes[0].strip()
					pasta_str = partes[-1]
					
					idx = pasta_str.find(":\\")
					if idx != -1:
						pasta = pasta_str[idx - 1:].strip()
						if not pasta.endswith('\\'):
							pasta += '\\'
						
						caminho_final = pasta + nome_arquivo
						
						if os.path.exists(pasta):
							for f in os.listdir(pasta):
								if f.lower().startswith(nome_arquivo.lower()):
									caminho_final = pasta + f
									break
									
						if caminho_final:
							filesToCopy.append(caminho_final)
			
			if len(filesToCopy) > 0:
				texto_clipboard = "\r\n".join(filesToCopy)
				api.copyToClip(texto_clipboard)
				ui.message(_("%d copiado(s)") % len(filesToCopy))
				return
				
		except Exception as e:
			import logHandler
			logHandler.log.error("Erro no atalho de copia do ZaraRadio: %s" % str(e))
		
		ui.message(_("Erro ao copiar"))

	__gestures = {
		"kb:control+c": "copy",
	}