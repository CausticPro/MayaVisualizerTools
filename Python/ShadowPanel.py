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
# Metering on object constraint
#
# add IBL and physical sky setups

import sys, os , re, math
import maya
import unittest
# this little trick enables us to run unittests in mayapy.exe..
try:
  import maya.standalone
  maya.standalone.initialize()
except:
  pass
from  CVToolUtil import *

class DecayButton(CVTButton):
	rateNames = ["No Decay","Linear","Quadratic","Cubic"]
	rateColors = [[0.2,0.2,0.2], [.4,.35,.35], [.25,.3,.25], [.3,.35,.45]]
	def __init__(self,Parent=None,Width=54,Cmd=None,Height=35):
		"A generic enum button gives these scripts a consistent look"
		super(DecayButton,self).__init__(Parent=Parent,Width=Width,Cmd=Cmd,Anno='Distance Falloff',Height=Height)
		self.rate = 0
		self.update()
		print maya.cmds.iconTextButton(self.btn,query=True,height=True)
	def set(self,Rate):
		self.rate = Rate
		if self.rate >= 4:
			self.rate = 0
		return self.rate
	def update(self):
		maya.cmds.iconTextButton(self.btn,edit=True,label=DecayButton.rateNames[self.rate],
			bgc=DecayButton.rateColors[self.rate])

class LampButton(CVTButton):
	"""
	A replacement for Maya's button control.
	It uses a "flat" look via iconTextButton, and makes the call correctly according to version of Maya.
	"""
	icons = {'directionalLight':'directionallight.png',
			'spotLight':'spotlight.png',
			'ambientLight':'ambientlight.png',
			'pointLight':'pointlight.png'}
	def __init__(self,Parent=None,Label='Label',Col=[.3,.3,.3],Width=120,Height=35,Cmd=None,Anno="Tooltip",Font='plainLabelFont',Type=''):
		"A generic button gives these scripts a consistent look"
		super(LampButton,self).__init__(Parent=Parent,Label=Label,Width=Width,Height=Height,Cmd=Cmd,Anno=Anno,Font=Font)
		i = LampButton.icons.get(Type)
		if i is None:
			return
		cx = maya.cmds.iconTextButton(self.btn,query=True,bgc=True)
		maya.cmds.iconTextButton(self.btn,edit=True,st='iconAndTextHorizontal',image=i,mw=4,bgc=cx)

# ############################

