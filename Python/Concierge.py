"""
Visualizer Quick Setup - handles all the trivial housekeeping for you when
  importing or creating a new Maya scene. Just load your scene and ask the
  Visualizer Concierge to Prep() it!

Try this in a shelf button:

import Concierge
Concierge.Prep()

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
import unittest
# this little trick enables us to run unittests in mayapy.exe..
try:
  import maya.standalone
  maya.standalone.initialize()
except:
  pass
from  CVToolUtil import *
import CVSupportCheck

class Service(CVToolUtil):
  use = None    # we use this to let Qt know where to look for stuff
  "should be a singleton"
  def __init__(self):
    super(Service,self).__init__()
    Service.use = self
    self.names = []    # ORDERED
    self.val = {}       
    self.prev = {}       
    self.desc = {}       
    self.hasChanges = False
    self.iblUpdate = False
    SC = CVSupportCheck.SupportChecker()
    self.probNodes = SC.actual_problems()
    
  def already_okay(self):
    "is the scene already okay?"
    return (not self.hasChanges) and (len(self.probNodes) == 0)

  def cache(self,Name,Value,Desc="%d Other changes"):
    """
    Put potentially-changed attrs into a hash for processing later.
    Returns True if a value is needed.
    """
    try:
      prevVal = maya.cmds.getAttr(Name)
    except:
      return False # no such attr
    if prevVal == Value:
      return False
    if self.val.has_key(Name):
      print 'Ooops, attr "%s" (value %s) over-written with (%s)' % (Name,self.val[Name],Value)
    else:
      self.names.append(Name)
      if self.desc.has_key(Desc):
        self.desc[Desc] += 1
      else:
        self.desc[Desc] = 1
    self.val[Name] = Value
    self.prev[Name] = prevVal
    self.hasChanges = True
    return True

  def set(self,Name):
    "actually send this value to Maya"
    if not self.val.has_key(Name):
      print 'Can\'t set attr "%s" because it\'s not defined' % (Name)
      return
    t = type(self.val[Name])
    if t is tuple:
      print "some sort of tuple, oops"
      return
    try:
      maya.cmds.setAttr(Name,self.val[Name])
    except:
      print 'Error setting "%s" to %s'%(Name,self.val[Name])

  def undo(self,Name):
    "actually send this value to Maya"
    if not self.prev.has_key(Name):
      print 'Can\'t set attr "%s" because it\'s not defined' % (Name)
      return
    t = type(self.prev[Name])
    if t is tuple:
      print "some sort of tuple, oops"
      return
    try:
      maya.cmds.setAttr(Name,self.prev[Name])
    except:
      print 'Error setting "%s" to %s'%(Name,self.prev[Name])

  def log(self,Name):
    "don't actually send this value to Maya"
    if not self.val.has_key(Name):
      print '# Can\'t set attr "%s" because it\'s not defined' % (Name)
      return
    t = type(self.val[Name])
    if t is tuple:
      print "# %s is some sort of tuple, oops"%(Name)
      return
    print 'maya.cmds.setAttr("%s",%s)'%(Name,self.val[Name])

  def send_all(self):
    for n in self.names:
      self.set(n)

  def log_all(self):
    for n in self.names:
      self.log(n)

  def undo_all(self):
    for n in self.names:
      self.undo(n)

  # most of the work gets done here

  def problem_texture_finder(self):
    "Look for unsupported texture formats -- TO-DO imporove"
    filenodes = []
    try:
      filenodes =  maya.cmds.ls(type="file")
    except:
      print "Err: cannot access file nodes"
      return
    for f in maya.cmds.ls(type="file"):
      try:
        fn = maya.cmds.getAttr(f+".ftn").lower()
        m = re.search(r'\.(map|psd|iff)$',fn)
        if m:
          print ('Caution: problem %s texture\n\t"%s"\n' % (m.groups(0)[0],fn))
      except:
        print '\tUnable to check texture format for "%f"'

  def enable_shadows(self):
    "turn on raytraced shadows for all lights that might need them"
    for L in maya.cmds.ls(lights=True):
      self.cache((L+".useRayTraceShadows"),True,"Shadows enabled for %d lights")

  def reflection_reduction(self,DefaultReflectivity=0.0):
    """Reduces the default reflectivity from 0.5 to DefaultReflectivity.
    Normally not used if the scene has been raytraced before."""
    for M in maya.cmds.ls(materials=True):
      try:
        if maya.cmds.attributeQuery('reflectivity',node=M,exists=True):
          reflAttr = M+".reflectivity"
          try:
            if maya.cmds.getAttr(reflAttr) == 0.5: # the untraced default: let's drop it to zero
              self.cache(reflAttr,DefaultReflectivity,"Reflectivity tuned for %d materials")
          except:
            print "issue with node %s"%(M)
      except:
        print "issue with material %s reflectivity"%(M)

  def correct_area_light_shapes(self):
    # make sure area lights use the right shape
    for L in maya.cmds.ls(type="areaLight"): # only if mental is active? TO-DO: find out
      self.cache(L+".areaLight",True,"%d Area lights tuned")
      self.cache(L+".useRayTraceShadows",True,"Area light shadow attrs adjusted")
      try:
        if maya.cmds.getAttr(L+".shadowRays") == 1:
          self.cache(L+".shadowRays",8,"Area light shadow rays increased") # chosen after CO chat
      except:
        print "issue with light %s"%(L)

  def adjust_final_gather_rays(self):
    if not maya.cmds.getAttr("miDefaultOptions.finalGather"):
      return
    # final gather vs diffuse
    try:
      fgRays = maya.cmds.getAttr("miDefaultOptions.finalGatherRays")
      if fgRays > 24:   # TO-DO -- what value REALLY????
        fgRays = int(fgRays/50)
        fgRays = min(fgRays,1)
      self.cache("miDefaultOptions.finalGatherRays",fgRays,"GI Rays adjusted") # ??????
    except:
      print "issue with miDefaultOptions"
    try:
      self.cache("CausticVisualizerBatchSettings.giMaxPrimaryRays",fgRays,"GI Rays adjusted")
      self.cache("CausticVisualizerSettings.giMaxPrimaryRays",fgRays,"GI Rays adjusted")
      cvPasses = maya.cmds.getAttr("CausticVisualizerBatchSettings.multiPassPasses")
      if cvPasses < 24:
        self.cache("CausticVisualizerBatchSettings.multiPassPasses",24,"Pass Count Improved")
      cvPasses = maya.cmds.getAttr("CausticVisualizerSettings.multiPassPasses")
      if cvPasses < 24:
        self.cache("CausticVisualizerSettings.multiPassPasses",24,"Pass Count Improved")
    except:
      print "issue with CV nodes"

  def adaptive_sampling(self):
    "Turn on adaptive sampling UNLESS motion blur is active"
    Adapt = True
    try:
      Adapt = not maya.cmds.getAttr('CausticVisualizerBatchSettings.motionBlur')
    except:
      # not all versions have that attribute
      pass
    self.cache("CausticVisualizerBatchSettings.multiPassAdaptive",Adapt,"Adaptive Sampling %s"%(Adapt))
    self.cache("CausticVisualizerSettings.multiPassAdaptive",Adapt,"Adaptive Sampling %s"%(Adapt))

  def linear_light_workflow(self):
    # color setup is based on expected output format
    use8Bit = is_8_bit()
    # set clipped filtering on
    self.cache("CausticVisualizerBatchSettings.clipFinalShadedColor",use8Bit,"Image range clipping adjusted")
    msg = "8-bit Color Profile Tuned" if use8Bit else "Floating-Point Color Profile Tuned"
    self.cache("defaultRenderGlobals.colorProfileEnabled",True,msg)
    self.cache("defaultRenderGlobals.inputColorProfile",3,msg)
    connectProfile = 3 if use8Bit else 2
    self.cache("defaultRenderGlobals.outputColorProfile",connectProfile,msg) 
    self.cache("defaultViewColorManager.imageColorProfile",connectProfile,msg) 
    self.cache("defaultViewColorManager.displayColorProfile",3,msg)
    self.cache("defaultViewColorManager.exposure",0.0,msg)
    self.cache("defaultViewColorManager.contrast",0.0,msg)
    self.problem_texture_finder()

  def calculate_needs(self):
    """
    build a list of needed changes
    Not currently managed:
      Enable DIffuse/Enable Caustics
      Camera Settings: Depth of Field and Motion Blur
    """
    neverTraced = self.cache("defaultRenderQuality.enableRaytracing",1,"Raytracing enabled")
    mrAvailable = expected_plugin("Mayatomr")
    hasUsedMental = is_mental() or smells_mental()
    self.enable_shadows()
    self.iblUpdate = update_string_options() # this part is NOT in the undo stack... harmless
    if self.iblUpdate:
      self.hasChanges = True
      self.desc["mentalray IBL native mode enabled"] = 1
    if neverTraced:
      self.reflection_reduction()
    if hasUsedMental:
      self.correct_area_light_shapes()
      self.adjust_final_gather_rays()
    self.adaptive_sampling()
    self.linear_light_workflow()

  def showUI(self):
    dl = []
    titleText = 'Scene Ready to Render!'
    needDIY = True
    if self.already_okay():
      titleText = "No Changes"
      needDIY = False
      dl.append("No changes needed!")
      dl.append("This scene is already fine, enjoy.")
    else:
      for d in self.desc:
        ds = d
        if ds.__contains__('%d'):
          ds = ds % (self.desc[d])
        dl.append(ds)
      if len(self.probNodes) > 0:
        dl.append('Potential Unaltered Hypershade Issues:')
        for t in self.probNodes:
          nt = len(maya.cmds.ls(typ=t))
          dl.append('> %s, %d node%s: %s'%(t,nt,('s' if nt>1 else ''),CVSupportCheck.SupportChecker.hs_issue(t)))
    # start actual UI bits
    self.startUI(DispTitle=titleText,WinTitle="Visualizer Concierge",WinName="Concierge",LogAction='Concierge')
    midsection = maya.cmds.columnLayout(p=self.vertLyt,co=['left',10],rs=3)
    for d in dl:
      maya.cmds.text(p=midsection,label=d)
    #
    bots = maya.cmds.rowLayout(p=self.vertLyt,nc=2+needDIY)
    wd = 120
    if not needDIY:
      wd = 120 * 3 / 2
    if self.appVersion > 2013:
      helpBtn = maya.cmds.iconTextButton(p=bots,label='Help',st='textOnly',width=wd,flat=True,bgc=[.4,.4,.3],mw=10,command=Service.use.helpHandler)
      okayBtn = maya.cmds.iconTextButton(p=bots,label='Great, Thanks',st='textOnly',width=wd,flat=True,bgc=[.3,.4,.3],font='boldLabelFont',mw=10,command=Service.use.okHandler)
      if needDIY:
        diyBtn = maya.cmds.iconTextButton(p=bots,label='No, I\'ll Do It Myself',st='textOnly',width=wd,flat=True,bgc=[.4,.3,.3],mw=10,command=Service.use.diyHandler)
    else:
      helpBtn = maya.cmds.iconTextButton(p=bots,label='Help',st='textOnly',width=wd,bgc=[.4,.4,.3],mw=10,command=Service.use.helpHandler)
      okayBtn = maya.cmds.iconTextButton(p=bots,label='Great, Thanks',st='textOnly',width=wd,bgc=[.3,.4,.3],font='boldLabelFont',mw=10,command=Service.use.okHandler)
      if needDIY:
        diyBtn = maya.cmds.iconTextButton(p=bots,label='No, I\'ll Do It Myself',st='textOnly',width=wd,bgc=[.4,.3,.3],mw=10,command=Service.use.diyHandler)
        maya.cmds.rowLayout(bots,edit=True,co2=[20,20])
      else:
        maya.cmds.rowLayout(bots,edit=True,co3=[20,40,20])
    maya.cmds.showWindow(self.window)

  # button handlers
  def okHandler(self, *args):
    if not self.already_okay():
      print "Happy to be of service!"
    maya.cmds.deleteUI(self.window)
    self.window = None
  def diyHandler(self, *args):
    print "# Reverting these changes: ######"
    self.undo_all()
    self.log_all()
    if self.iblUpdate:
      print "# mental ray IBL stringOptions not reverted"
    print "# end of Concierge log ##########"
    maya.cmds.deleteUI(self.window)
    self.window = None

  def helpHandler(self, *args):
    helpText = """The concierge will do its best to prep your scene
