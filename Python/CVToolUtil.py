"""
Visualizer Tools: Common Management & Windowing Elements for consistent UX and look


# TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THIS SOFTWARE IS PROVIDED
# *AS IS* AND IMAGINATION TECHNOLOGIES AND ITS SUPPLIERS DISCLAIM ALL WARRANTIES, EITHER
# EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS FOR A PARTICULAR PURPOSE.  IN NO EVENT SHALL IMAGINATION TECHNOLOGIES OR ITS
# SUPPLIERS BE LIABLE FOR ANY SPECIAL, INCIDENTAL, INDIRECT, OR CONSEQUENTIAL DAMAGES
# WHATSOEVER (INCLUDING, WITHOUT LIMITATION, DAMAGES FOR LOSS OF BUSINESS PROFITS,
# BUSINESS INTERRUPTION, LOSS OF BUSINESS INFORMATION, OR ANY OTHER PECUNIARY
# LOSS) ARISING OUT OF THE USE OF OR INABILITY TO USE THIS SOFTWARE, EVEN IF
# IMAGINATION TECHNOLOGIES HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

"""

import sys
import os
import maya.cmds
import maya.mel
import maya
import re
import unittest
# this little trick enables us to run unittests in mayapy.exe..
try:
  import maya.standalone
  maya.standalone.initialize()
except:
  pass

def _safely_seek_appVersion():
	"when running mayapy mel.eval() is not defined"
	v = 2014.0
	try:
		v = maya.mel.eval('getApplicationVersionAsFloat();')
	except:
		pass
	return v

def safely_log_event(Category='CVToolUtil',Action='Log',Label=None,Value=None):
	"If the user has opted out of reporting, nothing will happen"
	if Label is None and Value is None:
		try:
			maya.cmds.CausticVisualizerSendStatsEvent(Category,Action)
		except:
			pass
		return
	v=0
	try:
		v = int(max(v,Value))
	except:
		pass
	try:
		maya.cmds.CausticVisualizerSendStatsEvent(Category,Action,Label,v)
	except:
		pass

def maya_print(msg):
	"print, but only when running Maya -- not in mayapy testing"
	if not 'mayapy' in sys.executable:
		print msg

# ###################################

class CVTButton(object):
	"""
	A replacement for Maya's button control.
	It uses a "flat" look via iconTextButton, and makes the call correctly according to version of Maya.
	"""
	appVersion = None
	def __init__(self,Parent=None,Label='Label',Col=[.3,.3,.3],Width=120,Height=30,Cmd=None,Anno="Tooltip",Font='plainLabelFont'):
		"A generic button gives these scripts a consistent look"
		cmd = Cmd
		if cmd is None:
			print "assigning dummy callback to '%s' button" % (Label)
			cmd = self.defaultHandler
		self.btn = None
		if CVTButton.appVersion is None:
			CVTButton.appVersion = _safely_seek_appVersion()
		if CVTButton.appVersion > 2013:
			self.btn = maya.cmds.iconTextButton(p=Parent,label=Label,st='textOnly',flat=True,bgc=Col,width=Width,height=Height,command=cmd,annotation=Anno,font=Font)
		else:
			self.btn = maya.cmds.iconTextButton(p=Parent,label=Label,st='textOnly',bgc=Col,width=Width,height=Height,command=cmd,annotation=Anno,font=Font)

	def defaultHandler(self, *args):
		"use this when you don't know what to do"
		print "CVTButton"

	def enable(self,Value=True):
		maya.cmds.iconTextButton(self.btn,edit=True,enable=Value)


# ############################################

class CVTCheckBox(CVTButton):
	"""
	A replacement for Maya's checkbox control, based on CVTButton. Instead of a checked icon,
	   this checkbox changes color and label to indicate its state, and only has one simpler "Cmd" callback.
	"""
	def __init__(self,Parent=None,Label='Label',OffLabel=None,OffCol=[.3,.3,.3],OnCol=[.6,.5,.3],Width=120,Height=30,Cmd=None,Anno="Tooltip",Value=False):
		"A generic check button gives these scripts a consistent look"
		super(CVTCheckBox,self).__init__(Parent=Parent,Label=Label,Col=OffCol,Width=Width,Height=Height,Cmd=Cmd,Anno=Anno)
		self.value = Value #boolean
		self.onLabel = Label
		self.offLabel = OffLabel
		self.onCol = OnCol
		self.offCol = OffCol
		self.update()
	def update(self):
		"set color according to state"
		cl = self.onCol if self.value else self.offCol
		lb = self.onLabel
		if self.offLabel and not self.value:
			lb = self.offLabel
		maya.cmds.iconTextButton(self.btn,edit=True,bgc=cl,label=lb)
	def set(self,Value=None):
		if Value is None:
			self.value = not self.value
		else:
			self.value = Value
		self.update()
	def defaultHandler(self, *args):
		self.set() # toggles & updates

