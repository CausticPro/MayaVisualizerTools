"""
Find node types in shading networks
"""

import sys
import maya
import unittest

class SupportChecker(object):
	# static whitelist for now
	KNOWN_ISSUE = 'Known Issue, Uniform Results Should Look Okay'
	# list of node types, and any known 'issues'
	WhiteList = {
		'animCurve':	None,
		'animCurveTA':	KNOWN_ISSUE,
		'animCurveTL':	KNOWN_ISSUE,
		'animCurveTT':	KNOWN_ISSUE,
		'animCurveTU':	KNOWN_ISSUE,
		'animCurveUA':	KNOWN_ISSUE,
		'animCurveUL':	KNOWN_ISSUE,
		'animCurveUT':	KNOWN_ISSUE,
		'animCurveUU':	KNOWN_ISSUE,
		'anisotropic':	None,
		'blendColors':	None,
		'blendTwoAttr':	None,
		'blinn':	None,
		'brownian':	None,
		'bulge':	None,
		'bump2d':	None,
		'bump3d':	None,
		'checker':	None,
		'choice':	None,
		'clamp':	None,
		'cloud':	None,
		'condition':	None,
		'crater':	None,
		'dgs_material':	None,
		'dielectric_material':	None,
		'displayLayer':	None,
		'displayLayerManager':	None,
		'distanceBetwen':	None,
		'doubleShadingSwitch':	None,
		'envBall':	None,
		'envChrome':	None,
		'envCube':	None,
		'envSky':	None,
		'envSphere':	None,
		'expression':	KNOWN_ISSUE,
		'file':	None,
		'fractal':	None,
		'gammaCorrect':	None,
		'granite':	None,
		'grid':	None,
		'hsvToRgb':	None,
		'lambert':	None,
		'layeredShader':	None,
		'layeredTexture':	None,
		'leather':	None,
		'lightInfo':	None,
		'luminance':	None,
		'luminance':	None,
		'marble':	None,
		'mentalrayLightProfile':	None,
		'mentalrayTexture':	None,
		'mesh':	KNOWN_ISSUE,
		'mi_car_paint_phen':	None,
		'mi_car_paint_phen_x':	None,
		'mi_car_paint_phen_x_passes':	None,
		'mi_metallic_paint_x':	'no flakes',
		'mi_metallic_paint_x_passes':	None,
		'mia_exposure_photographic':	None,
		'mia_exposure_simple':	None,
		'mia_light_surface':	None,
		'mia_material':	None,
		'mia_material_x':	'bump mapping supported',
		'mia_material_x_passes':	'bump mapping supported',
		'mia_photometric_light':	None,
		'mib_amb_occlusion':	None,
		'mib_color_mix':	None,
		'mib_dielectric':	None,
		'mib_illum_blinn':	None,
		'mib_illum_cooktorr':	None,
		'mib_illum_phong':	None,
		'mib_illum_ward':	None,
		'mib_opacity':	None,
		'mib_twosided':	None,
		'mip_cameramap':	None,
		'mip_grayball':	None,
		'mip_matteshadow':	None,
		'mip_mirrorball':	None,
		'mip_rayswitch':	None,
		'mip_rayswitch_advanced':	None,
		'misss_fast_simple_maya':	None,
		'misss_fast_skin_maya':	None,
		'misss_set_normal':	None,
		'misss_skin_specular':	None,
		'multiplyDivide':	None,
		'mute':	None,
		'noise':	None,
		'particleCloud':	None,
		'phong':	None,
		'phongE':	None,
		'place2dTexture':	None,
		'place3dTexture':	None,
		'plusMinusAverage':	None,
		'projection':	None,
		'quadShadingSwitch':	None,
		'ramp':	None,
		'rampShader':	None,
		'remapColor':	None,
		'remapHsv':	None,
		'remapValue':	None,
		'renderLayer':	None,
		'renderLayerManager':	None,
		'reverse':	None,
		'rgbToHsv':	None,
		'rock':	None,
		'samplerInfo':	None,
		'setRange':	None,
		'shadingEngine':	None,
		'singleShadingSwitch':	None,
		'snow':	None,
		'solidFractal':	None,
		'stencil':	None,
		'stucco':	None,
		'surfaceShader':	None,
		'transform':	KNOWN_ISSUE,
		'tripleShadingSwitch':	None,
		'useBackground':	None,
		'vectorProduct':	None,
		'volumeNoise':	None,
		'wood':	None
	}

	@staticmethod
	def hs_issue(NodeType):
		return SupportChecker.WhiteList.get(NodeType,'Unknown Node Type')

	def __init__(self):
		self.hsNodes = {}
		self.hsTypes = {}
		for e in maya.cmds.ls(type='shadingEngine'):
			self.seek_hs_nodes(e)
		self.find_issues()
	def seek_hs_nodes(self,Node):
		if self.hsNodes.has_key(Node):
			return
		self.hsNodes[Node] = 1
		t = maya.cmds.nodeType(Node)
		self.hsTypes[t] = self.hsTypes.get(t,[])
		self.hsTypes[t].append(Node)
		c = maya.cmds.listConnections(Node,d=False,s=True)
		if c:
			for s in c:
				self.seek_hs_nodes(s)
	def find_issues(self):
		self.issues = {}
		for t in self.hsTypes:
			issue = SupportChecker.hs_issue(t)
			if issue is not None:
				self.issues[t] = issue

	def actual_problems(self):
		return [t for t in self.issues if self.issues[t] != SupportChecker.KNOWN_ISSUE]

	def has_issues(self):
		return len(self.issues) > 0

	def probably_okay(self):
		"if all we have are well-known non-killer issues"
		probs = self.actual_problems()
		if len(probs) > 0:
			return False
		return True

	def _found_types(self):
		print "Discovered these node types:"
		for t in sorted(self.hsTypes.keys()):
			print "%s: %d" % (t,len(self.hsTypes[t]))

	def _report_on(self,IssueList,Desc="%d nodes with potential issues"):
		if len(IssueList)>0:
			print "%d node types with *potential* issues:" % (len(IssueList))
			for t in IssueList:
				print '\t%s (%d nodes):\t"%s"' % (t,len(self.hsTypes[t]),self.issues[t])
				for n in sorted(self.hsTypes[t]):
					print '\t\t\t%s' % (n)
		else:
			print "Scene hypergraph looks okay"

	def _short_report_on(self,IssueList,Desc="%d nodes with potential issues"):
		if len(IssueList)>0:
			print "%d node types with *potential* issues:" % (len(IssueList))
			for t in IssueList:
				print '\t%s (%d nodes)\t"%s"' % (t,len(self.hsTypes[t]),self.issues[t])
		else:
			print "Scene hypergraph looks okay"

	def full_report(self):
		self._found_types()
		self._report_on(self.issues.keys())

	def short_report(self):
		self._short_report_on(self.actual_problems())

def check(Full=False):
	# basic call
	SC = SupportChecker()
	if Full:
		SC.full_report()
	else:
		SC.short_report()


class TestStuff(unittest.TestCase):
	"""
	Unit-Test Class
	"""
	def setUp(self):
		self.Checker = SupportChecker()
	def test_hasNodes(self):
		"all maya scenes should at least have an initial shading group!"
		self.assertTrue(len(self.Checker.hsNodes)>0)
	def test_hasTypes(self):
		"all maya scenes should at least one type"
		self.assertTrue(len(self.Checker.hsTypes)>0)
	def test_hasIssues(self):
		""
		self.assertTrue(len(self.Checker.hsTypes)>0)


# #############################################################

if __name__ == "__main__":
	try:
		unittest.main()
	except:
		print sys.exc_info()
		print "I love Maya"
		pass


# ################### eof ###
