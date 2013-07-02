"""
Visualizer Tools Common Windowing Elements for consistent UX and look


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
import maya
import re
# import unittest2

class CVToolUtil(object):
	use = None
	logoFile = None

	# ACTUAL METHODS BEGIN ###################################
	def __init__(self,HelpURL="https://www.caustic.com/visualizer/maya/"):
		self.window = None
		self.helpWindow = None
		self.vertLyt = None
		self.statusText = None
                self.appVersion = maya.mel.eval('getApplicationVersionAsFloat();')
		CVToolUtil.use = self
		self.helpURL = HelpURL
		if not CVToolUtil.logoFile:
			CVToolUtil.logoFile = self.findCausticLogo()

	# UI bits
	def findCausticLogo(self,Logo='CausticVisualizerLogo.png'):
		"track down the logo file -- may be in different places depending on the version of Maya being used"
		ml = maya.cmds.pluginInfo('CausticVisualizer.mll',query=True,path=True)
		ml = os.path.normpath(ml)
		ml = os.path.split(os.path.split(ml)[0])[0]
		logoFile = os.path.join(ml,'icons',Logo)
		if not os.path.exists(logoFile):
		 	print 'cannot find "%s"'%(logoFile)
		 	return None
		# print 'Found logo "%s"'%(logoFile)
		logoFile = re.sub(r'\\','/',logoFile) # Qt likes forwward slash
		return logoFile

	def showHelpWindow(self,Message="Help text should go here.",DispTitle="Generic CV Help",WinTitle="CVToolUtil Help"):
		"bring up help window, and print to screen too"
		print Message
		if self.helpWindow:
			if maya.cmds.window(self.helpWindow,exists=True):
				maya.cmds.deleteUI(self.helpWindow,window=True)
		self.helpWindow = maya.cmds.window(menuBar=False,sizeable=False,title=WinTitle)
		vert = maya.cmds.columnLayout(p=self.helpWindow,rs=16,cal='center',adj=True)
		tops = maya.cmds.rowLayout(p=vert,nc=2,bgc=[0,0,0],co2=[5,20])
		visBtn = maya.cmds.iconTextButton('Visualizer',image=CVToolUtil.logoFile,p=tops,command=CVToolUtil.use.webHandler)
		title = maya.cmds.text('title',p=tops,label=DispTitle,font='boldLabelFont',width=30+10*len(DispTitle))
		maya.cmds.setParent('..')
		maya.cmds.text(p=vert,label=Message,wordWrap=True)
                if self.appVersion > 2013:
                  okayBtn = maya.cmds.iconTextButton(p=vert,label='Got It',st='textOnly',width=260,flat=True,bgc=[.45,.2,.2],mw=10,font='boldLabelFont',command=CVToolUtil.use.helpOkHandler)
                else:
                  okayBtn = maya.cmds.iconTextButton(p=vert,label='Got It',st='textOnly',width=260,bgc=[.45,.2,.2],mw=10,font='boldLabelFont',command=CVToolUtil.use.helpOkHandler)
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

	# ##########

	def updateUI(self,SelName=None):
		if not self.window:
			print "cannot update when there is no window"
			return
		if not maya.cmds.window(self.window,exists=True):
			print "cannot update if the window has been closed"
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
			print Text


	def helpCloseFooter(self,Parent=None):
		"help and close buttons -- no others, no OKAY etc"
		par = Parent
		if not par:
			par = self.vertLyt
		botCol = maya.cmds.rowLayout(nc=3,parent=par,ct2=['left','right'],co2=[4,4],adjustableColumn=2)
                if self.appVersion > 2013:
                  maya.cmds.iconTextButton(p=botCol,label='Help',st='textOnly',flat=True,bgc=[.4,.4,.3],width=120,command=CVToolUtil.use.helpHandler,annotation='Get help from the Caustic website')
                  maya.cmds.text(label=' ') # dummy
                  maya.cmds.iconTextButton(p=botCol,label='Close',st='textOnly',flat=True,bgc=[.4,.3,.3],width=120,command=CVToolUtil.use.closeHandler,annotation='Close this window')
                else:
                  maya.cmds.iconTextButton(p=botCol,label='Help',st='textOnly',bgc=[.4,.4,.3],width=120,command=CVToolUtil.use.helpHandler,annotation='Get help from the Caustic website')
                  maya.cmds.text(label=' ') # dummy
                  maya.cmds.iconTextButton(p=botCol,label='Close',st='textOnly',bgc=[.4,.3,.3],width=120,command=CVToolUtil.use.closeHandler,annotation='Close this window')

	def startUI(self,DispTitle="Generic Window",WinTitle="CV Win",WinName="CVW"):
		if self.window:
			if maya.cmds.window(self.window,exists=True):
				maya.cmds.deleteUI(self.window,window=True)
		# ignore 'WinName'
		self.window = maya.cmds.window(menuBar=False,sizeable=False,title=WinTitle)
		self.vertLyt = maya.cmds.columnLayout(p=self.window,rs=6,cal='center',adj=True,cat=['both',0],co=['both',0])
		self.visHeader(DispTitle=DispTitle)

# ########################### eof ###
