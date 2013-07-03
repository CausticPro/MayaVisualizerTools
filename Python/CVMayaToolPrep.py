"""
Typically this is called from a  script node
	 in the "open_me_to_install.ma" scene.
If you'd rather DIY, just run the MayaVisToolSetup('c:/actual/location/of/vis/tools')
	to ensure that all paths are initialized for userSetup
	with the script sin this GitHub repo.

WHAT IT DOES:
	Checks first to see if the correct paths for Mel and python are already defined,
		and halts if nothing is needed.
	Otherwise:
		if you have a userSetup.py and no userSetup.mel and need only the python path,
			it Will append to sys.path in that file (it will add a line at the end) --
			userSetup.py loads before mel, so adding the mel path here is impractical.
		otherwise it will append or create userSetup.mel
			and add the required path(s) there.

	 TO-DO:
		 Look for updates on git
		 Split userSetup.mel and userSetup.py?
		 What about maya/scripts instead of maya/version/scripts?

# TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THIS SOFTWARE IS PROVIDED
# *AS IS* AND IMAGINATION TECHNOLOGIES AND ITS SUPPLIERS DISCLAIM ALL WARRANTIES, EITHER
# EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS FOR A PARTICULAR PURPOSE.	IN NO EVENT SHALL IMAGINATION TECHNOLOGIES OR ITS
# SUPPLIERS BE LIABLE FOR ANY SPECIAL, INCIDENTAL, INDIRECT, OR CONSEQUENTIAL DAMAGES
# WHATSOEVER (INCLUDING, WITHOUT LIMITATION, DAMAGES FOR LOSS OF BUSINESS PROFITS,
# BUSINESS INTERRUPTION, LOSS OF BUSINESS INFORMATION, OR ANY OTHER PECUNIARY
# LOSS) ARISING OUT OF THE USE OF OR INABILITY TO USE THIS SOFTWARE, EVEN IF
# IMAGINATION TECHNOLOGIES HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
"""

import os
import sys
import re
import maya.cmds
import maya.mel

def srcDirMissing(SrcDir):
	if not os.path.exists(os.path.normpath(SrcDir)):
		maya.cmds.confirmDialog(title=what+' install', message='Sorry, the directory\n"%s"\ndoes not appear to exist'%(SrcDir),button='OK')
		return True
	return False

def MayaVisToolSetup(VisToolsDir=None, HasValidPyPath=None):
	what = "MayaVisualizerTools"
	visToolsDir = VisToolsDir
	if visToolsDir is None:
		sceneName = maya.cmds.file(sn=True,q=True)
		visToolsDir = os.path.split(sceneName)[0]
	visMelPath = visToolsDir+'/MEL'
	visPyPath = os.path.join(os.path.normpath(visToolsDir),'Python')
	if srcDirMissing(visToolsDir) or srcDirMissing(visMelPath) or srcDirMissing(visPyPath):
		return
	mayaVers = os.path.split(os.environ['MAYA_LOCATION'])[-1].__str__()[4:]
	x64 = os.environ.get('PROCESSOR_ARCHITECTURE','32bit')
	if x64 == 'AMD64':
		mayaVers += '-x64'
	userSetupFile = None
	userPythonFile = None
	needMel = True
	needPy = True
	if HasValidPyPath is not None:
		needPy = not HasValidPyPath
	else:
		needPy = not sys.path.__contains__(visPyPath)
	existingMelPaths = maya.mel.eval('getenv "MAYA_SCRIPT_PATH"').split(';')
	needMel = existingMelPaths.__contains__(visMelPath)
	if not (needMel or needPy):
		maya.cmds.confirmDialog(title=what+' install', message='The correct paths are\nalready installed!\nNo need for changes.', messageAlign='center',button='OK')
		return
	for pName in existingMelPaths:
		if os.path.exists(pName):
			if needMel:
				m = os.path.join(pName,'userSetup.mel')
				if os.path.exists(m):
					userSetupFile = m
			elif needPy:
				p = os.path.join(pName,'userSetup.py') # yes look in mel paths... 
				if os.path.exists(p):
					userPythonFile = p
	if userPythonFile: # only true if needMel is False
		fp = open(userPythonFile,'a')
		fp.write("# Appended for %s\n"%(what))
		fp.write("import sys\n")
		fp.write('sys.path.append(r"%s")\n\n'%(visPyPath))
		fp.close()
		userSetupFile = userPythonFile
	else:
		fm = 'w'
		if userSetupFile:
			fm = 'a'
		else:
			homeDir = os.environ.get('HOME','.')
			mayaDefaultScriptDir = os.path.join(homeDir,'maya',mayaVers,'scripts')
			if not os.path.exists(mayaDefaultScriptDir):
				maya.cmds.confirmDialog(title=what+' install failure',message='Cannot find location to create userSetup.mel\n%s'%(mayaDefaultScriptDir),button='OK')
				return
			userSetupFile = os.path.join(mayaDefaultScriptDir,'userSetup.mel')
		fp = open(userSetupFile,fm)
		fp.write('// '+what+' '+'='*20+'\n\n')
		if needMel:
			fp.write('putenv "{0}" ( `getenv "{0}"` + \":{1}\");\n'.format('MAYA_SCRIPT_PATH',visMelPath))
		if needPy:
			fp.write('python("import sys");\n')
			vx = re.sub(r'\\',r'\\\\',visPyPath)
			fp.write(r'python("sys.path.append(r\"%s\")");'%(vx)+'\n')
		fp.write('\n')
		fp.close()
	# wrap up
	msg = ''
	if needMel:
		msg += 'Mel path: "%s"\n' % (visMelPath)
		cmd = 'putenv "MAYA_SCRIPT_PATH" ( `getenv "MAYA_SCRIPT_PATH"` + ";%s");' % (visMelPath)
		print cmd
		try:
			maya.mel.eval(cmd)
		except:
			print 'mel error'
		if needPy:
			msg += '\tand\n'
	if needPy:
		msg += 'Python path: "%s"\n' % (visPyPath)
		sys.path.append(visPyPath)
	msg += 'added to\n"%s"\nfor %s\n'%(userSetupFile,mayaVers)
	maya.cmds.confirmDialog(title=what+' install', message=msg, messageAlign='center', button='OK')

########### eof ##