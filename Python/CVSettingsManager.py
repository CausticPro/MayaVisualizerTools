"""
Visualizer Viewport-vs-batch managing - Provides Presets for the Visualizer viewport, and
		easy tools for managing and sharing settings between the Caustic Visualizer viewport
		and the Visualizer Batch-Render settings.

Usage in a shelf button etc:

from CVSettingsManager import *
cvs = CVSettingsManager()
cvs.showUI()

# Known issues:
#     no dialog for new-preset name

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
from  CVToolUtil import *

class CVSettingsManager(CVToolUtil):

	DefaultBatchSettings = {
		"multiPassPasses": 10,
		"multiPassSamplesPerPixelPerPass": 1,
		"multiPassAdaptive": True,
		"multiPassAdaptiveThresholdPct": 0.20000000298,
		"rayDepthMinContributionPct": 0.5,
		"giMaxPrimaryRays": 2,
		"giEnableCaustics": False,
		"limitTextureDimensions": False,
		"maxFileTextureDimension": 2048,
		"maxIBLTextureDimension": 8192,
		"highlightMissingTextures": False,
		"iblBakePasses": 10,
		"iblBakeSamplesPerPixelPerPass": 1,
		"iblBakeResolution": 1024,
		"consoleMaxVerbosityLevel": 4,
		"printDebugMessages": False,
		"rendererEmulation": 0,
		"maxRayDepthReflect": 2,
		"maxRayDepthRefract": 4,
		"maxRayDepthGI": 1,
		"maxRayDepthTotal": 6,
		"giEnableDiffuse": False,
		# "giDiffuseMultiplier": [(1.0, 1.0, 1.0)],    # note that the componenets are also attributes, so this tuple's not needed
		"giDiffuseMultiplierR": 1.0,
		"giDiffuseMultiplierG": 1.0,
		"giDiffuseMultiplierB": 1.0,
		"imageFormat": 0,
		"exrCompression": 0,
		"exrDataType": 0,
		"gammaCorrection": 1.0,
		"clipFinalShadedColor": False,
		"imageFilterType": 1,
		"imageFilterMitNetB": 0.33333298564,
		"imageFilterMitNetC": 0.33333298564}
	DefaultViewportSettings = {
		"multiPassPasses": 10,
		"multiPassSamplesPerPixelPerPass": 1,
		"multiPassAdaptive": True,
		"multiPassAdaptiveThresholdPct": 0.20000000298,
		"rayDepthMinContributionPct": 0.5,
		"giMaxPrimaryRays": 2,
		"giEnableCaustics": False,
		"limitTextureDimensions": False,
		"maxFileTextureDimension": 2048,
		"maxIBLTextureDimension": 8192,
		"highlightMissingTextures": False,
		"iblBakePasses": 10,
		"iblBakeSamplesPerPixelPerPass": 1,
		"iblBakeResolution": 1024,
		"consoleMaxVerbosityLevel": 4,
		"printDebugMessages": False,
		"multiPassFirstPass": -2,
		"enableHighlighting": True,
		"enableDepthHoldout": True,
		"depthHoldoutBias": 0.019999999553,
		"modelingModeAOMaxRays": 8,
		"modelingModeAOLimitRadius": False,
		"modelingModeAOMaxRadius": 1.0,
		"modelingModeAOShowReversedNormals": False,
		# "modelingModeAOGoochColor1": [(1.0, 1.0, 0.20000000298023224)],
		"modelingModeAOGoochColor1R": 1.0,
		"modelingModeAOGoochColor1G": 1.0,
		"modelingModeAOGoochColor1B": 0.20000000298,
		# "modelingModeAOGoochColor2": [(0.0, 0.0, 0.6000000238418579)],
		"modelingModeAOGoochColor2R": 0.0,
		"modelingModeAOGoochColor2G": 0.0,
		"modelingModeAOGoochColor2B": 0.600000023842,
		"modelingModeAOGoochAzimuth": 45.0,
		"modelingModeAOGoochElevation": 45.0,
		# "modelingModeSLDiffuseColor": [(0.5, 0.5, 0.5)],
		"modelingModeSLDiffuseColorR": 0.5,
		"modelingModeSLDiffuseColorG": 0.5,
		"modelingModeSLDiffuseColorB": 0.5,
		"modelingModeSLSpecularOn": True,
		"modelingModeSLSpecularGloss": 0.600000023842,
		"modelingModeSLReflectOn": True,
		"modelingModeSLReflectivity": 0.0500000007451,
		"modelingModeSLLightAzimuth": 45.0,
		"modelingModeSLLightElevation": 45.0,
		# "modelingModeSLLightColor": [(1.0, 0.949999988079071, 0.8999999761581421)],
		"modelingModeSLLightColorR": 1.0,
		"modelingModeSLLightColorG": 0.949999988079,
		"modelingModeSLLightColorB": 0.899999976158,
		# "modelingModeSLAmbientColor": [(0.10000000149011612, 0.10000000149011612, 0.20000000298023224)],
		"modelingModeSLAmbientColorR": 0.10000000149,
		"modelingModeSLAmbientColorG": 0.10000000149,
		"modelingModeSLAmbientColorB": 0.20000000298,
		"showFPS": False,
		"forceMeshRebuild": True,
		"useAnimationHints": True,
		"multiPassEnable": True,
		"rayDepthMax": 8,
		"rayDepthReflect": 2,
		"rayDepthRefract": 6,
		"rayDepthGI": 1,
		"giEnableDiffuse": False,
		"giDiffuseMultiplier": 1.0}

	# ACTUAL METHODS BEGIN ###################################
	def __init__(self):
		super(CVSettingsManager,self).__init__()
		self.prList = None
		# self.nameWindow = None
		self.newName = None
		# self.newNameField = None
		CVSettingsManager.use = self

	# ########################

	def get_new_preset_name(self):
		"get default name"
		defName = "CVViewPreset%d"%(len(self.get_viewport_presets()))
		self.newName = None
		n = maya.cmds.promptDialog(title='New Caustic Viewport Preset',text=defName,message='Alphanumeric Preset Name:',button=['OK','Cancel'],defaultButton='OK',cancelButton='Cancel',dismissString='Cancel')
		if n == 'OK':
			self.newName = maya.cmds.promptDialog(query=True,text=True)
		#self.presetNameWin(defName)
		return self.newName

	def selected_preset_name(self):
		nItems = maya.cmds.textScrollList(self.prList,query=True,nsi=True)
		if nItems < 1:
			self.statusMsg('No preset selected --\nplease select from the list')
			return None
		items = self.get_viewport_presets()
		if len(items)<1:
			print "no actual items exist.... these are dummies"
			self.statusMsg('The displayed names are dummy entries.\nPlease create at least one actual preset.')
			return None
		# other = maya.cmds.textScrollList(self.prList,query=True,ai=True)
		sn = maya.cmds.textScrollList(self.prList,query=True,sii=True)[0]
		print sn
		print items
		iName = items[sn-1]
		return iName

	def get_viewport_presets(self):
		# first make sure the viewport settings node exists... hmm: if can't find or create, return [] or None?
		self.force_viewport_settings_node()
		n = maya.cmds.ls('CausticVisualizerSettings')
		if len(n)<1:
			return []
		return maya.cmds.nodePreset(list='CausticVisualizerSettings')


	def new_preset(self,Name):
		"might disappear, uses the preset object above rather than maya's"
		if not self.presets.has_key(Name):
			self.presets.Name = ViewPreset(Name)
		self.presets[Name].grab_from_maya()

	# need remove preset, rename preset, UI components for selection and push/pull of presets...

	def grab_from_batch(self):
		"match the viewport settings to the current batch render settings"
		ct = 0
		for a in CVSettingsManager.DefaultViewportSettings.keys():
			if maya.cmds.attributeQuery(a,node='CausticVisualizerBatchSettings',exists=True):  # does the batch node have the same attribute?
				bv = maya.cmds.getAttr('CausticVisualizerBatchSettings.%s'%(a))
				if a == 'giDiffuseMultiplier': # HACKKK! this returns a list of one tuple. we will convert to grayscale
					bv = bv[0][0]*.29 + bv[0][1]*0.6 + bv[0][2]*0.11
				try:
					maya.cmds.setAttr('CausticVisualizerSettings.%s'%(a),bv)
					ct += 1
				except:
					print 'Error copying "%s" to "%s"'%(bv,a)
		return ct

	def push_to_batch(self):
		"push here means match the batch settings to the viewport render settings"
		ct = 0
		for a in CVSettingsManager.DefaultViewportSettings.keys():
			if maya.cmds.attributeQuery(a,node='CausticVisualizerBatchSettings',exists=True):  # does the batch node have the same attribute?
				vv = maya.cmds.getAttr('CausticVisualizerSettings.%s'%(a))
				if a == 'giDiffuseMultiplier': # HACKKK
					maya.cmds.setAttr('CausticVisualizerBatchSettings.%sR'%(a),vv)
					maya.cmds.setAttr('CausticVisualizerBatchSettings.%sG'%(a),vv)
					maya.cmds.setAttr('CausticVisualizerBatchSettings.%sB'%(a),vv)
					ct += 1
				else:
					try:
						maya.cmds.setAttr('CausticVisualizerBatchSettings.%s'%(a),vv)
						ct += 1
					except:
						print 'Error copying "%s" (%s) to "%s"'%(vv,type(vv),a)
		return ct

	# preset-name window #############################################

	def nameOkayHandler(self, *args):
		"NOT currently called"
		name = maya.cmds.textField(self.newNameField,query=True,text=True)
		okay = maya.cmds.nodePreset(query=True,isValidName=name)
		if okay:
			self.newName = name
		else:
			print 'Invalid preset name "%s"'%(name)
			self.statusMsg('Invalid preset name "%s"'%(name))
		maya.cmds.deleteUI(self.nameWindow)
		self.newNameField = None
		self.nameWindow = None

	def nameCancelHandler(self, *args):
		"NOT currently called"
		maya.cmds.deleteUI(self.nameWindow)
		self.newNameField = None
		self.nameWIndow = None

	def presetNameWin_someday(self,StartName="cv_preset"):
		"this should be a modal dialog but layoutDialog is a PITA so: NOT currently called, we use promptDialog() instead"
		if self.nameWindow:
			if maya.cmds.window(self.nameWindow,exists=True):
				maya.cmds.deleteUI(self.nameWindow,window=True)
		self.nameWindow = maya.cmds.window(menuBar=False,sizeable=False,title='New Preset Name')
		vert = maya.cmds.columnLayout(p=self.nameWindow,rs=16,cal='center',adj=True)
		self.visHeader(DispTitle="Name New Preset",Parent=vert)
		self.newNameField = maya.cmds.textField(p=vert)
		botCol = maya.cmds.rowLayout(nc=3,parent=vert,ct2=['left','right'],co2=[4,4],adjustableColumn=2)
                if self.appVersion > 2013:
                  maya.cmds.iconTextButton(p=botCol,label='Help',st='textOnly',flat=True,bgc=[.4,.4,.3],width=100,command=CVSettingsManager.use.helpHandler,annotation='Get help from the Caustic website')
                  maya.cmds.iconTextButton(p=botCol,label='Okay',st='textOnly',flat=True,bgc=[.3,.4,.3],width=100,command=CVSettingsManager.use.nameOkayHandler,annotation='Close this window')
                  maya.cmds.iconTextButton(p=botCol,label='Cancel',st='textOnly',flat=True,bgc=[.4,.3,.3],width=100,command=CVSettingsManager.use.nameCancelHandler,annotation='Close this window')
                else:
                  maya.cmds.iconTextButton(p=botCol,label='Help',st='textOnly',bgc=[.4,.4,.3],width=100,command=CVSettingsManager.use.helpHandler,annotation='Get help from the Caustic website')
                  maya.cmds.iconTextButton(p=botCol,label='Okay',st='textOnly',bgc=[.3,.4,.3],width=100,command=CVSettingsManager.use.nameOkayHandler,annotation='Close this window')
                  maya.cmds.iconTextButton(p=botCol,label='Cancel',st='textOnly',bgc=[.4,.3,.3],width=100,command=CVSettingsManager.use.nameCancelHandler,annotation='Close this window')
		maya.cmds.showWindow(self.nameWindow)

	# button handlers for main window #################

	def helpHandler(self, *args):
		"specific text"
		helpText = """The Render Settings Manager
