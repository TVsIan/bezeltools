import sys
import getopt
import os
import shutil
import textwrap
from os.path import isfile, join, splitext, exists
from xml.dom import minidom
from itertools import chain

def main(argv):
	# Settings
	filePath = join(os.getcwd(), 'bezels')
	xmlFile = join(os.getcwd(), 'mame.xml')
	verbose = False
	deleteUnknown = False
	moveUnknown = False

	# Command Line options
	# v = verbose, m = move unknown, d = delete unknown, p = file path, x = xml file
	try:
		opts, args = getopt.getopt(argv, '?vmdp:x:', ['help', 'verbose', 'move', 'delete', 'path=','xml='])
	except getopt.GetoptError:
		print('Invalid command line option. Use -? or --help to see available options.')
		sys.exit()
	for opt, arg in opts:
		if opt in ['-v', '--verbose']:
			verbose = True
			print('Verbose mode enabled.')
		elif opt in ['-m', '--move']:
			moveUnknown = True
			if verbose:
				print('Will move unmatched files')
		elif opt in ['-d', '--delete']:
			deleteUnknown = True
			if verbose:
				print('Will delete unmatched files')
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
		elif opt in ['-x', '--xml']:
			if exists(arg):
				xmlFile = arg
			elif exists(join(os.getcwd(), arg)):
				xmlFile = join(os.getcwd(), arg)
			elif exists(join(filePath, arg)):
				xmlFile = join(filePath, arg)
			else:
				print('XML file {} not found!'.format(arg))
				sys.exit()
			if verbose:
				print('XML File set to {}'.format(xmlFile))
		elif opt in ['-?', '--help']:
			print('Available command line options:')
			print('-?; --help:                   Shows this information.')
			print('-v; --verbose:                Shows additional logging information when running.')
			print('-m; --move:                   Will move unmatched png and info files into an Unknown folder under the path.')
			print('                              If the file already exists in Unknown, it will be ignored.')
			print('-d; --delete:                 Unmatched png and info files will be deleted.')
			print('-p [folder]; --path [folder]: Set the folder of bezels to process. This can be a subfolder or a full path.')
			print('                              If not specified, the default is {}'.format(filePath))
			print('-x [file]; --xml [file]:      Set the MAME XML file to parse. This can be a full path or a file in the current folder.')
			print('                              If not specified, the default is {}'.format(xmlFile))
			sys.exit()
	# Initialize
	fileList = [f for f in os.listdir(filePath) if isfile(join(filePath, f))]
	fileCount = len(fileList)
	unknownPath = join(filePath, 'Unknown')
	currentFile = 0
	processedCount = 0
	skippedCount = 0
	copyCount = 0
	copyTotal = 0
	deletedCount = 0
	movedCount = 0
	mameParents = []
	mameClones = []


	print('Starting Process...')
	print('Please wait, loading data may take some time.')

	# Load XML
	print('Loading XML file...                                         ', end='', flush=True)
	xmlData = minidom.parse(xmlFile)
	print('Done!')

	# Read XML file, check <machine> tag for name and parent
	print('Reading parent/clone sets...                                ', end='', flush=True)
	machineInfo = xmlData.getElementsByTagName('machine')
	for machine in machineInfo:
		if 'cloneof' in machine.attributes:
			# ROM is a clone, store parent & clone name
			if verbose:
				if len(mameParents) == 0:
					print('\n')
				print('Machine found: {}, clone of {}'.format(machine.attributes['name'].value, machine.attributes['cloneof'].value))
			machineName = machine.getAttribute('name')
			machineParent = machine.getAttribute('cloneof')
		else:
			# ROM is a parent, store name as parent only
			if verbose:
				if len(mameParents) == 0:
					print('\n')
				print('Machine found: {} (Parent Set)'.format(machine.attributes['name'].value))
			machineParent = machine.getAttribute('name')
			machineName = ''

		# Add parent if it doesn't exist
		# Add [parent, clone] if clone and doesn't exist
		if machineParent not in mameParents:
			mameParents.append(machineParent)
		if machineName != '':
			if [machineParent, machineName] not in mameClones:
				mameClones.append([machineParent, machineName])

	print('Done! Found {} parent sets and {} clone sets.'.format(len(mameParents), len(mameClones)))

	# Check files against the XML data
	for f in fileList:
		currentFile += 1
		if splitext(f)[1] in ['.png', '.info', '.lay', '.zip']:
			copyCount = 0
			deletedFile = False
			movedFile = False
			skippedFile = False
			print('Checking {} (File {}/{})... '.format(textwrap.shorten(f, width=30, placeholder='...').ljust(30), str(currentFile).rjust(4, '0'), str(fileCount).rjust(4, '0')), end='', flush=True)
			setName = splitext(f)[0]
			parentSet = setName in mameParents
			clonesExist = setName in chain(*mameClones)
			if parentSet and not clonesExist:
				if verbose:
					print('\n{} is a parent set with no clones.'.format(setName))
			elif parentSet and clonesExist:
				if verbose:
					print('\n{} is a parent set with clones, checking and copying as needed.'.format(setName))
				for clone in mameClones:
					if clone[0] == setName:
						targetFile = clone[1] + splitext(f)[1]
						if not exists(join(filePath, targetFile)):
							shutil.copy2(join(filePath, f), join(filePath, targetFile))
							if verbose:
								print('Copied {} to {}'.format(f, targetFile))
							copyCount += 1
			elif not parentSet and clonesExist:
				if verbose:
					print('\n{} is a clone set, checking and copying if parent does not exist.'.format(setName))
				parentSet = ''
				for clone in mameClones:
					if clone[1] == setName:
						parentSet = clone[0]
						targetFile = parentSet + splitext(f)[1]
						if not exists(join(filePath, targetFile)):
							shutil.copy2(join(filePath, f), join(filePath, targetFile))
							if verbose:
								print('Copied {} to {}'.format(f, targetFile))
							copyCount += 1
						else:
							# If there IS a parent set bezel, assume we want to use that for any missing clones and not this one.
							parentSet = ''
				if parentSet != '':
					for clone in mameClones:
						if clone[0] == parentSet:
							targetFile = clone[1] + splitext(f)[1]
							if not exists(join(filePath, targetFile)):
								shutil.copy2(join(filePath, f), join(filePath, targetFile))
								if verbose:
									print('Copied {} to {}'.format(f, targetFile))
								copyCount += 1
			elif not parentSet and not clonesExist:
				if verbose:
					print('\n{} does not match any known sets.'.format(setName))
				if deleteUnknown:
					os.remove(join(filePath, f))
					if verbose:
						print("File deleted.")
					deletedFile = True
					deletedCount += 1
				elif moveUnknown:
					if not exists(unknownPath):
						os.makedirs(unknownPath)
					if not exists(join(unknownPath, f)):
						os.rename(join(filePath, f), join(unknownPath, f))
						if verbose:
							print("File moved to {}".format(join(unknownPath, f)))
						movedFile = True
						movedCount += 1
					else:
						if verbose:
							print('File exists in backup path, not moved.')
						skippedFile = True
						skippedCount += 1
						processedCount -= 1
			processedCount += 1
			if copyCount > 0:
				print('Done! {} copy/copies made.'.format(copyCount))
				copyTotal += copyCount
			elif movedFile:
				print('Done! No match, moved to Unknown folder.')
			elif deletedFile:
				print('Done! No match, deleted.')
			elif skippedFile:
				print('Done! No match, already exists in Unknown, no actions taken.')
			else:
				print('Done! No actions taken.')
		else:
			print('Skipping {} - Not a decoration (File {}/{})'.format(textwrap.shorten(f, width=30, placeholder='...').ljust(30), str(currentFile).rjust(4, '0'), str(fileCount).rjust(4, '0')))
			skippedCount += 1
	print('Processing completed!')
	print('{} files processed, {} copies made, {} files moved, {} files deleted, {} files skipped.'.format(processedCount, copyTotal, movedCount, deletedCount, skippedCount))

if __name__ == "__main__":
   main(sys.argv[1:])