for use with the Visualizer for Maya. It checks and properly
sets-up common issues such as shadowing, ray-trace enabling, etc.
Everything the Concierge has done (if anything!) is listed
right in the Concierge window.

If you choose not to approve these actions, Concierge will revert
all Maya settings, and will also write to the Maya Script Editor
window a complete listing of what it *would* have altered --
you can copy and paste these commands selectively yourself."""
    self.showHelpWindow(Message=helpText,DispTitle='Visualizer Concierge Help',WinTitle="Concierge Help")


######### FIND AND FIX MAYA STUFF ###################################################

def needed_node(Name):
  n = maya.cmds.ls(Name)
  if len(n) != 1:
    nn = maya.cmds.createNode(Name,name=Name,shared=True,skipSelect=True)
    if nn != Name:
      maya.cmds.warning('Unable to correctly create node "%s" - got "%s"\n'%(Name,nn))
      return False
  return True

def expected_plugin(Name):
  n = maya.cmds.pluginInfo(Name,query=True,loaded=True)
  if not n:
    maya.cmds.warning('Sorry, the "%s" plugin is not loaded!\n'%(Name))
  return n

## mental ray string options ###############

def cv_assign_mr_stringopt(Name,Type,Value):
  "python version of mel script"
  prevName = None
  for i in range(0,200):
      attr = "miDefaultOptions.stringOptions[%d]" % (i)
      try:
        prevName = maya.cmds.getAttr(attr+".name")
      except:
        print "issue with %s"%(attr)
        break
      if prevName == "":        # we ran off the end of mental ray's existing list
        print "Adding '%s'=(%s) as stringOption[%d]" % (Name,Value,i)
        try:
          maya.cmds.setAttr(attr+".name",Name,type="string")
          maya.cmds.setAttr(attr+".type",Type,type="string")
          maya.cmds.setAttr(attr+".value",Value,type="string")
        except:
          print "Error assigning stringOption"
        return True
      elif prevName == Name:         # there is already a stringopt with the desired name
        prevValue = maya.cmds.getAttr(attr+".value")
        if prevValue == Value:
          # print "The '%s' stringOption is already set to [%s] - Great!" % (Name,Value)
          return False # the existing value is already the desired value
        try:
          maya.cmds.setAttr(attr+".value",Value,type="string")
        except:
          print "Error setting %s.value"%(attr)
        print "Changing '%s' stringOption from [%s] to [%s]" % (Name,prevValue,Value) 
        return True
  # maya.cmds.warning("Hmm, never got to '%s'\n" % (Name))
  return False

def update_string_options():
  "mental ray string options -- update mental IBL to 'native' -- return True if anything changed"
  changes = False
  prevSel = maya.cmds.ls(selection=True)
  # print ("Optimizing MentalRay IBL Options for Caustic Visualizer Use:\n")
  try:
    maya.cmds.select("miDefaultOptions",replace=True) # selecting it will ensure it exists
    changes |= cv_assign_mr_stringopt("environment lighting mode","string","light")
    changes |= cv_assign_mr_stringopt("environment lighting quality","float","0.75")
    changes |= cv_assign_mr_stringopt("environment lighting shadow","string","on")
    changes |= cv_assign_mr_stringopt("light relative scale","float","0.31831") # (1.0/PI)
    changes |= cv_assign_mr_stringopt("light lighting resolution","int","512")
  except:
    print "Caution, mental ray is not loaded"
    return False
  if len(prevSel) > 0:
    maya.cmds.select(prevSel)
  return changes

##

def is_8_bit():
  "try to tell if the output is 8bit or what"
  renderer = maya.mel.eval("currentRenderer();")
  if renderer == 'CausticVisualizer':
    fmt = maya.cmds.getAttr('CausticVisualizerBatchSettings.imageFormat')
    return  (fmt != 0) and (fmt != 5) # i.e., EXR or TIFF
  fmt =  maya.cmds.getAttr('defaultRenderGlobals.imageFormat')
  if fmt > 50:
    return False
  return True
 
## detect mental ray ######

def is_mental():
  "look for traces of mental ray usage in this scene"
  renderer = maya.mel.eval("currentRenderer();")
  if renderer == 'mentalRay':
    return True # that was easy
  if renderer == 'CausticVisualizer':
    try:
      emulator = maya.cmds.getAttr("CausticVisualizerBatchSettings.rendererEmulation")
      if emulator == 2:  # hopefully this never chnages!!!
        return True # we are in mental emulaton mode
    except:
      print "issue with emulation"
  return False

def smells_mental():
  "look for traces of mental ray usage in this scene"
  renderer = maya.mel.eval("currentRenderer();")
  if renderer == 'mentalRay':
    return True # that was easy
  for M in maya.cmds.ls(materials=True):
    try:
      if maya.cmds.attributeQuery('miFactoryNode',node=M,exists=True) or \
        maya.cmds.attributeQuery('miForwardDefinition',node=M,exists=True):
        return True
    except:
      print "Not finding %s mental attrs"%(M)
  return False

def Prep():
  """
  Make sure mental ray is loaded? React differently, depending.
  Likewise Caustic Visualizer....
  """
  aList = Service()
  if not expected_plugin("CausticVisualizer"):
    # load it
    try:
      plugRes = maya.cmds.loadPlugin("CausticVisualizer.mll")
      if len(plugRes) < 1:
        maya.cmds.warning('Unable to load the Visualizer plugin!\nCheck your installation.\n')
        return
    except:
      print "Sorry, cannot load Caustic Visualizer for Maya!!"
      aList.showHelpWindow(Message="Sorry, Caustic Visualizer for Maya cannot be Loaded",DispTitle='Visualizer Concierge Halt',WinTitle="Concierge Fail")
      return
  needed_node("CausticVisualizerBatchSettings")
  needed_node("CausticVisualizerSettings")
  aList.calculate_needs()
  if not aList.already_okay():
    aList.send_all()
    for d in aList.desc:
      ds = d
      if ds.__contains__('%d'):
        ds = ds % (aList.desc[d])
      print ds
  aList.showUI()
  return

#### UNIT TESTING #################

class TestStuff(unittest.TestCase):
  """
  Unit-Test Class
  """
  def setUp(self):
    pass
  def test_hasNodes(self):
    svc = Service()
    "see if we got that far"
    self.assertTrue(len(svc.probNodes) is not None)
  def test_createBatchNode(self):
    "prints warnings, but completes when testing"
    self.assertTrue(needed_node("CausticVisualizerBatchSettings"))
  def test_smell(self):
    "scene is empty"
    self.assertFalse(smells_mental())

if __name__ == "__main__":
  print "Running Concierge Unit Tests"
  unittest.main()

################# eof ##