# ###############################

class CVToolUtil(object):
	"""
	A generic tool window class (and related helpwindow) for Caustic Visualizer-related tools.
	This class provides some common operations when dealing with Visualizer queries and UI issues.
	Note the "use" class property, that lets us create control items with a known-at-root scope (which Maya needs),
	and the "logoFile" item which tracks down the Caustic logo (regardless of where the installer has
		placed it, depending on your version of Maya)
	"""
	use = None
	logoFile = None

	# ACTUAL METHODS BEGIN ###################################
	def __init__(self,HelpURL="https://www.caustic.com/visualizer/maya/"):
		self.window = None
		self.helpWindow = None
		self.vertLyt = None
		self.statusText = None
		self.appVersion = _safely_seek_appVersion()
		CVToolUtil.use = self
		self.helpURL = HelpURL
		if not CVToolUtil.logoFile:
			CVToolUtil.logoFile = self.findCausticLogo()

	# UI bits
	def findCausticLogo(self,Logo='CausticVisualizerLogo.png'):
		"track down the logo file -- may be in different places depending on the version of Maya being used"
		try:
			ml = maya.cmds.pluginInfo('CausticVisualizer.mll',query=True,path=True)
		except:
			maya_print("Caution: Caustic Visualizer is not installed!")
			return None
		ml = os.path.normpath(ml)
		ml = os.path.split(os.path.split(ml)[0])[0]
		logoFile = os.path.join(ml,'icons',Logo)
		if not os.path.exists(logoFile):
		 	print 'Caution: cannot find logo file "%s"'%(logoFile)
		 	return None
		# print 'Found logo "%s"'%(logoFile)
		logoFile = re.sub(r'\\','/',logoFile) # Qt likes forwward slash
		return logoFile

	def showHelpWindow(self,Message="Help text should go here.",DispTitle="Generic CV Help",WinTitle="CVToolUtil Help",ToolCat='CVTool'):
		"bring up help window, and print to screen too"
		print Message
		safely_log_event(ToolCat,'Help',DispTitle)
		if self.helpWindow:
			if maya.cmds.window(self.helpWindow,exists=True):
				maya.cmds.deleteUI(self.helpWindow,window=True)
		self.helpWindow = maya.cmds.window(menuBar=False,sizeable=False,title=WinTitle)
		vert = maya.cmds.columnLayout(p=self.helpWindow,rs=16,cal='center',adj=True)
		tops = maya.cmds.rowLayout(p=vert,nc=2,bgc=[0,0,0],co2=[5,20])
		if CVToolUtil.logoFile:
			visBtn = maya.cmds.iconTextButton('Visualizer',image=CVToolUtil.logoFile,p=tops,command=CVToolUtil.use.webHandler)
		else:
			visBtn = maya.cmds.iconTextButton('Visualizer',st='textOnly',label='Visualizer for Maya',font='smallPlainLabelFont',p=tops,command=CVToolUtil.use.webHandler)
		title = maya.cmds.text('title',p=tops,label=DispTitle,font='boldLabelFont',width=30+10*len(DispTitle))
		maya.cmds.setParent('..')
		maya.cmds.text(p=vert,label=Message,wordWrap=True)
		okayBtn = CVTButton(Parent=vert,Label='Got It',Width=260,Col=[.45,.2,.2],Font='boldLabelFont',Cmd=CVToolUtil.use.helpOkHandler)
		maya.cmds.showWindow(self.helpWindow)

	# button handlers
	def helpHandler(self, *args):
		"override this with parameters for helpWindow()"
		self.showHelpWindow()

	def helpOkHandler(self, *args):
		print "Happy to be of service!"
		maya.cmds.deleteUI(self.helpWindow)
		self.helpWindow = None

	def webHandler(self, *args):
		"show caustic web site or any other value for self.helpURL"
		maya.cmds.launch(web=self.helpURL)

	def closeHandler(self, *args):
		"close window, erase pointers to controls"
		maya.cmds.deleteUI(self.window)
		self.statusText = None
		self.vertLyt = None
		self.window = None

	def dummyHandler(self, *args):
		"use this when you don't know what to do"
		print "click"

	# ##########

	def updateUI(self,SelName=None):
		if not self.window:
			maya_print("cannot update when there is no window")
			return
		if not maya.cmds.window(self.window,exists=True):
			maya_print("cannot update if the window has been closed")
			return

	def visHeader(self,DispTitle="wha?",Parent=None):
		"standardized Caustic Visualizer header"
		par = Parent
		if not par:
			par = self.vertLyt
		tops = maya.cmds.rowLayout(p=par,nc=2,bgc=[0,0,0],co2=[5,20])
		visBtn = maya.cmds.iconTextButton('Visualizer',image=CVToolUtil.logoFile,p=tops,command=CVToolUtil.use.webHandler,annotation='Caustic Web Site')
		title = maya.cmds.text('title',p=tops,label=DispTitle,font='boldLabelFont',width=20+8*len(DispTitle))

	def statusLine(self,Label='Welcome to the Caustic Visualizer for Maya\nStatus Text Item',Parent=None):
		par = Parent
		if not par:
			par = self.vertLyt
		self.statusText = maya.cmds.text(p=par,label=Label)

	def statusMsg(self,Text="Status Text Should Go\nIn This Space"):
		if self.statusText:
			maya.cmds.text(self.statusText,edit=True,label=Text)
		else:
			print 'Status: %s' % (Text)

	def helpCloseFooter(self,Parent=None):
		"help and close buttons -- no others, no OKAY etc"
		par = Parent
		if not par:
			par = self.vertLyt
		botCol = maya.cmds.rowLayout(nc=3,parent=par,ct2=['left','right'],co2=[4,4],adjustableColumn=2)
		CVTButton(Parent=botCol,Label='Help',Col=[.4,.4,.3],Cmd=CVToolUtil.use.helpHandler,Anno='Get help from the Caustic website')
		#maya.cmds.text(p=botCol,label=' ') # dummy
		maya.cmds.separator(p=botCol,style='none')
		CVTButton(Parent=botCol,Label='Close',Col=[.4,.3,.3],Cmd=CVToolUtil.use.closeHandler,Anno='Close this window')

	def startUI(self,DispTitle="Generic Window",WinTitle="CV Win",WinName="CVW",ToolCat='CVTool',ToolAction='Start'):
		if self.window:
			if maya.cmds.window(self.window,exists=True):
				maya.cmds.deleteUI(self.window,window=True)
		# ignore 'WinName'
		safely_log_event(ToolCat,ToolAction,DispTitle)
		self.window = maya.cmds.window(menuBar=False,sizeable=False,title=WinTitle)
		self.vertLyt = maya.cmds.columnLayout(p=self.window,rs=6,cal='center',adj=True,cat=['both',0],co=['both',0])
		self.visHeader(DispTitle=DispTitle)

	def force_cv_node(self,Name='Error'):
		if len(maya.cmds.ls(Name)) < 1:
			n = maya.cmds.createNode(Name,name=Name,shared=True,skipSelect=True)
			if n != Name:
				print "force_cv_node(): Cannot create '%s' node!"%(Name)
				return False
		return True

	def force_viewport_settings_node(self):
		return self.force_cv_node('CausticVisualizerSettings')

	def force_batch_settings_node(self):
		return self.force_cv_node('CausticVisualizerBatchSettings')

# ###################################

class TestTools(unittest.TestCase):
  """
  Unit-Test Class
  """
  def setUp(self):
    self.tool = CVToolUtil()
  def test_hasVers(self):
    "see if we got that far"
    self.assertTrue(self.tool.appVersion is not None) 
  def test_hasHelp(self):
    "see if we got that far"
    self.assertTrue(self.tool.helpURL is not None) 

# #############################################################

# launched from maya as:
#  maya -command "python(\"execfile('Concierge.py')\")"

if __name__ == "__main__":
	print "Running CVToolUtil Unit Tests"
	unittest.main()

# ########################### eof ###
