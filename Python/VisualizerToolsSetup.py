"""
Contains the same script (except for the invovcation) as found as a script node
   in the "open_me_to_install.ma" scene.
   
   TO-DO:
     Look for updates on git
     Split userSetup.mel and userSetup.py?
     What about maya/scripts instead of maya/version/scripts?

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

import os, sys, re, maya

def MayaVisToolSetup():
  sceneName = maya.cmds.file(sn=True,q=True)
  visToolsDir = os.path.split(sceneName)[0]
  visMelPath = visToolsDir+'/MEL'
  visPyPath = os.path.join(os.path.normpath(visToolsDir),'Python')
  what = "MayaVisualizerTools"
  mayaVers = os.path.split(os.environ['MAYA_LOCATION'])[-1].__str__()[4:]
  x64 = os.environ.get('PROCESSOR_ARCHITECTURE','32bit')
  if x64 == 'AMD64':
    mayaVers += '-x64'
  userSetupFile = None
  userPythonFile = None
  needMel = True
  needPy = True
  previous = '// end //\n'
  for pName in sys.path:
    if pName == visPyPath:
      print 'Python path already includes "%s"'%(visPyPath)
      needPy = False
  existingMelPath = maya.mel.eval('getenv "MAYA_SCRIPT_PATH"')
  for pName in existingMelPath.split(';'):
    if pName == visMelPath:
      print 'Mel path already includes "%s"'%(visMelPath)
      needMel = False
    if os.path.exists(pName):
      for fName in os.listdir(pName):
        if needMel and fName == 'userSetup.mel':
          userSetupFile = os.path.join(pName,fName)
        if needPy and fName == 'userSetup.py':
          userPythonFile = os.path.join(pName,fName)
  if not (needMel or needPy):
    maya.cmds.confirmDialog(title=what+' install', message='Already Installed!\nNo need for changes.',button='OK')
    return
  if userSetupFile:
    fp = open(userSetupFile,'r')
    previous = fp.read()
    fp.close()
  elif userPythonFile:
    fp = open(userPythonFile,'r')
    previous = fp.read()
    fp.close()
  else:
    homeDir = os.environ.get('HOME','.')
    mayaDefaultScriptDir = os.path.join(homeDir,'maya',mayaVers,'scripts')
    if not os.path.exists(mayaDefaultScriptDir):
      maya.cmds.confirmDialog(title=what+' install failure',message='Cannot find location to create userSetup.mel\n%s'%(mayaDefaultScriptDir),button='OK')
      return
    userPythonFile = os.path.join(mayaDefaultScriptDir,'userSetup.py')
    userSetupFile = userPythonFile
    # userSetupFile = os.path.join(mayaDefaultScriptDir,'userSetup.mel')
    print 'Will create "%s"'%(userSetupFile)
  print 'Adding %s paths to "%s"'%(what,userSetupFile)
  fp = open(userSetupFile,'w')
  hasVisTools = False
  hdr = '// '
  if userPythonFile:
    visPyPath = re.sub(r'\\', r'\\\\', visPyPath)
    hdr = '## '
  for line in previous.split('\n'):
    isDelim = line[:len(what)+3] == hdr + what
    if isDelim:
      hasVisTools = True
    if not hasVisTools and not userPythonFile:
      # that is, we insert into userSetup.mel as early as possible
      fp.write(hdr+what+' '+'='*20+'\n\n')
      fp.write('putenv "{0}" ( `getenv "{0}"` + \":{1}\");\n'.format('MAYA_SCRIPT_PATH',visMelPath))
      fp.write('python("import sys");\n')
      fp.write(r'python("sys.path.append(r\"%s\")");'%(visPyPath)+'\n')
      fp.write(hdr+what+' '+'='*20+'\n')
      hasVisTools = True
    # we insert into the userSetup.py file as LATE as possible
    if userPythonFile and not hasVisTools:
      fp.write(hdr+what+' '+'='*20+'\n')
      fp.write("import sys, maya\n")
      fp.write('sys.path.append(r"%s")'%(visPyPath))
      fp.write('maya.mel(\'putenv "{0}" ( `getenv "{0}"` + \";{1}\");\')\n'.format('MAYA_SCRIPT_PATH',visMelPath))
      fp.write(hdr+what+' '+'='*20+'\n')
    fp.write(line+'\n')
  fp.close()
  maya.cmds.confirmDialog(title=what+' install', message='Paths assigned for Maya %s!\nNow just restart Maya'%(mayaVers),button='OK')

# MayaVisToolSetup()

########### eof ##