class Lamp(object):
	"class for UI sub-panels"
	def __init__(self,ShapeNode,LampType):
		"create based on the specified maya shape or xform node"
		self.shape = ShapeNode
		self.xform = None
		self.master = None
		self.expr = None # potentialy a maya expression for meter-object linking
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
		if self.xform:
			maya.cmds.select(self.xform)
		else:
			maya.cmds.select(self.shape) # eg ibls and such
		#if self.xform is not None:
		#	prev = maya.cmds.ls(sl=True)
		#	lp = len(prev)
		#	if lp > 0 or (lp > 1 and prev[0] != self.xform):
		#		maya.cmds.select(self.xform)

	def selectHandler(self, *args):
		# print 'selectHandler'
		# self.select()
		if self.xform:
			maya.cmds.select(self.xform)
		else:
			maya.cmds.select(self.shape) # eg ibls and such

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
		if self.master.meterState: # is metering on?
			if self.lampType != 'ambientLight' and self.lampType != 'directionalLight' and self.decay.rate != 0:
				meterDist = self.attr('centerOfIllumination')
				v *= math.pow(meterDist,float(self.decay.rate))
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

	def turn_on_meter(self,PreserveMaya=False):
		if self.lampType == 'ambientLight' or self.lampType == 'directionalLight' or  self.decay.rate == 0:
			return # no change anyway
		if PreserveMaya:
			i = self.attr('intensity')
			self.max_intensity(i) # just in case
			maya.cmds.floatSliderGrp(self.intensity,edit=True,value=i)
		else:
			i = self.calculate_maya_intensity()
			self.setAttr("intensity",i)

	def turn_off_meter(self):
		if self.lampType == 'ambientLight' or self.lampType == 'directionalLight' or  self.decay.rate == 0:
			return # no change anyway
		i = self.attr('intensity')
		i /= self.master.dimmerVal
		self.max_intensity(i) # just in case
		maya.cmds.floatSliderGrp(self.intensity,edit=True,value=i)

	def set_abilities(self):
		"enable or disable controls based on the current state of the lamp"
		if self.shadow:
			shadowed = self.useShadow()
			self.shadow.update()
			maya.cmds.intFieldGrp(self.shadRays,edit=True,enable=shadowed)
			maya.cmds.intFieldGrp(self.depthLimit,edit=True,enable=shadowed)
			if self.shadRad:
				maya.cmds.attrFieldSliderGrp(self.shadRad,edit=True,enable=shadowed)
			if self.lightRad:
				maya.cmds.attrFieldSliderGrp(self.lightRad,edit=True,enable=shadowed)
			if self.lightAng:
				maya.cmds.attrFieldSliderGrp(self.lightAng,edit=True,enable=shadowed)
			if self.shadColor:
				maya.cmds.attrColorSliderGrp(self.shadColor,edit=True,enable=shadowed)
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
		#
		toggles = maya.cmds.rowLayout('togs',p=self.panel,nc=5,adjustableColumn=4)
		self.selectMe = LampButton(Parent=toggles,Label='  '+self.xform,Col=[.4,.4,.7],
			Cmd=self.selectHandler,Font='boldLabelFont',Anno='Select %s'%(self.xform),Type=self.lampType,Height=35)
		maya.cmds.separator(p=toggles,style='none',width=14)
		if self.lampType != 'ambientLight':
			self.shadow = CVTCheckBox(Parent=toggles,Label="Shadow",OffLabel='Unshadowed',Width=80,
				OffCol=[.6,.6,.6],OnCol=[.2,.2,.2],Value=self.useShadow(),
				Cmd=self.shadowHandler,Anno='Toggle Shadowing',Height=35)
		else:
			self.shadow = None
		if maya.cmds.attributeQuery('emitDiffuse',node=self.shape,exists=True): # ambi lights do not have these
			maya.cmds.separator(p=toggles,style='none',width=8)
			tog2 = maya.cmds.rowLayout('tog2',p=toggles,nc=4,adjustableColumn=3)
			self.diffuse = CVTCheckBox(Parent=tog2,Label="Diff",OffLabel='NoDiff',Width=46,
				OffCol=[.2,.2,.2],OnCol=[.45,.45,.45],
				Value=self.attr('emitDiffuse'),Cmd=self.eDiffHandler,Anno='Emit Diffuse Light?',Height=35)
			self.specular = CVTCheckBox(Parent=tog2,Label="Spec",Width=46,OffLabel='NoSpec',
				OffCol=[.2,.2,.2],OnCol=[.45,.45,.45],
				Value=self.attr('emitSpecular'),Cmd=self.eSpecHandler,Anno='Emit Specular Light?',Height=35)
			if self.lampType != 'directionalLight':
				maya.cmds.separator(p=tog2,style='none',width=8)
				self.decay = DecayButton(Parent=tog2,Cmd=self.decayHandler,Height=35)
		#
		b = self.calculate_maya_intensity()
		mi = self.max_intensity(b)
		cons = maya.cmds.listConnections(self.shape+".intensity")
		if cons is None:
			self.intensity = maya.cmds.floatSliderGrp(p=self.panel,label='Intensity',field=True,
				value=b,max=mi,cw=[1,120],cc=self.intensityHandler,dc=self.intensitySlideHandler,
				annotation='local intensity')
		else:
			"TO-DO: do not like this! What is the correct behavior???"
			self.intensity = maya.cmds.attrFieldSliderGrp(p=self.panel,label='Intensity',max=mi,cw=[1,120],hmb=True,
				at='%s.intensity'%(self.shape))
		if self.lampType == 'ambientLight':
			self.color = maya.cmds.attrColorSliderGrp(p=self.panel,label='Color',sb=False,
				cw=[1,120],at='%s.color'%(self.shape),annotation='ambient color')
		else:
			crow = maya.cmds.rowLayout('crow',p=self.panel,nc=3,adjustableColumn=2)
			self.color = maya.cmds.attrColorSliderGrp(p=crow,label='Color',sb=False,cw4=[56,60,60,8],
				at='%s.color'%(self.shape),annotation='lamp color')
			maya.cmds.separator(p=crow,style='none')
			self.shadColor = maya.cmds.attrColorSliderGrp(p=crow,label='Shadow',sb=False,cw4=[56,30,60,8],
				at='%s.shadowColor'%(self.shape),annotation='lamp shadow color')
		#
		if maya.cmds.attributeQuery('shadowRadius',node=self.shape,exists=True) and self.lampType != 'ambientLight':
			maxR = max(8.0,self.attr('shadowRadius'))
			self.shadRad = maya.cmds.attrFieldSliderGrp(p=self.panel,label='Shadow Radius',max=maxR,hmb=True,cw=[1,120],
				at='%s.shadowRadius'%(self.shape))
		if maya.cmds.attributeQuery('lightRadius',node=self.shape,exists=True) and self.lampType != 'directionalLight':
			maxR = max(8.0,self.attr('lightRadius'))
			self.lightRad = maya.cmds.attrFieldSliderGrp(p=self.panel,label='Light Radius',max=maxR,hmb=True,cw=[1,120],
				at='%s.lightRadius'%(self.shape),annotation='effective size of the lamp')
		if maya.cmds.attributeQuery('lightAngle',node=self.shape,exists=True):
			maxA = max(20.0,self.attr('lightAngle'))
			self.lightAng = maya.cmds.attrFieldSliderGrp(p=self.panel,label='Light Angle',max=maxA,hmb=True,cw=[1,120],
				at='%s.lightAngle'%(self.shape),annotation='spread angle for shadow rays')
		if maya.cmds.attributeQuery('ambientShade',node=self.shape,exists=True):
			self.ambShade = maya.cmds.attrFieldSliderGrp(p=self.panel,label='Ambient Shade',max=1.0,hmb=True,cw=[1,120],
				at='%s.ambientShade'%(self.shape),annotation='angular falloff of ambient tone')
		if self.shadow:
			rays = maya.cmds.rowLayout('rays',p=self.panel,nc=3,adjustableColumn=2)
			self.shadRays = maya.cmds.intFieldGrp(p=rays,label="Shadow Rays",cw=[1,80],
				v1=self.attr('shadowRays'),annotation='shadow ray count')
			self.depthLimit = maya.cmds.intFieldGrp(p=rays,label="Ray Depth Limit",cw=[1,80],
				v1=self.attr('rayDepth'),annotation='max ray depth for shadows')
		if self.lampType == 'spotLight':
			srow = maya.cmds.rowLayout('srow',p=self.panel,nc=3)
			self.cone = maya.cmds.attrFieldSliderGrp(p=srow,label='Cone',max=180.0,hmb=True,cw3=[30,40,50],
				at='%s.coneAngle'%(self.shape),pre=2,annotation='cone angle')
			self.penumbra = maya.cmds.attrFieldSliderGrp(p=srow,label='Penumbra',min=-10,max=10.0,hmb=True,cw3=[48,40,50],
				at='%s.penumbraAngle'%(self.shape),pre=2,annotation='pensumbrar spread angle')
			self.dropoff = maya.cmds.attrFieldSliderGrp(p=srow,label='Drop',max=255.0,hmb=True,cw3=[24,40,50],
				at='%s.dropoff'%(self.shape),pre=2,annotation='dropoff against the center of the spotlight')
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
		self.meterState = False
		self.meterObject = None # a Dag object
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
		CVTButton(Parent=botCol,Label='Help',Col=[.4,.4,.3],
			Cmd=CVToolUtil.use.helpHandler,Anno='Get help from the Caustic website')
		CVTButton(Parent=botCol,Label='Refresh',Col=[.3,.3,.4],
			Cmd=ShadowPanelUI.use.refreshHandler,Anno='Refresh this window')
		CVTButton(Parent=botCol,Label='Close',Col=[.4,.3,.3],
			Cmd=CVToolUtil.use.closeHandler,Anno='Close this window')

	def dimmerHandler(self, *args):
		self.dimmerVal = maya.cmds.floatSliderGrp(self.dimmer,query=True,value=True)
		for a in self.lamps:
			a.update_intensity()

	def meterHandler(self, *args):
		"this is called BEFORE the CVTCheckBox Value is updated...."
		r = ""
		tt = 'Turn Meter On'
		if self.meterState:
			tt = 'Disable Metering'
		r = maya.cmds.confirmDialog(title=tt,
			message='As we switch metering state:\nPreserve the current Appearance,\nor the Number values shown?',
			button=['Help','Appearance','Numbers','Cancel'],
			defaultButton = 'Appearance',
			cancelButton='Cancel',
			dismissString='Cancel')
		if r == 'Cancel':
				return
		if r == 'Help':
			self.helpHandler(args)
			return
		self.metered.defaultHandler() # now the value is updated....
		self.meterState = self.metered.value # kep separate from UI in case window is refreshed
		if self.metered.value:
			for a in self.lamps:
				a.turn_on_meter(PreserveMaya=(r=='Numbers'))
		else:
			for a in self.lamps:
				a.turn_off_meter()
		self.meterPick.enable(self.meterState)

	def pickHandler(self, *args):
		tt = maya.cmds.ls(sl=True,type='xform')
		meterPt = None
		if len(tt<1):
			print "No objects selected"
			r = maya.cmds.confirmDialog(title='Meter Create',
				message='No object is selected.\nCreate a locator to use as a meter point?',
				button=['Help','Yes','No','Cancel'],
				defaultButton = 'Yes',
				cancelButton='Cancel',
				dismissString='Cancel')
			if r == 'Cancel' or r == 'No':
				return
			if r == 'Help':
				self.helpHandler(args) # TO-DO -- specific help
				return
			meterPt = maya.cmds.createNode('meterPoint',type='locator')
		elif len(tt) > 1:
			r = maya.cmds.confirmDialog(title='Meter Select',
				message='Too many objects.\nUse "%s" as a meter point?'%(tt[0]),
				button=['Help','Yes','No','Cancel'],
				defaultButton = 'Yes',
				cancelButton='Cancel',
				dismissString='Cancel')
			if r == 'Cancel' or r == 'No':
				return
			if r == 'Help':
				self.helpHandler(args) # TO-DO -- specific help
				return
			meterPt = tt[0]
		else:
			meterPt = tt[0]
		print "Someday we can use object '%s' as a light meter location. Please wait."%(meterPt)

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
		self.dimmer = maya.cmds.floatSliderGrp(p=tops,label='Dimmer',field=True,
			value=self.dimmerVal,min=0,max=2.0,cw3=[40,60,100],
			cc=self.dimmerHandler,dc=self.dimmerHandler,annotation='Controls brightness over all lamps')
		# maya.cmds.text(label=' ',p=tops)
		maya.cmds.separator(p=tops,style='none')
		self.metered = CVTCheckBox(Parent=tops,Width=80,Label='Meter',OffLabel='No Meter',Anno='use metering?',
			Value=self.meterState,Cmd=self.meterHandler)
		self.meterPick = CVTButton(Parent=tops,Width=50,Label='Pick',
			Col=[.2,.4,.3],Anno='set metering distance to selected object',
			Cmd=self.pickHandler)
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
	sp = ShadowPanelUI()
	sp.showUI()

# #############################################

class TestShadPanel(unittest.TestCase):
  """
  Unit-Test Class
  """
  def setUp(self):
    self.panel = ShadowPanelUI()
  def test_hasVers(self):
    "see if we got that far"
    self.assertTrue(self.panel.appVersion is not None) 

if __name__ == "__main__":
	unittest.main()

# ########################### eof ###
