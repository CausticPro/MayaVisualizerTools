"""
Find node types in shading networks
"""

import maya
import unittest

class SupportChecker(object):
	# static whitelist for now
	WhiteList = {
		'shadingEngine':	'Ok',
		'animCurveTA':	'Ok',
		'animCurveTL':	'Ok',
		'animCurveTU':	'Ok',
		'blendColors':	'Ok',
		'bump2d':	'Ok',
		'bump3d':	'Ok',
		'cloud':	'Ok',
		'dgs_material':	'Ok',
		'dielectric_material':	'Ok',
		'displayLayer':	'Ok',
		'displayLayerManager':	'Ok',
		'file':	'Ok',
		'gammaCorrect':	'Ok',
		'lambert':	'Ok',
		'layeredTexture':	'Ok',
		'luminance':	'Ok',
		'mentalrayLightProfile':	'Ok',
		'mentalrayTexture':	'Ok',
		'mi_car_paint_phen':	'Ok',
		'mi_car_paint_phen_x':	'Ok',
		'mi_car_paint_phen_x_passes':	'Ok',
		'mi_metallic_paint_x':	'no flakes',
		'mi_metallic_paint_x_passes':	'Ok',
		'mia_exposure_photographic':	'Ok',
		'mia_exposure_simple':	'Ok',
		'mia_light_surface':	'Ok',
		'mia_material':	'Ok',
		'mia_material_x':	'bump mapping supported',
		'mia_material_x_passes':	'bump mapping supported',
		'mia_photometric_light':	'Ok',
		'mib_amb_occlusion':	'Ok',
		'mib_color_mix':	'Ok',
		'mib_dielectric':	'Ok',
		'mib_illum_blinn':	'Ok',
		'mib_illum_cooktorr':	'Ok',
		'mib_illum_phong':	'Ok',
		'mib_illum_ward':	'Ok',
		'mib_opacity':	'Ok',
		'mib_twosided':	'Ok',
		'mip_cameramap':	'Ok',
		'mip_grayball':	'Ok',
		'mip_matteshadow':	'Ok',
		'mip_mirrorball':	'Ok',
		'mip_rayswitch':	'Ok',
		'mip_rayswitch_advanced':	'Ok',
		'misss_fast_simple_maya':	'Ok',
		'misss_fast_skin_maya':	'Ok',
		'misss_set_normal':	'Ok',
		'misss_skin_specular':	'Ok',
		'mute':	'Ok',
		'particleCloud':	'Ok',
		'place2dTexture':	'Ok',
		'place3dTexture':	'Ok',
		'plusMinusAverage':	'Ok',
		'ramp':	'Ok',
		'remapColor':	'Ok',
		'remapHsv':	'Ok',
		'remapValue':	'Ok',
		'renderLayer':	'Ok',
		'renderLayerManager':	'Ok',
		'reverse':	'Ok',
		'rgbToHsv':	'Ok',
		'samplerInfo':	'Ok',
		'shadingEngine':	'Ok',
		'surfaceShader':	'Ok',
		'transform':	'Ok',
		'volumeNoise':	'Ok'
	}
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
			if not SupportChecker.WhiteList.has_key(t):
				self.issues[t] = 'Unknown Node Type'
			elif SupportChecker.WhiteList[t] != 'Ok':
				self.issues[t] = SupportChecker.WhiteList[t]
	def report(self):
		print "Discovered these node types:"
		for t in sorted(self.hsTypes.keys()):
			print "%s: %d" % (t,len(self.hsTypes[t]))
		if len(self.issues)>0:
			print "%d node types with *potential* issues:" % (len(self.issues))
			for t in self.issues:
				print '\t%s (%d nodes):\t"%s"' % (t,len(self.hsTypes[t]),self.issues[t])
				for n in sorted(self.hsTypes[t]):
					print '\t\t\t%s' % (n)


def check():
	# basic call
	SC = SupportChecker()
	SC.report()


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


# #############################################################

if __name__ == "__main__":
	try:
		unittest.main()
	except:
		pass


# ################### eof ###