MayaVisualizerTools
===================

Python modules, Mel scripts, and related data to help make Caustic Visualizer for Maya even better.

Caustic Visualizer is a interactive raytraced 3D rendering tool from Imagination Technologies that extends Autodesk® Maya® and Autodesk® 3Ds Max®. You can find out more about it and even get a trial edition at http://www.caustic.com

The scripts here are public, open, and NOT part of the standard Visualizer release -- they're provided to help users be even more awesome.

Current Contents
----------------

*	**Caustic Concierge** (Python) is a one-button scene-prep tool -- load or create any scene, and have the Concierge prep all the settings to ensure good out-of-the-box results with Caustic Visualizer: IBL
			settings, linear color workflow, proper shadow setups, etc. (Python)

*	**CVSettingsManager** provides Maya _presets_ for the Caustic Visualizer viewport -- you can quickly jump between different setups depending on whether you want fast flipbooks, WYSIWYG matching to the 		Batch Renderer, etc. It also provides easy shortcuts for copyng values bwteen the two render contexts and shortcuts to the settings windows. (Python)

*   **ShadowPanel** provides a single-dialog panel for managing all the shadows and key lighting properties in your scene. (Python)

![Settings Manager Panel](http://farm8.staticflickr.com/7373/9194352959_bf2fff30d8_o.jpg "Settings Manager")

*	**CausticVisualizer_IBL_Setup** makes sure that your mental ray stringOptions are up to date. _This functionality is also included in the Caustic Concierge._ The script here is exactly the
		one mentioned in recent Caustic forums posts and in this tutorial video: https://vimeo.com/68349810 (Mel)

*	**MatchAttr** is a tiny Mel-script-editor utility that's useful when hunting-down specific attributes on a Maya node -- it matches their names against a regex (Mel)

Installation
------------

You can download & install these tools with or without a (free) GitHub account -- though
with an account is easier!

1. Clone the repo or download and unpack the ZIP file to your desired location
1. Open the Maya file `open_me_to_install.ma` & then restart Maya -- Maya will do the rest for you

Of course, if you like the Old School Ways, just copy the .mel and .py files to your existing Maya script locations. If you use the New Way, then anytime you pull updates into the same directory, they'll be available instantly in Maya, no further installation required.

Enjoy, and please feel free to comment, share, and especially contribute here on GitHub.

kb, 2 July 2013
