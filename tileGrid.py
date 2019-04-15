'''
Tiling script for CellenONE FL images to an well-plate format (96,384)
@Ikuo Obataya (obataya@qd-japan.com)

Requirements
Python 3.x, pillow

Usage
Specify folder contains image files. The folder name should end widh .RUN
You can specify parameters of format, target index by options. Check by -h or --help
'''
import os
import argparse
import sys
import re
import glob
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
parser = argparse.ArgumentParser(description="Tiles images by defined format")
parser.add_argument('arg_dir',type=str,help="Path of directory contains images")
parser.add_argument('-f','--format',type=str,default='96',help="Format of well plate: 96 or 384")
parser.add_argument('-s','--start',type=int,default=1,help="Start index to tile")
parser.add_argument('-e','--end',type=int,help='End index to tile')
parser.add_argument('-c','--channel',type=int,default=1,help="Number of channels to tile")
parser.add_argument('-a', '--export_all',action='store_true',help="Export all image of isolation")
parser.add_argument('-d','--debug',action='store_true',help="Flag for debug-mode running without saving")
parser.add_argument('-b','--background',type=str,help='File path of background image to overlay')
parser.add_argument('-w','--width_to',type=int,default=400,help='Resize width of each images')
parser.add_argument('-t','--text_color',type=int,default=255,help='Text color by grey scale')
args = parser.parse_args()

# Check directory
working_dir = os.getcwd()
if os.path.exists(args.arg_dir):
    working_dir = args.arg_dir
else:
    print("Not found: %s" % args.arg_dir)
    exit()
if args.debug:
    print("Working directory: %s" % working_dir)

# Set format
wellNameFormat = "R%02d_C%02d"
m = re.match(r"(\d+)x(\d+)",args.format)
if not m:
    print("Invalid format definition (%s). Set as 10x10" % args.format)
    exit()
targetCols=int(m.group(1))
targetRows=int(m.group(2))
wellNameFormat = "R%02d_C%02d"
wRowName = [i for i in range(1,targetRows+1)]
wColName = [i for i in range(1,targetCols+1)]

# Make directory for well images
imgdir_path = os.path.join(working_dir,"grid_img")
if args.export_all==True and not os.path.exists(imgdir_path):
    os.makedirs(imgdir_path)
    print("grid_img directory created.")

# Read *Run.png files and check numbers
filenames = sorted(glob.glob(os.path.join(working_dir,"*Run.png")))
imgCount = len(filenames)
channels = args.channel
imgSetCount = imgCount/channels
if args.debug:
    print("%d png files read. (%d image sets)" % (imgCount,imgSetCount))
targetStart = args.start
targetEnd = imgSetCount if args.end == None else int(args.end)
targetCount = targetEnd-targetStart+1
if args.debug:
    print('Tiling target index is from %d to %d' % (targetStart,targetEnd))
if imgSetCount<targetCount:
    print('! Number of found images (%d) is less than %d' % (imgSetCount,targetCount))
    exit()

# Get the first image
tmpImage = Image.open(filenames[0],'r')
(width,height) = (tmpImage.width,tmpImage.height)
widthTo = args.width_to
heightTo = int(height*widthTo/width)
print("Original image size (%s,%s)" % (width,height))

# Tile for grid
(mX,mY) = (4,2)  # margin
font = ImageFont.truetype("CenturyGothic.ttf", int(heightTo/4))
tilesCanvas = Image.new('RGB',((widthTo+mX)*targetCols,(heightTo+mY)*channels*targetRows),(255,255,255))
tilesDraw = ImageDraw.Draw(tilesCanvas)
if not args.background == None and os.path.exists(args.background):
    tilesCanvas.paste(Image.open(args.background,'r'),(0,0))

print("Format %s, (cols,rows)=(%d,%d), channels:%d" % (args.format,targetCols,targetRows,channels))

fileIdx = 0
targetIdx = 1
wellNameLabel = "%s  (%d)"

for row in range(0,targetRows):
    for col in range(0,targetCols):
        tile = Image.new('RGB',(widthTo,heightTo*channels),(0,0,0))
        imDraw = ImageDraw.Draw(tile)
        wellName = wellNameFormat % (wRowName[row],wColName[col])
        (tileX,tileY) = ((widthTo+mX)*col,(heightTo+mY)*row*channels)
        if targetStart<=targetIdx and targetIdx<=targetEnd:
            print('(col,row)=(%d,%d),  (wellName,fileIdx,targetIdx)=(%s,%d,%d)' % (col,row,wellName,fileIdx,targetIdx))
            for ch in range(0,channels):
                original = Image.open(filenames[fileIdx+ch],'r')
                resized = original.resize((widthTo,heightTo))
                tile.paste(resized,(0,heightTo*ch+1))
            fileIdx += channels
            if args.export_all==True:
                wellImagePath = os.path.join(imgdir_path,wellName + ".jpg")
                if args.debug:
                    print("Well image (%s) will be saved." % wellName)
                else:
                    tile.save(wellImagePath,"JPEG")
            if args.debug:
                print("Pasted to whole image at (%d,%d)" % (tileX,tileY))
            else:
                tilesCanvas.paste(tile,(tileX,tileY))
        # write well name after pasted
        tilesDraw.text((tileX+10,tileY+10),wellNameLabel % (wellName,targetIdx),fill=(255,255,255),font=font)
        targetIdx += 1
        if targetIdx > targetEnd:
            break

# Save whole image
tiled_path = os.path.join(working_dir,"_tiled_%03d_%03d.jpg" % (targetStart,targetEnd))
if args.debug:
    print("Whole image will be saved, %s" % tilesCanvas)
else:
    tilesCanvas.save(tiled_path,"JPEG")
    print("Saved as %s" % tiled_path)
