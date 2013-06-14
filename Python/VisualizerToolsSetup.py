"""
Contains the same script (except for the invovcation) as found as a script node
   in the "open_me_to_install.ma" scene.
"""

import os, sys, re, maya

def MayaVisToolSetup():
  sceneName = maya.cmds.file(sn=True,q=True)
  visToolsDir = os.path.split(sceneName)[0]
  # print 'These tools have been placed in "%s"' % (visToolsDir)
  # sys.path.append(os.path.join(visToolsDir,'Python'))
  what = "MayaVisualizerTools"
  mayaVers = os.path.split(os.environ['MAYA_LOCATION'])[-1].__str__()[4:]
  x64 = os.environ.get('PROCESSOR_ARCHITECTURE','32bit')
  if x64 == 'AMD64':
    mayaVers += '-x64'
  userSetupFile = None
  previous = '// end //\n'
  for pName in maya.mel.eval('getenv "MAYA_SCRIPT_PATH"').split(';'):
    if os.path.exists(pName):
      print "check "+pName
      for fName in os.listdir(pName):
        if fName == 'userSetup.mel':
          userSetupFile = os.path.join(pName,fName)
  if userSetupFile:
    fp = open(userSetupFile,'r')
    previous = fp.read()
    fp.close()
  else:
    homeDir = os.environ.get('HOME','.')
    mayaDefaultScriptDir = os.path.join(homeDir,'maya',mayaVers,'scripts')
    if not os.path.exists(mayaDefaultScriptDir):
      maya.cmds.confirmDialog(title=what+' install failure',message='Cannot find location to create userSetup.mel\n%s'%(mayaDefaultScriptDir),button='OK')
      return
    userSetupFile = os.path.join(mayaDefaultScriptDir,'userSetup.mel')
    print 'Will create "%s"'%(userSetupFile)
  print 'Adding %s paths to "%s"'%(what,userSetupFile)
  fp = open(userSetupFile,'w')
  hasVisTools = False
  melPath = visToolsDir+'/MEL'
  pyPath = os.path.join(os.path.normpath(visToolsDir),'Python')
  pyPath = re.sub(r'\\', r'\\\\', pyPath)
  for line in previous.split('\n'):
    isDelim = line[:len(what)+3] == '// ' + what
    if isDelim:
      hasVisTools = True
    if not hasVisTools:
      fp.write('// '+what+' '+'='*20+'\n\n')
      fp.write('putenv "{0}" ( `getenv "{0}"` + \":{1}\");\n'.format('MAYA_SCRIPT_PATH',melPath))
      fp.write('python("import sys");\n')
      fp.write(r'python("sys.path.append(r\"%s\")");'%(pyPath)+'\n')
      fp.write('// '+what+' '+'='*20+'\n')
      hasVisTools = True
    fp.write(line+'\n')
  fp.close()
  maya.cmds.confirmDialog(title=what+' install', message='Paths assigned for Maya %s!\nNow just restart Maya'%(mayaVers),button='OK')

# the script node also calls the above function:
# MayaVisToolSetup()

########### eof ##
