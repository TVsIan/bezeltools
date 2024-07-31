# Bezel Tools

This is a set of scripts to assist with Batocera and MAME bezel set creation.

## Important Note:
These scripts may move, delete, or overwrite files. It is recommended you run them on a copy of your pngs or completed bezels and **not** on the original folder.

## Creating Clones:
If you are planning on creating bezels and cloning them (more for Batocera, MAME will automatically use parent art for clones), it is faster to run createinfos.py before mameclonebezels.py. createinfos has a longer processing time per .png, mameclonebezels takes some time to load and process the xml, but runs very quickly once loaded.

## Requirements:
The scripts run well in a virtual environment. The system needs to have ImageMagick installed, and Wand is the only additional module that will need to be installed in the virtual environment.

## createinfos.py

This script will scan a folder of png files for transparent areas, and create matching .info files to be used with Retroarch or MAME in Batocera.
For best results, make sure the image has one single transparent display area. The script will use the closest rectangular area for the viewport.

### Options:
There are several command line options:

`-?` or `--help`: Displays command line information.  
`-v` or `--verbose`: Displays detailed information when running, useful for debugging.  
`-s` or `--skip`: Will skip files that already have a matching .info, otherwise it will be regenerated.  
`-d` or `--debug`: If a file has problems detecting the transparency, this will save the alpha mask as a black & white image to the Debug subfolder of the folder it is processing. This usually happens if there is no transparency, it's too small (320x200 is the minimum size the script is looking for), or it has more than one area (such as a Nintendo DS bezel). The file will have the same name as the original .png, making it easier to find which images need a manual info or editing.  
`-o` or `--opacity`: Sets the opacity in generated bezels. The default is 0.7, the value can be up to 1 (totally opaque) but must be higher than 0 (totally transparent). This only applies to the image, and the transparency will only be seen if the art overlaps the gameplay area.  
`-u` or `--ui`: Shows a UI for folder selection. 
`-p` or `--path`: Sets the path to work from. The default is a subfolder named `bezels` in whatever folder the script is in - for example, if you have the script in `c:\bezeltools`, the default folder is `c:\bezeltools\bezels`. You can use either a full path or a subfolder name. 

## createmameart.py

This script will scan a folder of png files for transparent areas, and create matching .lay files, then zip them together. The resulting zip files can be used as MAME artwork.
For best results, make sure the image has one single transparent display area. The script will use the closest rectangular area for the viewport.

### Options:
There are several command line options:

`-?` or `--help`: Displays command line information.  
`-v` or `--verbose`: Displays detailed information when running, useful for debugging.  
`-s` or `--skip`: Will skip files that already have a matching .info, otherwise it will be regenerated.  
`-d` or `--debug`: If a file has problems detecting the transparency, this will save the alpha mask as a black & white image to the Debug subfolder of the folder it is processing. This usually happens if there is no transparency, it's too small (320x200 is the minimum size the script is looking for), or it has more than one area (such as a Nintendo DS bezel). The file will have the same name as the original .png, making it easier to find which images need a manual info or editing.  
`-u` or `--ui`: Shows a UI for folder selection. 
`-p` or `--path`: Sets the path to work from. The default is a subfolder named `bezels` in whatever folder the script is in - for example, if you have the script in `c:\bezeltools`, the default folder is `c:\bezeltools\bezels`. You can use either a full path or a subfolder name. 

## mameclonebezels.py

This script will load a list of MAME parent and clone ROMs from an XML file. It will then scan a folder of .png/.info files in order to populate it for all clones.

If a parent file is found, it will be copied to all clones that don't have their own art. If a clone file is found without a parent, it will be copied to the parent and all other clones without art. 

### Options:
There are several command line options:

`-?` or `--help`: Displays command line information.  
`-v` or `--verbose`: Displays detailed information when running, useful for debugging.  
`-m` or `--move`: Moves files that do not match a MAME ROM name to the Unknown subfolder of the folder it is processing. If the file already exists in Unknown, it will be left alone.  
`-d` or `--delete`: Deletes files that do not match a MAME ROM name. **This is a destructive operation**, be careful not to use it on original folders.  
`-p` or `--path`: Sets the path to work from. The default is a subfolder named `bezels` in whatever folder the script is in - for example, if you have the script in `c:\bezeltools`, the default folder is `c:\bezeltools\bezels`. You can use either a full path or a subfolder name. 
`-x` or `--xml`: Sets the name of the xml file to read from. The default is a file named `mame.xml` in the current folder. You can provide a full path, or just a filename for the current folder.  

### Generating the XML
MAME can create it's own XML data files. From a command line, run `mame -listxml > mame.xml` to create a file called mame.xml in your MAME folder. Copy that to the folder with the script, or use the `-x` command line option with the full path. The generation will take a few minutes.

### Notes
The script will only process .png, .info, .lay, and .zip files, and other files in the folder will be skipped over.