unifies and simplifies the two different usages of Caustic
Visualizer rendering: the interactive viewport and the final
batch render. Maya's UI keeps these settings far apart, which
can make managing them awkward -- this manager helps you by
providing shortcuts to key settings, common actions, and
a means to quickly copy, save, and restore
viewport rendering presets."""
		self.showHelpWindow(Message=helpText,DispTitle='Render Settings Manager Help',WinTitle="Settings Mgr Help")

	def newHandler(self, *args):
		"create new viewport preset"
		# we will need to create a dialog box for this....
		if not self.force_viewport_settings_node():
			self.statusMsg('Unable to determine new preset name')
			return # fail
		self.get_new_preset_name()
		if not self.newName:	# dialog may return None
			self.statusMsg('No name for new preset')
			return	# do nothing
		maya.cmds.nodePreset(save=('CausticVisualizerSettings',self.newName))
		self.updateUI(self.newName)
		self.statusMsg('Preset "%s" added.'%(self.newName))

	def replaceHandler(self, *args): # should I have a selectcommand?
		"replace the selected preset"
		preName = self.selected_preset_name()
		if not preName:
			return
		maya.cmds.nodePreset(save=('CausticVisualizerSettings',preName))
		self.updateUI()
		self.statusMsg('Preset "%s" replaced.'%(preName))

	def deleteHandler(self, *args): # should I have a selectcommand?
		"replace the selected preset"
		preName = self.selected_preset_name()
		if not preName:
			return
		maya.cmds.nodePreset(delete=('CausticVisualizerSettings',preName))
		self.updateUI()
		self.statusMsg('Preset "%s" deleted.'%(preName))

	def preferHandler(self, *args): # should I have a selectcommand?
		"assign the selected preset as the 'preferred' one -- this is NOT currently called"
		preName = self.selected_preset_name()
		if not preName:
			return
		maya.cmds.nodePreset(exists=('CausticVisualizerSettings',preName))
		self.statusMsg('Preset "%s" marked as preferred.'%(preName))

	def loadHandler(self, *args): # should I have a selectcommand?
		"load the selected preset"
		preName = self.selected_preset_name()
		if not preName:
			return
		maya.cmds.nodePreset(load=('CausticVisualizerSettings',preName))
		self.statusMsg('Preset "%s" loaded.'%(preName))

	def b2vHandler(self, *args):
		"copy batch settings to viewport"
		self.force_viewport_settings_node()
		self.force_batch_settings_node()
		c = self.grab_from_batch()
		self.statusMsg('%d Batch Render settings copied\nto Caustic Viewport settings'%(c))
		
	def v2bHandler(self, *args):
		"copy vewport settings to batch renderer"
		self.force_viewport_settings_node()
		self.force_batch_settings_node()
		c = self.push_to_batch()
		self.statusMsg('%d Caustic Viewport attributes copied\nto Batch Render settings'%(c))

	def visWinHandler(self, *args):
		"display the visualizer settings window"
		try:
			maya.mel.eval("CausticVisualizerOptionBox;")
		except:
			print "unable to display caustic render settings window, it may not have been initialized -- try opening it ONCE by hand..."
			self.statusMsg('Unable to open Caustic Viewport Settings Window,\ntry by hand?')

	def batWinHandler(self, *args):
		"display the render settings window"
		try:
			maya.mel.eval("unifiedRenderGlobalsWindow;")
		except:
			print "unable to display render settings window, it may not have been initialized -- try opening it ONCE by hand..."
			self.statusMsg('Unable to open Maya Render Settings Window,\ntry by hand?')

	# ########## main window ############

	def updateUI(self,SelName=None):
		super(CVSettingsManager,self).updateUI()
		if not self.prList:
			print "why no prList?"
			return
		presetList = self.get_viewport_presets()
		if len(presetList)<1:
			presetList += ['default','fast_color','fastest','pretty_but_slow']
		maya.cmds.textScrollList(self.prList,edit=True,removeAll=True)
		maya.cmds.textScrollList(self.prList,edit=True,append=presetList)

	def showUI(self):
		self.startUI(DispTitle="Render Settings Manager",WinTitle="Render Settings Mgr",WinName="SetMgr")
		#
		prFrame = maya.cmds.frameLayout('pre',label='Caustic Visualizer Viewport Presets',parent=self.vertLyt)
		prCol = maya.cmds.rowLayout(parent=prFrame,nc=3,ct2=['left','right'],co2=[4,4],adjustableColumn=2)
		presetList = self.get_viewport_presets()
		if len(presetList)<1:
			presetList += ['default','fast_color','fastest','pretty_but_slow']
		self.prList = maya.cmds.textScrollList(parent=prCol,ams=False,append=presetList,width=120,height=160,dcc=CVSettingsManager.use.loadHandler,dkc=CVSettingsManager.use.deleteHandler) # preset list goes here
		maya.cmds.text(parent=prCol,label=' ') # dummy
		pbV = maya.cmds.columnLayout(parent=prCol,rs=8,co=["both",2],adjustableColumn=True)
		longWid = 10+8*len('Preferred Default')
                if self.appVersion > 2013:
                  maya.cmds.iconTextButton(p=pbV,label='New Preset',st='textOnly',flat=True,bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.newHandler,annotation='New preset from current viewport settings')
                  maya.cmds.iconTextButton(p=pbV,label='Replace Preset',st='textOnly',flat=True,bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.replaceHandler,annotation='Replace the selected preset with the current viewport settings')
                  maya.cmds.iconTextButton(p=pbV,label='Delete Preset',st='textOnly',flat=True,bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.deleteHandler,annotation='Delete the selected preset')
                else:
                  maya.cmds.iconTextButton(p=pbV,label='New Preset',st='textOnly',bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.newHandler,annotation='New preset from current viewport settings')
                  maya.cmds.iconTextButton(p=pbV,label='Replace Preset',st='textOnly',bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.replaceHandler,annotation='Replace the selected preset with the current viewport settings')
                  maya.cmds.iconTextButton(p=pbV,label='Delete Preset',st='textOnly',bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.deleteHandler,annotation='Delete the selected preset')
		#maya.cmds.separator(style='singleDash')
		#maya.cmds.iconTextButton(p=pbV,label='Preferred Default',st='textOnly',bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.preferHandler,annotation='Set the selected preset as the default preference',enable=False)
		#
		longWid = 10+6*len('Show Viewport Settings')
		cpFrame = maya.cmds.frameLayout('cp',label='WYSIWYG: Batch Render Settings',parent=self.vertLyt)
		cpCol = maya.cmds.rowLayout(nc=3,parent=cpFrame,adjustableColumn=2)
		#longWid = 20+10*len('Batch->View')
                if self.appVersion > 2013:
                  maya.cmds.iconTextButton(p=cpCol,label='Copy View -> Batch',st='textOnly',flat=True,bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.v2bHandler,annotation='Copy the current Viewport settings for use in Batch Rendering')
                  maya.cmds.text(label=' ') # dummy
                  maya.cmds.iconTextButton(p=cpCol,label='Copy Batch -> View',st='textOnly',flat=True,bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.b2vHandler,annotation='Copy the current batch rendering settings into the viewport settings')
                else:
                  maya.cmds.iconTextButton(p=cpCol,label='Copy View -> Batch',st='textOnly',bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.v2bHandler,annotation='Copy the current Viewport settings for use in Batch Rendering')
                  maya.cmds.text(label=' ') # dummy
                  maya.cmds.iconTextButton(p=cpCol,label='Copy Batch -> View',st='textOnly',bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.b2vHandler,annotation='Copy the current batch rendering settings into the viewport settings')
		#
		shoFrame = maya.cmds.frameLayout('sh',label='Show Settings Dialog Windows',parent=self.vertLyt)
		shoCol = maya.cmds.rowLayout(nc=3,parent=shoFrame,adjustableColumn=2)
                if self.appVersion > 2013:
                  maya.cmds.iconTextButton(p=shoCol,label='Show Viewport Settings',st='textOnly',flat=True,bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.visWinHandler,annotation='Reveal Caustic Visualizer Viewport Settings')
                  maya.cmds.text(label=' ') # dummy
                  maya.cmds.iconTextButton(p=shoCol,label='Show Batch Settings',st='textOnly',flat=True,bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.batWinHandler,annotation='Reveal Maya Render Settings Window')
                else:
                  maya.cmds.iconTextButton(p=shoCol,label='Show Viewport Settings',st='textOnly',bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.visWinHandler,annotation='Reveal Caustic Visualizer Viewport Settings')
                  maya.cmds.text(label=' ') # dummy
                  maya.cmds.iconTextButton(p=shoCol,label='Show Batch Settings',st='textOnly',bgc=[.4,.4,.4],width=longWid,command=CVSettingsManager.use.batWinHandler,annotation='Reveal Maya Render Settings Window')
		#
		self.statusLine(Label='Welcome to the Caustic Visualizer for Maya\nRender Settings Manager')
		self.helpCloseFooter()
		maya.cmds.showWindow(self.window)


# ########################### eof ###
