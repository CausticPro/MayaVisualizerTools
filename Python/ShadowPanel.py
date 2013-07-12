"""
An editing panel for shadows

Usage in a shelf button etc:

from ShadowPanel import *
ShadowPanel()

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

# TO-DO 
# spot penumbra coneangle dropoff
# shadowColor for all
# ambi ambientShade
#
# master dimmer: before updating intensity sliders check their ranges against the desired value!
# meters
# new light/duplicate?
# add IBL



import sys
import os
import maya
import re
import math
from  CVToolUtil import *

class DecayButton(CVTButton):
	rateNames = ["No Decay","Linear","Quadratic","Cubic"]
	rateColors = [[0.2,0.2,0.2], [.4,.3,.3], [.2,.3,.2], [.2,.3,.45]]
	def __init__(self,Parent=None,Width=54,Cmd=None):
		"A generic check button gives these scripts a consistent look"
		super(DecayButton,self).__init__(Parent=Parent,Width=Width,Cmd=Cmd,Anno='Distance Falloff')
		self.rate = 0
		self.update()
	def set(self,Rate):
		self.rate = Rate
		if self.rate >= 4:
			self.rate = 0
		return self.rate
	def update(self):
		maya.cmds.iconTextButton(self.btn,edit=True,label=DecayButton.rateNames[self.rate],bgc=DecayButton.rateColors[self.rate])
	
# ############################

class Lamp(object):
	"class for UI sub-panels"
	def __init__(self,ShapeNode,LampType):
		"create based on the specified maya shape or xform node"
		self.shape = ShapeNode
		self.xform = None
		self.master = None
		if len(maya.cmds.ls(ShapeNode)) < 1:
			self.shape = None # FAIL: no such node
			return
		if maya.cmds.nodeType(ShapeNode) == 'transform': # oops
			self.xform = ShapeNode
			kids = maya.cmds.listRelatives(ShapeNode,children=True)
			if len(kids)<1: # fail NO KIDS
				self.shape = None
				return
			self.shape = kids[0]
		if len(maya.cmds.ls(ShapeNode,lights=True)) < 1:
			self.shape = None # FAIL: not a light node
			return
		if self.xform is None:
			self.xform = maya.cmds.listRelatives(self.shape,parent=True)[0]
		self.lampType = LampType
		self.flush_controls()

	def select(self):
		maya.cmds.select(self.xform)
		#if self.xform is not None:
		#	prev = maya.cmds.ls(sl=True)
		#	lp = len(prev)
		#	if lp > 0 or (lp > 1 and prev[0] != self.xform):
		#		maya.cmds.select(self.xform)

	def selectHandler(self, *args):
		# print 'selectHandler'
		# self.select()
		maya.cmds.select(self.xform)

	def toggle_btn(self,Parent=None,Label="Xxx",Col=[.3,.3,.4]):
		btn = CVTCheckBox(Parent=Parent,Label=Label,OffCol=Col)
		return btn

	def attr(self,Attr):
		if self.shape is None:
			return None
		full = '%s.%s'%(self.shape,Attr)
		try:
			return maya.cmds.getAttr(full)
		except:
			print 'Unable to fetch "%s"'%(full)
			return None

	def setAttr(self,Attr,Value):
		if self.shape is None:
			return False
		full = '%s.%s'%(self.shape,Attr)
		try:
			maya.cmds.setAttr(full,Value)
		except:
			print 'Unable to assign (%s) to "%s"'%(Value,full)
			return False
		return True

	def useShadow(self):
		if self.lampType == 'ambientLight':
			return False
		s = self.attr('useRayTraceShadows')
		if maya.cmds.attributeQuery('useDepthMapShadows',node=self.shape,exists=True):
			s = s or self.attr('useDepthMapShadows')
		return s

	def setShadow(self,Value):
		s = self.setAttr('useRayTraceShadows',Value)
		if maya.cmds.attributeQuery('useDepthMapShadows',node=self.shape,exists=True):
			self.setAttr('useDepthMapShadows',False) # unify it!
	
	def shadowHandler(self, *args):
		self.shadow.defaultHandler()
		self.setShadow(self.shadow.value)
		self.select()
		self.set_abilities()
	def eDiffHandler(self, *args):
		self.diffuse.defaultHandler()
		self.setAttr('emitDiffuse',self.diffuse.value)
		self.select()
	def eSpecHandler(self, *args):
		self.specular.defaultHandler()
		self.setAttr('emitSpecular',self.specular.value)
		self.select()
	def colorHandler(self, *args):
		c = maya.cmds.colorSliderGrp(self.color,query=True,rgb=True)
		maya.cmds.setAttr(self.shape+'.color',c[0],c[1],c[2],type='double3')
		self.select()
	def shadColorHandler(self, *args):
		c = maya.cmds.colorSliderGrp(self.shadColor,query=True,rgb=True)
		maya.cmds.setAttr(self.shape+'.shadowColor',c[0],c[1],c[2],type='double3')
		self.select()

	def lightRadHandler(self, *args):
		if self.lightRad:
			existing = self.attr("lightRadius")
			rad = maya.cmds.floatSliderGrp(self.lightRad,query=True,value=True)
			if rad != existing:
				self.setAttr("lightRadius",rad)
				self.select()
	def lightAngHandler(self, *args):
		if self.lightAng:
			existing = self.attr("lightAngle")
			rad = maya.cmds.floatSliderGrp(self.lightAng,query=True,value=True)
			if rad != existing:
				self.setAttr("lightAngle",rad)
				self.select()
	def shadRadHandler(self, *args):
		if self.shadRad:
			existing = self.attr("shadowRadius")
			rad = maya.cmds.floatSliderGrp(self.shadRad,query=True,value=True)
			if rad != existing:
				self.setAttr("shadowRadius",rad)
				self.select()
	def ambShadeHandler(self, *args):
		if self.shadRad:
			existing = self.attr("ambientShade")
			rad = maya.cmds.floatSliderGrp(self.shadRad,query=True,value=True)
			if rad != existing:
				self.setAttr("ambientShade",rad)
				self.select()
	def coneHandler(self, *args):
		if self.cone:
			existing = self.attr("coneAngle")
			rad = maya.cmds.floatSliderGrp(self.cone,query=True,value=True)
			if rad != existing:
				self.setAttr("coneAngle",rad)
				self.select()
	def penHandler(self, *args):
		if self.penumbra:
			existing = self.attr("penumbraAngle")
			rad = maya.cmds.floatSliderGrp(self.penumbra,query=True,value=True)
			if rad != existing:
				self.setAttr("penumbraAngle",rad)
				self.select()
	def dropHandler(self, *args):
		if self.dropoff:
			existing = self.attr("dropoff")
			rad = maya.cmds.floatSliderGrp(self.dropoff,query=True,value=True)
			if rad != existing:
				self.setAttr("dropoff",rad)
				self.select()

	def decayHandler(self):
		dRate = self.decay.set(self.attr("decayRate") + 1)
		self.decay.update()
		self.setAttr("decayRate",dRate)
		self.select()

	def intensityHandler(self, *args):
		self.update_intensity()
		self.select()
	def intensitySlideHandler(self, *args):
		self.update_intensity(FixRange=False)
		self.select()

	def update_intensity(self,FixRange=True):
		"also called when dimmer changes"
		b = self.calculate_maya_intensity()
		if FixRange:
			self.max_intensity(b)
		self.setAttr("intensity",b)

	def calculate_maya_intensity(self):
		"determine the appropriate intensity to pass to maya - use metering and other master flags"
		# TO-DO: if the user has altered the brightnesses with the AE the values from self.intensity will be wrong.
		# perhaps they should be checked before the dimmer is changed?
		v = 0.0
		if self.intensity:
			v = maya.cmds.floatSliderGrp(self.intensity,query=True,value=True)
		else:
			v = self.attr("intensity")
		v *= self.master.dimmerVal
		# print "%s maya intensity: %g" % (self.xform,v)
		return v

	def max_intensity(self,InBright):
		"determine if we need to extend the range of the intensity slider"
		existing = 10.0
		if self.lampType == 'directionalLight' or self.lampType == 'ambientLight':
			existing = 2.0
		if self.intensity:
			existing = maya.cmds.floatSliderGrp(self.intensity,query=True,value=True)
		if existing >= InBright:
			return existing
		newTop = math.pow(10,1.0+math.floor(math.log(InBright)/math.log(10)))
		if self.intensity:
			maya.cmds.floatSliderGrp(self.intensity,edit=True,max=newTop)
		return newTop

	def set_abilities(self):
		"enable or disable controls based on the current state of the lamp"
		if self.shadow:
			shadowed = self.useShadow()
			self.shadow.update()
			maya.cmds.intFieldGrp(self.shadRays,edit=True,enable=shadowed)
			maya.cmds.intFieldGrp(self.depthLimit,edit=True,enable=shadowed)
			if self.shadRad:
				maya.cmds.floatSliderGrp(self.shadRad,edit=True,enable=shadowed)
			if self.lightRad:
				maya.cmds.floatSliderGrp(self.lightRad,edit=True,enable=shadowed)
			if self.lightAng:
				maya.cmds.floatSliderGrp(self.lightAng,edit=True,enable=shadowed)
		if self.color:
			r = self.attr('colorR')
			g = self.attr('colorG')
			b = self.attr('colorB')
			maya.cmds.colorSliderGrp(self.color,edit=True,rgb=[r,g,b])
		if self.shadColor:
			rgb = self.attr('shadowColor')[0]
			try:
				maya.cmds.colorSliderGrp(self.shadColor,edit=True,rgb=rgb)
			except:
				print self.shape
		if self.decay:
			self.decay.set(self.attr("decayRate"))
			self.decay.update()

	def flush_controls(self):
		self.panel = None
		self.selectMe = None # button
		self.shadow = None # toggle UI
		self.diffuse = None
		self.specular = None
		self.decay = None # 4x something
		self.intensity  = None # this is the text UI for the intensity - may be disabled by attachments 
		self.color = None # will be swatch tool - may be disabled by attachments
		self.cone = None
		self.penumbra = None
		self.dropoff = None
		self.shadColor = None
		self.shadRad = None
		self.lightRad = None
		self.lightAng = None
		self.ambShade = None
		self.shadRays = None
		self.depthLimit = None
		self.ibl = None

	def init_ui(self,Parent=None,Master=None):
		"""
		TO-DO: IBL "colorGain"
		mia_physicalsky1 "multiplier"
		"""
		if not self.shape:
			return
		# temporarily....
		if self.lampType == 'mentalrayIblShape' or self.lampType == 'mia_physicalsky':
			return
		# print '%s %s'%(self.xform,Parent)
		self.master = Master
		self.flush_controls()
		self.panel = maya.cmds.columnLayout(p=Parent)
		toggles = maya.cmds.rowLayout('togs',p=self.panel,nc=6,adjustableColumn=2)
		self.selectMe = CVTButton(Parent=toggles,Label=self.xform,Col=[.4,.4,.7],Cmd=self.selectHandler,Font='boldLabelFont',Anno='Select %s'%(self.xform))
		# maya.cmds.iconTextButton(self.selectMe.btn,edit=True,align='left')
		maya.cmds.text(p=toggles,label=' ')
		if self.lampType != 'ambientLight':
			self.shadow = CVTCheckBox(Parent=toggles,Label="Shadow",OffLabel='Unshadowed',Width=80,OffCol=[.6,.6,.6],Value=self.useShadow(),Cmd=self.shadowHandler,Anno='Toggle Shadowing')
		else:
			self.shadow = None
		if maya.cmds.attributeQuery('emitDiffuse',node=self.shape,exists=True): # ambi lights do not have these
			self.diffuse = CVTCheckBox(Parent=toggles,Label="Diff",OffLabel='NoDiff',Width=40,Value=self.attr('emitDiffuse'),Cmd=self.eDiffHandler,Anno='Emit Diffuse Light?')
			self.specular = CVTCheckBox(Parent=toggles,Label="Spec",Width=40,OffLabel='NoSpec',Value=self.attr('emitSpecular'),Cmd=self.eSpecHandler,Anno='Emit Specular Light?')
			if self.lampType != 'directionalLight':
				self.decay = DecayButton(Parent=toggles,Cmd=self.decayHandler)
			else:
				maya.cmds.text(p=toggles,label=' ')
		else:
			maya.cmds.text(p=toggles,label=' ')
			maya.cmds.text(p=toggles,label=' ')
			maya.cmds.text(p=toggles,label=' ') # no decay either
		cons = maya.cmds.listConnections(self.shape+".intensity")
		if cons is None:
			b = self.calculate_maya_intensity()
			mi = self.max_intensity(b)
			self.intensity = maya.cmds.floatSliderGrp(p=self.panel,label='Intensity',field=True,value=b,max=mi,cw=[1,120],cc=self.intensityHandler,dc=self.intensitySlideHandler,annotation='local intensity')
		cons = maya.cmds.listConnections(self.shape+".intensity")
		if cons is None:
			if self.lampType == 'ambientLight':
				self.color = maya.cmds.colorSliderGrp(p=self.panel,label='Color',cw=[1,120],cc=self.colorHandler,dc=self.colorHandler,annotation='ambient color')
			else:
				crow = maya.cmds.rowLayout('crow',p=self.panel,nc=3,adjustableColumn=2)
				self.color = maya.cmds.colorSliderGrp(p=crow,label='Color',cw3=[60,60,60],cc=self.colorHandler,dc=self.colorHandler,annotation='lamp color')
				maya.cmds.text(p=crow,label=' ')
				self.shadColor = maya.cmds.colorSliderGrp(p=crow,label='Shadow',cw3=[60,30,60],cc=self.shadColorHandler,dc=self.shadColorHandler,annotation='lamp shadow color')
		if self.lampType == 'spotLight':
			v = self.attr('coneAngle')
			self.cone = maya.cmds.floatSliderGrp(p=self.panel,label='Cone Angle',field=True,value=v,max=180.0,cw=[1,120],cc=self.coneHandler,dc=self.coneHandler,annotation='cone angle')
			v = self.attr('penumbraAngle')
			self.penumbra = maya.cmds.floatSliderGrp(p=self.panel,label='Penumbra',field=True,value=v,min=-10,max=10.0,cw=[1,120],cc=self.penHandler,dc=self.penHandler,annotation='pensumbrar spread angle')
			v = self.attr('dropoff')
			self.dropoff = maya.cmds.floatSliderGrp(p=self.panel,label='DropOff',field=True,value=v,max=255.0,cw=[1,120],cc=self.dropHandler,dc=self.dropHandler,annotation='dropoff against the center of the spotlight')
		if maya.cmds.attributeQuery('shadowRadius',node=self.shape,exists=True) and self.lampType != 'ambientLight':
			v = self.attr('shadowRadius')
			maxR = max(8.0,v)
			self.shadRad = maya.cmds.floatSliderGrp(p=self.panel,label='Shadow Radius',field=True,value=v,max=maxR,cw=[1,120],cc=self.shadRadHandler,dc=self.shadRadHandler)
		if maya.cmds.attributeQuery('lightRadius',node=self.shape,exists=True) and self.lampType != 'directionalLight':
			v = self.attr('lightRadius')
			maxR = max(8.0,v)
			self.lightRad = maya.cmds.floatSliderGrp(p=self.panel,label='Light Radius',field=True,value=v,max=maxR,cw=[1,120],cc=self.lightRadHandler,dc=self.lightRadHandler,annotation='effective size of the lamp')
		if maya.cmds.attributeQuery('lightAngle',node=self.shape,exists=True):
			v = self.attr('lightAngle')
			maxA = max(20.0,v)
			self.lightAng = maya.cmds.floatSliderGrp(p=self.panel,label='Light Angle',field=True,value=v,max=maxA,cw=[1,120],cc=self.lightAngHandler,dc=self.lightAngHandler,annotation='spread angle for shadow rays')
		if maya.cmds.attributeQuery('ambientShade',node=self.shape,exists=True):
			v = self.attr('ambientShade')
			self.ambShade = maya.cmds.floatSliderGrp(p=self.panel,label='Ambient Shade',field=True,value=v,max=1.0,cw=[1,120],cc=self.ambShadeHandler,dc=self.ambShadeHandler,annotation='angular falloff of ambient tone')
		if self.shadow:
			rays = maya.cmds.rowLayout('rays',p=self.panel,nc=3,adjustableColumn=2)
			self.shadRays = maya.cmds.intFieldGrp(p=rays,label="Shadow Rays",cw=[1,80],v1=self.attr('shadowRays'),annotation='shadow ray count')
			self.depthLimit = maya.cmds.intFieldGrp(p=rays,label="Ray Depth Limit",cw=[1,80],v1=self.attr('rayDepth'),annotation='max ray depth for shadows')
		self.set_abilities()


# MAIN WINDOW CLASS #############################

class ShadowPanelUI(CVToolUtil):
	def __init__(self):
		super(ShadowPanelUI,self).__init__()
		ShadowPanelUI.use = self
		self.dimmerVal = 1.0
		self.dimmer = None # UI
		self.metered = None # UI
		self.meterPick = None
		self.lamps = self.build_lamp_list()

	def build_lamp_list(self):
		"""
		Builds the lamp list, but does not yet populate the UI.
		Doesn't look to see if this light is actually shadowed
		"""
		lampList = []
		mayaLamps = maya.cmds.ls(lights=True,sl=True) + maya.cmds.ls('mentalRayIblShape1',sl=True) + maya.cmds.ls('mia_physicalsky1',sl=True)
		if len(mayaLamps) < 1:
			mayaLamps = maya.cmds.ls(lights=True) + maya.cmds.ls('mentalRayIblShape1') + maya.cmds.ls('mia_physicalsky1')
		if len(mayaLamps) < 1:
			return lampList
		for lType in ['areaLight','directionalLight','spotLight','pointLight','ambientLight','mentalrayIblShape','mia_physicalsky']: # no 'volumeLight'
			for lamp in mayaLamps:
				t = maya.cmds.nodeType(lamp)
				if t == lType:
					lampList.append(Lamp(lamp,t))
		return lampList

	def refreshHandler(self, *args):
		self.build_lamp_list()
		self.showUI()

	def helpCloseFooter(self,Parent=None):
		"help and close buttons + refresh"
		par = Parent
		if not par:
			par = self.vertLyt
		botCol = maya.cmds.rowLayout(nc=3,parent=par,ct2=['left','right'],co2=[4,4],adjustableColumn=2)
		CVTButton(Parent=botCol,Label='Help',Col=[.4,.4,.3],Cmd=CVToolUtil.use.helpHandler,Anno='Get help from the Caustic website')
		CVTButton(Parent=botCol,Label='Refresh',Col=[.3,.3,.4],Cmd=ShadowPanelUI.use.refreshHandler,Anno='Refresh this window')
		CVTButton(Parent=botCol,Label='Close',Col=[.4,.3,.3],Cmd=CVToolUtil.use.closeHandler,Anno='Close this window')

	def dimmerHandler(self, *args):
		self.dimmerVal = maya.cmds.floatSliderGrp(self.dimmer,query=True,value=True)
		for a in self.lamps:
			a.update_intensity()

	def showUI(self):
		if ShadowPanelUI.use and ShadowPanelUI.use.window:
			try:
				maya.cmds.deleteUI(ShadowPanelUI.use.window)
				ShadowPanelUI.use.statusText = None
				ShadowPanelUI.use.vertLyt = None
				ShadowPanelUI.use.window = None
			except:
				print "no old window"
		maya.cmds.setAttr('defaultRenderQuality.enableRaytracing',1)
		self.startUI(DispTitle="Shadow Panel",WinTitle="Shadows",WinName="ShadowPanel")
		tops = maya.cmds.rowLayout(nc=4,adjustableColumn=2,p=self.vertLyt)
		self.dimmerVal = 1.0 # always reset when starting a new window
		self.dimmer = maya.cmds.floatSliderGrp(p=tops,label='Dimmer',field=True,value=self.dimmerVal,min=0,max=2.0,cw3=[40,60,100],cc=self.dimmerHandler,dc=self.dimmerHandler,annotation='Controls brightness over all lamps')
		maya.cmds.text(label=' ',p=tops)
		self.metered = CVTCheckBox(Parent=tops,Width=50,Label='Meter',Anno='use metering?')
		self.meterPick = CVTButton(Parent=tops,Width=30,Label='Pick',Col=[.2,.4,.3],Anno='set metering distance to selected object')
		self.metered.enable(False)
		self.meterPick.enable(False)
		for a in self.lamps:
			a.init_ui(Parent=self.vertLyt,Master=self)
		#
		self.statusLine(Label='Welcome to the Visualizer for Maya\nShadow Panel')
		self.helpCloseFooter()
		maya.cmds.showWindow(self.window)

	# ########################


	# button handlers for main window #################

	def helpHandler(self, *args):
		helpText = """Use the Shadow Panel
as a quick may to manage light intensities, colors,
and of course shadows. Just the key attributes
are all there for quick handling.

When you start or refresh the panel, it will first try
to find lights in the current Maya selection. If None
are selected it will show all lights.

If intensity or color are driven by external connections,
they won't appear in the panel.

In addition, you can use "meter mode" to unify
light intensities -- use the 'ctrl-T' indicator to
set the distance, or select an objects and press
the "Pick" button to say:
"Set the right intensities for THIS object."
The panel script will do the rest!
"""
		self.showHelpWindow(Message=helpText,DispTitle='Shadow Panel Help',WinTitle="Shadow Panel Help")

def ShadowPanel():
	ShadowPanelUI().showUI()

# ########################### eof ###
