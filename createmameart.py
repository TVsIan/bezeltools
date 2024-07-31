import sys
import getopt
import os
import wand
import textwrap
import shutil
from wand.image import Image
from wand.color import Color
from os.path import isfile, join, splitext, exists
from zipfile import ZipFile
from tkinter import filedialog

def main(argv):
	# Set defaults
	filePath = join(os.getcwd(), 'bezels')
	skipMode = False
	debugMode = False
	verbose = False

	# Command Line options
	# v = verbose, d = debug, p = file path
	try:
		opts, args = getopt.getopt(argv, '?vsdp:u', ['help', 'skip', 'debug', 'verbose','path=','ui'])
	except getopt.GetoptError:
		print('Invalid command line option. Use -? or --help to see available options.')
		sys.exit()
	for opt, arg in opts:
		if opt in ['-v', '--verbose']:
			verbose = True
			print('Verbose mode enabled.')
		if opt in ['-s', '--skip']:
			skipMode = True
			if verbose:
				print('Skip existing enabled.')
		if opt in ['-d', '--debug']:
			debugMode = True
			if verbose:
				print('Debug mode enabled.')
		if opt in ['-u', '--ui']:
			scriptDir = os.path.dirname(os.path.abspath(sys.argv[0]))
			filePath = filedialog.askdirectory(initialdir=scriptDir)
			if not exists(filePath):
				print('Cancelled or bad path selected.')
				sys.exit()
		elif opt in ['-p', '--path']:
			if exists(arg):
				filePath = arg
			elif exists(join(os.getcwd(), arg)):
				filePath = join(os.getcwd(), arg)
			else:
				print('Path {} does not exist!'.format(arg))
				sys.exit()
			if verbose:
				print('File path set to {}'.format(filePath))		
		elif opt in ['-?', '--help']:
			print('Available command line options:')
			print('-?; --help:                   Shows this information')
			print('-v; --verbose:                Shows additional logging information when running')
			print('-s; --skip:                   Skip files with existing info')
			print('-d; --debug:                  Saves alpha mask images of failed bezels to a Debug folder')			
			print('-p [folder]; --path [folder]: Set the folder of bezels to process. This can be a subfolder or a full path')
			print('-u; --ui:							 Use folder selection UI')
			print('                              If not specified, the default is {}'.format(filePath))
			sys.exit()


	rawFileList = [f for f in os.listdir(filePath) if isfile(join(filePath, f))]
	fileList = []
	for f in rawFileList:
		if f.endswith('.png') and f != 'alphaMask.png':
			fileList.append(f)
	debugPath = join(filePath, 'Debug')
	fileCount = len(fileList)
	currentFile = 0
	pngCount = 0
	bezelCount = 0
	skipCount = 0

	print('Starting Process...')

	for f in fileList:
		currentFile += 1
		print('Processing {} (File {}/{})... '.format(textwrap.shorten(f, width=30, placeholder='...').ljust(30), str(currentFile).rjust(4, '0'), str(fileCount).rjust(4, '0')), end='', flush=True)
		pngCount += 1
		infoCreated = False
		skippedFile = False
		alphaError = False
		if (exists(join(filePath, splitext(f)[0] + '.zip')) or exists(join(filePath, splitext(f)[0] + '.lay'))) and skipMode:
			skipCount += 1
			skippedFile = True
		else:
			with Image(filename=join(filePath, f)) as bezel:
				bezelWidth = bezel.width
				bezelHeight = bezel.height
				if verbose:
					print('\nExtracting alpha mask from {}'.format(f))
				with bezel.clone() as alphaMask:
					alphaMask.alpha_channel = 'extract'
					alphaMask.negate()
					alphaMask.auto_threshold(method='triangle')
					if verbose:
						print('Saving temp file')
					alphaMask.save(filename=join(filePath, "alphaMask.png"))
			with Image(filename=join(filePath, "alphaMask.png")).clone() as alphaDetect:
				objects = alphaDetect.connected_components(connectivity=8)
				for cc_obj in objects:
					# We want a white box of at least 320x200.
					if cc_obj.mean_color == Color('gray(255)') and cc_obj.width >= 320 and cc_obj.height >= 200:
						if infoCreated:
							if verbose:
								print('Multiple transparent areas found, keeping the first one.')
							if debugMode:
								if not exists(debugPath):
									os.makedirs(debugPath)
								shutil.copy2(join(filePath, 'alphaMask.png'), join(debugPath, f))
								if verbose:
									print('Debug copy of alpha mask saved to {}'.format(join(debugPath, f)))
							alphaError = True
						else:
							if verbose:
								print('Found transparent area at {} with size {}'.format(cc_obj.offset, cc_obj.size))
							infoFilename = splitext(f)[0] + '.lay'
							infoFile = open(join(filePath, infoFilename), "w")
							infoFile.write('<?xml version="1.0"?>\n')
							infoFile.write(f'<!-- {splitext(f)[0]}.lay -->\n')
							infoFile.write('\n')
							infoFile.write('<mamelayout version="2">\n')
							infoFile.write('\t<element name="bezel">\n')
							infoFile.write(f'\t\t<image file="{splitext(f)[0]}.png" />\n')
							infoFile.write('\t</element>\n')
							infoFile.write('\t<view name="Upright Artwork">\n')
							infoFile.write('\t\t<screen index="0">\n')
							infoFile.write(f'\t\t\t<bounds x="{cc_obj.left}" y="{cc_obj.top}" width="{cc_obj.width}" height="{cc_obj.height}" />\n')
							infoFile.write('\t\t</screen>\n')
							infoFile.write('\t\t<element ref="bezel">\n')
							infoFile.write(f'\t\t\t<bounds x="0" y="0" width="{bezelWidth}" height="{bezelHeight}" />\n')
							infoFile.write('\t\t</element>\n')
							infoFile.write('\t</view>\n')
							infoFile.write('</mamelayout>\n')
							infoFile.write('\n')
							infoFile.write('<!-- Created by Bezel Tools script - https://github.com/TVsIan/bezeltools -->\n')
							infoFile.close()
							if verbose:
								print('Created {} for image {}'.format(infoFilename, f))
							infoCreated = True
							with ZipFile(join(filePath, splitext(f)[0] + '.zip'), 'w') as mameArtFile:
								mameArtFile.write(join(filePath, splitext(f)[0] + '.png'), splitext(f)[0] + '.png')
								mameArtFile.write(join(filePath, splitext(f)[0] + '.lay'), splitext(f)[0] + '.lay')
			if infoCreated:
				bezelCount += 1
				print('Done! Created .lay file and zipped.')
			elif skippedFile:
				print('Skipped! .lay file already exists.')
			elif alphaError:
				if debugMode:
					print('Done with Errors! .lay file created, but multiple transparent areas found. Alpha mask saved.')
				else:
					print('Done with Errors! .lay file created, but multiple transparent areas found.')
			else:
				print('Error! No .lay file created, no transparent area detected.')
				if debugMode:
					if not exists(debugPath):
						os.makedirs(debugPath)
					shutil.copy2(join(filePath, 'alphaMask.png'), join(debugPath, f))
					if verbose:
						print('Debug copy of alpha mask saved to {}'.format(join(debugPath, f)))

	print('Processing completed!')
	print('{} png files found, {} lay files written, {} files skipped.'.format(pngCount, bezelCount, skipCount))
	if os.path.exists(join(filePath, "alphaMask.png")):
		os.remove(join(filePath, "alphaMask.png"))
		if verbose:
			print('Temp file deleted')

if __name__ == "__main__":
   main(sys.argv[1:])