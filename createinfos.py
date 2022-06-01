import sys
import getopt
import os
import wand
import textwrap
import shutil
from wand.image import Image
from wand.color import Color
from os.path import isfile, join, splitext, exists

def main(argv):
	# Set defaults
	filePath = join(os.getcwd(), 'bezels')
	skipMode = True
	debugMode = False
	verbose = False

	# Command Line options
	# v = verbose, d = debug, p = file path
	try:
		opts, args = getopt.getopt(argv, '?vsdp:', ['help', 'verbose','path='])
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
			print('-?; --help:                   Shows this information.')
			print('-v; --verbose:                Shows additional logging information when running.')
			print('-s; --skip:                   Skip files with existing info')
			print('-d; --debug:                  Saves alpha mask images of failed bezels to a Debug folder')
			print('-p [folder]; --path [folder]: Set the folder of bezels to process. This can be a subfolder or a full path.')
			print('                              If not specified, the default is {}'.format(filePath))
			sys.exit()


	fileList = [f for f in os.listdir(filePath) if isfile(join(filePath, f))]
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
		if f.endswith('.png') and f != 'alphaMask.png':
			pngCount += 1
			infoCreated = False
			skippedFile = False
			alphaError = False
			if exists(join(filePath, splitext(f)[0] + '.info')) and skipMode:
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
						alphaMask.color_threshold(start='black', stop='black')
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
								infoFilename = splitext(f)[0] + '.info'
								infoFile = open(join(filePath, infoFilename), "w")
								infoFile.write('{\n')
								infoFile.write(' "width":{},\n'.format(bezelWidth))
								infoFile.write(' "height":{},\n'.format(bezelHeight))
								infoFile.write(' "top":{},\n'.format(cc_obj.top))
								infoFile.write(' "left":{},\n'.format(cc_obj.left))
								infoFile.write(' "bottom":{},\n'.format(bezelHeight - (cc_obj.top + cc_obj.height)))
								infoFile.write(' "right":{},\n'.format(bezelWidth - (cc_obj.left + cc_obj.width)))
								infoFile.write(' "opacity":1.0,\n')
								infoFile.write(' "messagex":0.22,\n')
								infoFile.write(' "messagey":0.12,\n')
								infoFile.write('}')
								infoFile.close()
								if verbose:
									print('Created {} for image {}'.format(infoFilename, f))
								infoCreated = True
			if infoCreated:
				bezelCount += 1
				print('Done! Created .info file.')
			elif skippedFile:
				print('Skipped! .info file already exists.')
			elif alphaError:
				if debugMode:
					print('Done with Errors! .info file created, but multiple transparent areas found. Alpha mask saved.')
				else:
					print('Done with Errors! .info file created, but multiple transparent areas found.')
			else:
				print('Error! No .info file created, no transparent area detected.')
				if debugMode:
					if not exists(debugPath):
						os.makedirs(debugPath)
					shutil.copy2(join(filePath, 'alphaMask.png'), join(debugPath, f))
					if verbose:
						print('Debug copy of alpha mask saved to {}'.format(join(debugPath, f)))
		else:
			print('Skipped! Not a png file.')
			skipCount += 1

	print('Processing completed!')
	print('{} png files found, {} info files written, {} files skipped.'.format(pngCount, bezelCount, skipCount))
	if os.path.exists(join(filePath, "alphaMask.png")):
		os.remove(join(filePath, "alphaMask.png"))
		if verbose:
			print('Temp file deleted')

if __name__ == "__main__":
   main(sys.argv[1:])