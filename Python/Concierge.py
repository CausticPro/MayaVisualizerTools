""" Visualizer Quick Setup - Python version

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

class Service(object):
  use = None    # we use this to let Qt know where to look for stuff
  "should be a singleton"
  def __init__(self):
    Service.use = self
    self.concWindow = None
    self.names = []    # ORDERED
    self.val = {}       
    self.prev = {}       
    self.desc = {}       
    self.hasChanges = False
    self.iblUpdate = False

  def already_okay(self):
    "is the scene already okay?"
    return not self.hasChanges

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
    maya.cmds.setAttr(Name,self.val[Name])

  def undo(self,Name):
    "actually send this value to Maya"
    if not self.prev.has_key(Name):
      print 'Can\'t set attr "%s" because it\'s not defined' % (Name)
      return
    t = type(self.prev[Name])
    if t is tuple:
      print "some sort of tuple, oops"
      return
    maya.cmds.setAttr(Name,self.prev[Name])

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
    for f in maya.cmds.ls(type="file"):
      fn = maya.cmds.getAttr(f+".ftn").lower()
      m = re.search(r'\.(map|psd|iff)$',fn)
      if m:
        print ('Caution: problem %s texture\n\t"%s"\n' % (m.groups(0)[0],fn))

  def calculate_needs(self):
    """
    build a list of needed changes
    """
    neverTraced = self.cache("defaultRenderQuality.enableRaytracing",1,"Raytracing enabled")
    mrAvailable = expected_plugin("Mayatomr")
    hasUsedMental = is_mental() or smells_mental()
    # turn on shadows?
    for L in maya.cmds.ls(lights=True):
      self.cache((L+".useRayTraceShadows"),True,"Shadows enabled for %d lights")
    # update mental IBL to "native"
    self.iblUpdate = update_string_options() # this part is NOT in the undo stack... harmless
    if self.iblUpdate:
      self.hasChanges = True
      self.desc["mentalray IBL native mode enabled"] = 1
    if neverTraced:
      # reduce reflectivity
      for M in maya.cmds.ls(materials=True):
        if maya.cmds.attributeQuery('reflectivity',node=M,exists=True):
          reflAttr = M+".reflectivity"
          if maya.cmds.getAttr(reflAttr) == 0.5: # the untraced default: let's drop it to zero
            self.cache(reflAttr,0.0,"Reflectivity tuned for %d materials")
    if hasUsedMental:
      # make sure area lights use the right shape
      for L in maya.cmds.ls(type="areaLight"): # only if mental is active? TO-DO: find out
        self.cache(L+".areaLight",True,"%d Area lights tuned")
        self.cache(L+".useRayTraceShadows",True,"Area light shadow attrs adjusted")
        if maya.cmds.getAttr(L+".shadowRays") == 1:
          self.cache(L+".shadowRays",8,"Area light shadow rays increased") # chosen after CO chat
      if maya.cmds.getAttr("miDefaultOptions.finalGather"):
        # final gather vs diffuse
        fgRays = maya.cmds.getAttr("miDefaultOptions.finalGatherRays")
        if fgRays > 24:   # TO-DO -- what value REALLY????
          fgRays = int(fgRays/50)
          fgRays = min(fgRays,1)
        self.cache("miDefaultOptions.finalGatherRays",fgRays,"GI Rays adjusted") # ??????
        self.cache("CausticVisualizerBatchSettings.giMaxPrimaryRays",fgRays,"GI Rays adjusted")
        self.cache("CausticVisualizerSettings.giMaxPrimaryRays",fgRays,"GI Rays adjusted")
        cvPasses = maya.cmds.getAttr("CausticVisualizerBatchSettings.multiPassPasses")
        if cvPasses < 24:
          self.cache("CausticVisualizerBatchSettings.multiPassPasses",24,"Pass Count Improved")
        cvPasses = maya.cmds.getAttr("CausticVisualizerSettings.multiPassPasses")
        if cvPasses < 24:
          self.cache("CausticVisualizerSettings.multiPassPasses",24,"Pass Count Improved")
    # set clipped filtering on
    self.cache("CausticVisualizerBatchSettings.clipFinalShadedColor",True,"Image range clipping adjusted")
    # make sure adaptive is on
    self.cache("CausticVisualizerBatchSettings.multiPassAdaptive",True,"Adaptive Sampling Enabled")
    self.cache("CausticVisualizerSettings.multiPassAdaptive",True,"Adaptive Sampling Enabled")
    # set up linear sRGB color workflow
    self.cache("defaultRenderGlobals.colorProfileEnabled",True,"Color Profile Tuned")
    self.cache("defaultRenderGlobals.inputColorProfile",3,"Color Profile Tuned")
    self.cache("defaultRenderGlobals.outputColorProfile",2,"Color Profile Tuned")
    self.cache("defaultViewColorManager.imageColorProfile",2,"Color Profile Tuned")
    self.cache("defaultViewColorManager.displayColorProfile",3,"Color Profile Tuned")
    self.cache("defaultViewColorManager.exposure",0.0,"Color Profile Tuned")
    self.cache("defaultViewColorManager.contrast",0.0,"Color Profile Tuned")
    self.problem_texture_finder()
    ## 
    # how to handle Enable Diffuse and Enable Caustic?
    # camera settings - depth of field enabled?

  def findCausticLogo(self,Logo='CausticVisualizerLogo.png'):
    ml = maya.cmds.pluginInfo('CausticVisualizer.mll',query=True,path=True)
    ml = os.path.normpath(ml)
    ml = os.path.split(os.path.split(ml)[0])[0]
    logoFile = os.path.join(ml,'icons',Logo)
    if not os.path.exists(logoFile):
      print 'cannot find "%s"'%(logoFile)
      return None
    print 'Found logo "%s"'%(logoFile)
    logoFile = re.sub(r'\\','/',logoFile) # Qt likes forwward slash
    return logoFile

  def getUiString(self,UiFileName="Concierge.ui"):
    """
    Find the indicated UI file among sys.path directories, and read it as a string.
    Return None if not found
    """
    for d in sys.path:
      uPath = os.path.join(d,UiFileName)
      if os.path.exists(uPath):
          # print 'Reading "%s"'%(uPath)
          f = open(uPath)
          uiData = f.readlines()
          f.close()
          logoFile = self.findCausticLogo()
          logoInsert = r'<normaloff>%s</normaloff>%s</iconset>'%(logoFile,logoFile)
          pat = re.compile(r'<normaloff>.*png</iconset>')
          Lx = []
          for L in uiData:
            m = pat.search(L)
            if m:
              L = pat.sub(logoInsert,L)
              print L
            Lx.append(L.__str__())
          return '\n'.join(Lx)
    return None

  def showUI(self):
    uiS = self.getUiString()
    if not uiS:
      print "Unable to find UI file!"
      # TO-DO: build vanilla UI from scratch?
      return
    else:
      # print uiS
      self.concWindow = maya.cmds.loadUI(uiString=uiS,verbose=False)
    # print '"%s"'%(self.concWindow) #temporary
    maya.cmds.window(self.concWindow,edit=True,topLeftCorner=[200,200])
    logLabel = self.concWindow+"|central|mainVtLayout|logLabel"
    dl = []
    if self.already_okay():
      title = self.concWindow+"|central|mainVtLayout|Title"
      maya.cmds.text(title,edit=True,label="No Changes")
      dl.append("No changes needed!")
      dl.append("This scene is already fine.")
      dl.append("")
      dl.append("Enjoy.")
      # diyBtn = self.concWindow+"|central|mainVtLayout|btnHzLayout|diyBtn"
      diyBtn = self.concWindow+"|central|mainVtLayout|diyBtn"
      maya.cmds.deleteUI(diyBtn) # no need for it
    else:
      for d in self.desc:
        ds = d
        if ds.__contains__('%d'):
          ds = ds % (self.desc[d])
        dl.append(ds)
    h = maya.cmds.window(self.concWindow,query=True,height=True)
    maya.cmds.window(self.concWindow,edit=True,height=(h+100))
    h = maya.cmds.text(logLabel,query=True,height=True)
    maya.cmds.text(logLabel,edit=True,height=(h+100))
    maya.cmds.text(logLabel,edit=True,label="\n".join(dl))
    maya.cmds.showWindow(self.concWindow)

  # button handlers
  def okHandler(self, *args):
    print "Happy to be of service!"
    maya.cmds.deleteUI(self.concWindow)
    self.concWindow = None
  def diyHandler(self, *args):
    print "# Reverting these changes: ######"
    self.undo_all()
    self.log_all()
    if self.iblUpdate:
      print "# mental ray IBL stringOptions not reverted"
    print "# end of Concierge log ##########"
    maya.cmds.deleteUI(self.concWindow)
    self.concWindow = None
  def helpHandler(self, *args):
    helpText = """The concierge will do its best to prep your scene for use with the
    Caustic Visualizer. It checks and properly sets-up common isues such as shadowing,
    ray-trace enabling, etc. It lists everything it has done (if anything) in the Concierge
    window. If you choose not to approve these actions, Concierge will reverty all Maya settings,
    but will also write to the console a listing of what it would have altered -- you can
    copy and paste these commands selectively yourself."""
    print helpText
  def webHandler(self, *args):
    maya.cmds.launch(web="https://www.caustic.com/visualizer/maya/")

############## UI BITS ###############

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
  for i in range(0,200):
      attr = "miDefaultOptions.stringOptions[%d]" % (i)
      prevName = maya.cmds.getAttr(attr+".name")
      if prevName == "":        # we ran off the end of mental ray's existing list
        print "Adding '%s'=(%s) as stringOption[%d]" % (Name,Value,i)
        maya.cmds.setAttr(attr+".name",Name,type="string")
        maya.cmds.setAttr(attr+".type",Type,type="string")
        maya.cmds.setAttr(attr+".value",Value,type="string")
        return True
      elif prevName == Name:         # there is already a stringopt with the desired name
        prevValue = maya.cmds.getAttr(attr+".value")
        if prevValue == Value:
          print "The '%s' stringOption is already set to [%s] - Great!" % (Name,Value)
          return False # the existing value is already the desired value
        maya.cmds.setAttr(attr+".value",Value,type="string")
        print "Changing '%s' stringOption from [%s] to [%s]" % (Name,prevValue,Value) 
        return True
  maya.cmds.warning("Hmm, never got to '%s'\n" % (Name))
  return False

def update_string_options():
  "mental ray string options -- return True if anything changed"
  changes = False
  prevSel = maya.cmds.ls(selection=True)
  print ("Optimizing MentalRay IBL Options for Caustic Visualizer Use:\n")
  maya.cmds.select("miDefaultOptions",replace=True) # selecting it will ensure it exists
  changes |= cv_assign_mr_stringopt("environment lighting mode","string","light")
  changes |= cv_assign_mr_stringopt("environment lighting quality","float","0.75")
  changes |= cv_assign_mr_stringopt("environment lighting shadow","string","on")
  changes |= cv_assign_mr_stringopt("light relative scale","float","0.31831") # (1.0/PI)
  changes |= cv_assign_mr_stringopt("light lighting resolution","int","512")
  if len(prevSel) > 0:
    maya.cmds.select(prevSel)
  return changes

## detect mental ray ######

def is_mental():
  "look for traces of mental ray usage in this scene"
  renderer = maya.mel.eval("currentRenderer();")
  if renderer == 'mentalRay':
    return True # that was easy
  if renderer == 'CausticVisualizer':
    emulator = maya.cmds.getAttr("CausticVisualizerBatchSettings.rendererEmulation")
    if emulator == 2:  # hopefully this never chnages!!!
      return True # we are in mental emulaton mode
  return False

def smells_mental():
  "look for traces of mental ray usage in this scene"
  renderer = maya.mel.eval("currentRenderer();")
  if renderer == 'mentalRay':
    return True # that was easy
  for M in maya.cmds.ls(materials=True):
    if maya.cmds.attributeQuery('miFactoryNode',node=M,exists=True) or \
      maya.cmds.attributeQuery('miForwardDefinition',node=M,exists=True):
      return True

###########################

###########################

############

def Prep():
  """
  Make sure mental ray is loaded? React differently, depending.
  Likewise Caustic Visualizer....
  """
  aList = Service()
  if not expected_plugin("CausticVisualizer"):
    # load it
    plugRes = maya.cmds.loadPlugin("CausticVisualizer.mll")
    if len(plugRes) < 1:
      maya.cmds.warning('Unable to load the Visualizer plugin!\nCheck your installation.\n')
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

# Prep()
