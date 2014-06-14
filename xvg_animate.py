################################################################################################################################################
# IMPORT MODULES
################################################################################################################################################

#import general python tools
import argparse
import operator
from operator import itemgetter
import sys, os, shutil
import os.path
import math

#import python extensions/packages to manipulate arrays
import numpy 				#to manipulate arrays
import scipy 				#mathematical tools and recipesimport MDAnalysis

#import graph building module
import matplotlib as mpl
mpl.use('Agg')
import pylab as plt
import matplotlib.cm as cm			#colours library
import matplotlib.ticker
from matplotlib.ticker import MaxNLocator
from matplotlib.font_manager import FontProperties
fontP=FontProperties()

################################################################################################################################################
# RETRIEVE USER INPUTS
################################################################################################################################################

#create parser
#=============
version_nb="2.0.0"
parser = argparse.ArgumentParser(prog='xvg_animate', usage='', add_help=False, formatter_class=argparse.RawDescriptionHelpFormatter, description=\
'''
**********************************************
v''' + version_nb + '''
author: Jean Helie
git: https://github.com/jhelie/xvg_animate.git
**********************************************

[ Description ]

This script allows to create a time lapse of the plotting of the data contained in .xvg-like file.
It outputs numbered png and svg files that are ready to be concatenated into a movie using your
preferred utility to do so (see note 7).

If the desired movie duration is specified this script will tell you the frame_rate to use to achieve
it with the pngs created (not rocket science but a convenient shortcut:).

[ Notes ]

1. The format of the pictures can be either a single graph or two graphs vertically stacked. This is
   controlled by the --graph option. The script can take several xvg files as inputs:
    -f file1.xvg file2.xvg ... 
   However --graph and -f are independent: the graph(s) can contain data from one or several xvg.
   
   For example the following combinations are possible:
    -1 graph, 1 xvg: a single graph containing data from a single xvg file
    -1 graph, 2 xvg: a single graph containing data from the two specified xvg files	
    -2 graphs, 1 xvg: two vertically stacked graphs containing data from a single xvg file
    -2 graphs, 2 xvg: two vertically stacked graphs containing data from the two specified xvg files
    -etc... 

2. Columns of the xvg file(s) that should be used for plotting are defined for each graphs via 
   the --upper_cols and --lower_cols options.
   In case only one graph is to be plotted, only the --upper_col needs to be specified.
   The format for specifying lines should be:
    'xvg_file_nb:x_column_nb,y1_column_nb,y2_column_nb/xvg_file_nb:x_column_nb,y1_column_nb'
   where the numbering of xvg file is 1-based and that of xvg columns is 0-based. As many y columns
   as contained in the xvg files can be specified.
 
   Examples:
    -1 graph, 1 xvg: --upper_cols 1:0,1,4
    -1 graph, 2 xvg: --upper_cols 1:0,1,4/2:0,1,2,3
    -2 graphs, 1 xvg: --upper_cols 1:0,1,2 --lower_cols 1:0,3,4
    -2 graphs, 2 xvg: --upper_cols 1:0,1,2/2:0,1,2 --lower_cols 1:0,3,4

3. The strings for the axis labels and plot titles of the graphs can be defined in a way similar to
   that explained in note 2 above with the exception that quotation marks must be used. The graphs
   are referred to with numbers with the upper being 1 and the lower one being 2.
   If 2 plots are specified and if the options --xlabel, --ylabel or --title are specified they must
   be defined for both plots - i.e. you either specify it for the two plots or none.

   Example: 
    -2 graphs, 2 xvg: --xlabel "1:x_upper/2:x_lower" --ylabel "1:y_upper/2:y_lower"

4. A text file can be supplied to define the legend and the colour to be used for each line plotted.
   The information in this text file should be placed on single lines with the following format:
    xvg_file_nb,xvg_column_nb,column_name,column_colour
   (xvg_file_nb is 1 based and xvg_column_nb is 0 based and colours can be specified as hexadecimal)
   code or standard matplotlib one letter code). This means that a given column in an xvg file
   will be represented the same way in both the upper and lower graph (if present).
   
   Example:
    xvgfilename1,1,POPC,r
    xvgfilename2,1,POPC,#C0C0C0
    xvgfilename2,2,POPE,#FFFFFF
   
   NB:
    - such a file is automatically produced along with xvg files written by the scripts order_param,
      thickness, cluster_lip, cluster_param.
    - the color can be automatically attributed (using the jet color map) by specifying 'auto' instead
      as a colour code.
    - in case no colour file is supplied the jet colour map will be used to generate colours if there
      are several lines on a plot

5. A confidence interval can be plotted as a shaded area for each line. To define these, the -e option
   can be used to specify which column contains the error associated to another column. The error
   value will be added and substracted to the value of the relevant column and the enclosed area will
   be shaded accordingly. The format should be:
   --error_col xvgfile_nb:col_data1-col_err1,col_data2-col_err2;xvgfile_nb:col_data1-col_err1
   
   Example: 
    --error_cols 1:1-3,2-4/2:1,5

6. Exact boundaries of the plot(s) can be enforced by using the --upper_range option (resp.	
   --lower_range). The range of the x-axis and of the y-axis can be specified or can be determined
   automatically by writing 'auto'. The format to use is as follows (note the use of quotation marks):
    --upper_range "x:x_min,x_max/y:y_min,y_max"
   
   Example:
    --upper_range "x:0,auto/y:-0.5,1"

7. Several utlitily exist to concatenate png into movies, ffmpeg, and avconv are two popular ones.
   Each come with its own set of options but a command similar to the one below should work:
   
   avconv -qscale 0 -r your_frame_rate -i xvg_graph_%05d.png -c:v libx264 -c:a copy xvg_movie.mp4

[ Usage ]
	
Option	      Default  	Description                    
-----------------------------------------------------
-f			: xvg file(s)
-c			: file containing legend and colouring info, see note 4
-o			: name of output folder
--upper_cols		: composition of upper (resp. only) graph, see note 2
--lower_cols		: composition of lower graph, see note 2
--error_cols		: definition of error areas, see note 5
--smooth		: nb of points to use for smoothing (optional)
--offset	 0 	: initial line offset 
--skip		 5 	: move forward X lines for each image
--graph		 1 	: nb of graphs, see note 1

Graphs annotations  
-----------------------------------------------------
--xlabel		: labelling of x axis, see note 3
--ylabel		: labelling of y axis, see note 3
--titles		: labelling of plots, see note 3
--nolegend		: mask lines labels
--thickness [3]		: thickness of lines
--upper_range		: boundaries of the upper plot (optional, see note 6)
--lower_range		: boundaries of the lower plot (optional, see note 6)	

Other options
-----------------------------------------------------
--dpi 		100 	: figure resolution, in dpi
--size 		8,6.2	: figure dimensions 'width,height', in inches
--duration		: show frame rate to use to achieve this duration
--version		: show version number and exit
-h, --help		: show this menu and exit
 
''')

#data options
parser.add_argument('-f', nargs='+', dest='xvg_names', required=True, metavar='file.xvg', help=argparse.SUPPRESS)
parser.add_argument('-c', nargs=1, dest='colour_file', default=['no'], help=argparse.SUPPRESS)
parser.add_argument('-o', nargs=1, dest='output_folder', default=['no'], help=argparse.SUPPRESS)
parser.add_argument('--offset', nargs=1, dest='lines_offset', default=[0], type=int, help=argparse.SUPPRESS)
parser.add_argument('--skip', nargs=1, dest='lines_skip', default=[10], type=int, help=argparse.SUPPRESS)
parser.add_argument('--graph', dest='nb_graphs', default=1, choices=[1,2], type=int, help=argparse.SUPPRESS)
parser.add_argument('--upper_cols', nargs=1, dest='lines_upper', required=True, help=argparse.SUPPRESS)
parser.add_argument('--lower_cols', nargs=1, dest='lines_lower', default=['no'], help=argparse.SUPPRESS)
parser.add_argument('--error_cols', nargs=1, dest='lines_error', default=['no'], help=argparse.SUPPRESS)
parser.add_argument('--smooth', nargs=1, dest='nb_smoothing', default=[0], type=int, help=argparse.SUPPRESS)
#graph options
parser.add_argument('--xlabel', nargs=1, dest='captions_x', default=['1:x axis 1/2:x axis 2'], help=argparse.SUPPRESS)
parser.add_argument('--ylabel', nargs=1, dest='captions_y', default=['1:y axis 1/2:y axis 2'], help=argparse.SUPPRESS)
parser.add_argument('--titles', nargs=1, dest='captions_t', default=['1:title 1/2:title 2'], help=argparse.SUPPRESS)
parser.add_argument('--upper_range', nargs=1, dest='boundaries_upper', default=['x:auto,auto/y:auto,auto'], help=argparse.SUPPRESS)
parser.add_argument('--lower_range', nargs=1, dest='boundaries_lower', default=['x:auto,auto/y:auto,auto'], help=argparse.SUPPRESS)
parser.add_argument('--thickness', nargs=1, dest='lines_thick', default=[3], type=float, help=argparse.SUPPRESS)
parser.add_argument('--nolegend', dest='mask_labels', action='store_true', help=argparse.SUPPRESS)
parser.add_argument('--dpi', nargs=1, dest='fig_dpi', default=[100], type=int, help=argparse.SUPPRESS)
parser.add_argument('--size', nargs=1, dest='fig_size', default=['8,6.2'], help=argparse.SUPPRESS)
#movie option
parser.add_argument('--duration', nargs=1, dest='avconv_duration', default=[0], type=float, help=argparse.SUPPRESS)
#store version
parser.add_argument('--version', action='version', version='%(prog)s v' + version_nb, help=argparse.SUPPRESS)
#deal with help
parser.add_argument('-h','--help', action='help', help=argparse.SUPPRESS)

#store inputs
#============
args=parser.parse_args()
args.colour_file=args.colour_file[0]
args.output_folder=args.output_folder[0]
args.lines_offset=args.lines_offset[0]
args.lines_skip=args.lines_skip[0]
args.lines_upper=args.lines_upper[0]
args.lines_lower=args.lines_lower[0]
args.lines_error=args.lines_error[0]
args.lines_thick=args.lines_thick[0]
args.nb_smoothing=args.nb_smoothing[0]
args.captions_x=args.captions_x[0]
args.captions_y=args.captions_y[0]
args.captions_t=args.captions_t[0]
args.boundaries_upper=args.boundaries_upper[0]
args.boundaries_lower=args.boundaries_lower[0]
args.fig_size=args.fig_size[0]
args.fig_dpi=args.fig_dpi[0]
args.avconv_duration=args.avconv_duration[0]

#debug
print sys.argv
if '-f' in sys.argv:
	print "in"
	sys.exit(0)

#sanity check
#============
for f in args.xvg_names:
	if not os.path.isfile(f):
		print "Error: file " + str(f) + " not found."
		sys.exit(1)
if args.colour_file!="no" and not os.path.isfile(args.colour_file):
	print "Error: file " + str(args.colour_file) + " not found."
	sys.exit(1)
if args.lines_lower=="no" and args.nb_graphs==2:
	print "Error: two graphs specified but --lower_col wasn't specified."
	sys.exit(1)
if args.lines_lower!="no" and args.nb_graphs==1:
	print "Error: --lower_col specified but only one graph specfied."
	sys.exit(1)

#create folders and log file
#===========================
if args.output_folder=="no":
	args.output_folder="xvg_animate_" + args.xvg_names[0][:-4]
if os.path.isdir(args.output_folder):
	print "Error: folder " + str(args.output_folder) + " already exists, choose a different output name via -o."
	sys.exit(1)
else:
	#create folder
	os.mkdir(args.output_folder)
	os.mkdir(args.output_folder + "/png")
	if args.nb_smoothing>1:
		os.mkdir(args.output_folder + "/png_smoothed")
	#create log
	filename_log=os.getcwd() + '/' + str(args.output_folder) + '/xvg_animate.log'
	output_log=open(filename_log, 'w')		
	output_log.write("[xvg_animate v" + str(version_nb) + "]\n")
	output_log.write("\nThis folder and its content were created using the following command:\n\n")
	tmp_log="python xvg_animate.py"
	for c in sys.argv[1:]:
		tmp_log+=" " + c
	output_log.write(tmp_log + "\n")
	output_log.close()
	#copy input files
	for f in args.xvg_names:
		shutil.copy2(f,args.output_folder + "/")
	if args.colour_file!="no":
		shutil.copy2(args.colour_file,args.output_folder + "/")

################################################################################################################################################
# FUNCTIONS
################################################################################################################################################

def error_format(option_name):
	print "Error: the format of the -" +str(option_name) + " option is incorrect, see xvg_animate -h"
	sys.exit(1)
	return
def identify_columns():
	
	graph_columns["upper"]={}
	graph_columns["upper"]["files"]=[]
	graph_columns["upper"]["x axis"]=[]
	graph_columns["upper"]["y axis"]={}
	graph_columns["lower"]={}
	graph_columns["lower"]["files"]=[]
	graph_columns["lower"]["x axis"]=[]
	graph_columns["lower"]["y axis"]={}

	#upper graph
	#===========
	tmp_files=args.lines_upper.split('/')
	if len(tmp_files)>2:
		error_format("u")
	else:
		for f in tmp_files:
			tmp_f=f.split(':')
			if len(tmp_f)!=2:
				error_format("u")
			else:
				#retrieve xvg file referred to
				f_index=int(tmp_f[0])
				graph_columns["upper"]["files"].append(f_index)
				graph_columns["upper"]["y axis"][f_index]=[]
				
				#retrieve col of the x axis
				tmp_xvg_c=tmp_f[1].split(',')				
				graph_columns["upper"]["x axis"]=[f_index, int(tmp_xvg_c[0])]		#we overwrite whatever was there before => the x axis must be the same within a graph anyhow
				xvg_columns[f_index].append(int(tmp_xvg_c[0]))
				if int(tmp_xvg_c[0]) not in xvg_data[f_index].keys():
					xvg_data[f_index][int(tmp_xvg_c[0])]=[]
				
				#retrieve cols of the y axis
				for c in tmp_xvg_c[1:]:
					graph_columns["upper"]["y axis"][f_index].append(int(c))
					xvg_columns[f_index].append(int(c))
					if int(c) not in xvg_data[f_index].keys():
						xvg_data[f_index][int(c)]=[]
	
	#lower graph
	#===========
	if args.nb_graphs==2:
		tmp_files=args.lines_lower.split('/')
		if len(tmp_files)>2:
			error_format("l")
		else:
			for f in tmp_files:
				tmp_f=f.split(':')
				if len(tmp_f)!=2:
					error_format("u")
				else:
					#retrieve xvg file referred to
					f_index=int(tmp_f[0])
					graph_columns["lower"]["files"].append(f_index)
					graph_columns["lower"]["y axis"][f_index]=[]
					
					#retrieve col of the x axis
					tmp_xvg_c=tmp_f[1].split(',')
					graph_columns["lower"]["x axis"]=[f_index, int(tmp_xvg_c[0])]		#we overwrite whatever was there before => the x axis must be the same within a graph anyhow
					xvg_columns[f_index].append(int(tmp_xvg_c[0]))
					if int(tmp_xvg_c[0]) not in xvg_data[f_index].keys():
						xvg_data[f_index][int(tmp_xvg_c[0])]=[]
					
					#retrieve cols of the y axis
					for c in tmp_xvg_c[1:]:
						graph_columns["lower"]["y axis"][f_index].append(int(c))
						xvg_columns[f_index].append(int(c))
						if int(c) not in xvg_data[f_index].keys():
							xvg_data[f_index][int(c)]=[]
			
	#errors
	#======
	if args.lines_error!="no":
		#create pair assocations
		tmp_files=args.lines_error.split('/')
		if len(tmp_files)>2:
			error_format("e")
		else:
			for f in tmp_files:
				tmp_f=f.split(':')
				if len(tmp_f)!=2:
					error_format("e")
				else:
					f_index=int(tmp_f[0])
					tmp=tmp_f[1].split(',')
					for pair in tmp:
						xvg_error[f_index][int(pair.split('-')[0])]=int(pair.split('-')[1])
						
		#add error columns to data to read
		for f_index in xvg_files:
			for c_index in xvg_error[f_index].keys():
				xvg_columns[f_index].append(xvg_error[f_index][c_index])
				if xvg_error[f_index][c_index] not in xvg_data[f_index].keys():
					xvg_data[f_index][xvg_error[f_index][c_index]]=[]

	
	#clean up
	#========
	for f_index in xvg_files:
		xvg_columns[f_index]=list(numpy.unique(xvg_columns[f_index]))
		
	return
def read_data():
	
	#read data from file
	#===================
	for f_index in xvg_files:
		print " -reading file " + xvg_names[f_index] + "..."
		#open file
		with open(xvg_names[f_index]) as f:
			lines = f.readlines()
		lines_nb=len(lines)
		for l_index in range(0,lines_nb):
			#read line
			line=lines[l_index]		
			
			#process line if not meta-data
			if line[0]!='@' and line[0]!='#':
				#update nb of lines
				xvg_nb_lines[f_index]+=1
								
				#preprocess: remove end of line characters and replace space by tabs
				if '\n' in line:
					line=line.split('\n')[0]
				if '\r' in line:
					line=line.split('\r')[0]				
				if ' ' in line:
					line=line.replace(' ','\t')
								
				#weird format
				if '\t' not in line:
					print "Error: unsuported data format, data is separated by something else than spaces and tabulations."
					sys.exit(1)
								
				#extract info
				line_content=list(filter(('').__ne__, line.split('\t')))

				#store data of relevant columns
				for c_index in xvg_columns[f_index]:
					xvg_data[f_index][c_index].append(float(line_content[c_index]))

							
	#check xvg files have the same number of data lines
	#==================================================
	if len(numpy.unique(xvg_nb_lines.values()))>1:
		print "Error: the xvg files have different number of data lines."
		for f_index in xvg_files:
			print " -" + xvg_names[f_index] + ": " + str(xvg_nb_lines[f_index])
		sys.exit(1)
	else:
		print " -found " + str(xvg_nb_lines[1]) + " data lines"
	
	#post process to turn list into arrays
	#=====================================
	for f_index in xvg_files:
		for c_index in xvg_columns[f_index]:
			xvg_data[f_index][c_index]=numpy.asarray(xvg_data[f_index][c_index])
	
	return
def read_captions():
	#captions: x axis
	graph_captions["x axis"]={}
	tmp=args.captions_x.split('/')
	if len(tmp)>2:
		error_format("x")
	else:
		for f in tmp:
			tmp_f=f.split(':')
			if len(tmp_f)!=2:
				error_format("x")
			else:
				if int(tmp_f[0])==1:
					graph_captions["x axis"]["upper"]=str(tmp_f[1])
				elif int(tmp_f[0])==2:
					graph_captions["x axis"]["lower"]=str(tmp_f[1])
				else:
					error_format("x")
	
	#captions: y axis
	graph_captions["y axis"]={}
	tmp=args.captions_y.split('/')
	if len(tmp)>2:
		error_format("y")
	else:
		for f in tmp:
			tmp_f=f.split(':')
			if len(tmp_f)!=2:
				error_format("y")
			else:
				if int(tmp_f[0])==1:
					graph_captions["y axis"]["upper"]=str(tmp_f[1])
				elif int(tmp_f[0])==2:
					graph_captions["y axis"]["lower"]=str(tmp_f[1])
				else:
					error_format("y")
	
	#captions: title
	graph_captions["title"]={}
	tmp=args.captions_t.split('/')
	if len(tmp)>2:
		error_format("t")
	else:
		for f in tmp:
			tmp_f=f.split(':')
			if len(tmp_f)!=2:
				error_format("t")
			else:
				if int(tmp_f[0])==1:
					graph_captions["title"]["upper"]=str(tmp_f[1])
				elif int(tmp_f[0])==2:
					graph_captions["title"]["lower"]=str(tmp_f[1])
				else:
					error_format("t")
	return
def read_colours():
	
	#case: no colour file 
	#====================
	if args.colour_file=="no":
		#set everyone to "auto"
		#----------------------
		for f_index in xvg_files:
			for c_index in xvg_columns[f_index]:
				xvg_labels[f_index][c_index]="xvg" + str(f_index) + "_col" + str(c_index)
				xvg_colours[f_index][c_index]="auto"
	
		#use jet colour map unless 1 line only in each plot (use 'k')
		#------------------------------------------------------------
		if args.nb_graphs==1 and len(graph_columns["upper"]["y axis"].keys())==1 and len(graph_columns["upper"]["y axis"][graph_columns["upper"]["y axis"].keys()[0]])==1:
			f_index_upper=graph_columns["upper"]["y axis"].keys()[0]
			xvg_colours[f_index_upper][graph_columns["upper"]["y axis"][f_index_upper][0]]='k'				
		elif args.nb_graphs==2 and len(graph_columns["upper"]["y axis"].keys())==1 and len(graph_columns["upper"]["y axis"][graph_columns["upper"]["y axis"].keys()[0]])==1 and len(graph_columns["lower"]["y axis"].keys())==1 and len(graph_columns["lower"]["y axis"][graph_columns["lower"]["y axis"].keys()[0]])==1:
			f_index_upper=graph_columns["upper"]["y axis"].keys()[0]
			xvg_colours[f_index_upper][graph_columns["upper"]["y axis"][f_index_upper][0]]='k'
			f_index_lower=graph_columns["lower"]["y axis"].keys()[0]
			xvg_colours[f_index_lower][graph_columns["lower"]["y axis"][f_index_lower][0]]='k'
		else:			
			colours_auto_nb=0
			colours_auto_pairs={}
			for f_index in xvg_files:
				for c_index in xvg_colours[f_index]:
					if xvg_colours[f_index][c_index]=="auto":
						colours_auto_pairs[colours_auto_nb]=[f_index,c_index]
						colours_auto_nb+=1
			tmp_cmap=cm.get_cmap('jet')
			tmp_colours_values=tmp_cmap(numpy.linspace(0, 1, colours_auto_nb))
			for n in range(0, colours_auto_nb):
				xvg_colours[colours_auto_pairs[n][0]][colours_auto_pairs[n][1]]=tmp_colours_values[n]
	
	#case: colour file
	#=================
	else:
		#read file
		#---------
		with open(args.colour_file) as f:
			lines = f.readlines()
		tmp_nb=len(lines)
		for l_index in range(0,tmp_nb):
			#only process line if not a comment
			if lines[l_index][0]!='@' and lines[l_index][0]!='#':
				#read line
				line=lines[l_index].split(',')
				
				#retrieve data
				xvg_labels[xvg_index[line[0]]][int(line[1])]=str(line[2])
				xvg_colours[xvg_index[line[0]]][int(line[1])]=str(line[3][:-1])

		#set auto colours to jet
		#-----------------------
		colours_auto_nb=0
		colours_auto_pairs={}
		for f_index in xvg_files:
			for c_index in xvg_colours[f_index].keys():
				if xvg_colours[f_index][c_index]=="auto":
					colours_auto_pairs[colours_auto_nb]=[f_index,c_index]
					colours_auto_nb+=1
		if colours_auto_nb>1:
			tmp_cmap=cm.get_cmap('jet')
			tmp_colours_values=tmp_cmap(numpy.linspace(0, 1, colours_auto_nb))
			for n in range(0, colours_auto_nb):
				xvg_colours[colours_auto_pairs[n][0]][colours_auto_pairs[n][1]]=tmp_colours_values[n]
			
	return
def graph_detect_boundaries():

	#upper graph
	#===========	
	#x axis
	#------
	if graph_boundaries["upper"]["x axis"][0]=="auto":
		graph_boundaries["upper"]["x axis"][0]=min(xvg_data[graph_columns["upper"]["x axis"][0]][graph_columns["upper"]["x axis"][1]])
		if args.nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["x axis"][0]=min(xvg_data_smoothed[graph_columns["upper"]["x axis"][0]][graph_columns["upper"]["x axis"][1]])
	else:
		graph_boundaries["upper"]["x axis"][0]=float(graph_boundaries["upper"]["x axis"][0])
		if args.nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["x axis"][0]=float(graph_boundaries_smoothed["upper"]["x axis"][0])
	if graph_boundaries["upper"]["x axis"][1]=="auto":
		graph_boundaries["upper"]["x axis"][1]=max(xvg_data[graph_columns["upper"]["x axis"][0]][graph_columns["upper"]["x axis"][1]])
		if args.nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["x axis"][1]=max(xvg_data_smoothed[graph_columns["upper"]["x axis"][0]][graph_columns["upper"]["x axis"][1]])
	else:
		graph_boundaries["upper"]["x axis"][1]=float(graph_boundaries["upper"]["x axis"][1])
		if args.nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["x axis"][1]=float(graph_boundaries_smoothed["upper"]["x axis"][1])
	
	#y axis
	#------
	if graph_boundaries["upper"]["y axis"][0]=="auto" or graph_boundaries["upper"]["y axis"][1]=="auto":
		tmp_min=100000000000000000000000000000000
		tmp_max=-100000000000000000000000000000000
		for f_index in graph_columns["upper"]["y axis"].keys():
			for c_index in graph_columns["upper"]["y axis"][f_index]:
				tmp_min=min(tmp_min,numpy.min(xvg_data[f_index][c_index]))
				tmp_max=max(tmp_max,numpy.max(xvg_data[f_index][c_index]))
		if args.nb_smoothing>1:
			tmp_min_s=100000000000000000000000000000000
			tmp_max_s=-100000000000000000000000000000000
			for f_index in graph_columns["upper"]["y axis"].keys():
				for c_index in graph_columns["upper"]["y axis"][f_index]:
					tmp_min_s=min(tmp_min_s,numpy.min(xvg_data_smoothed[f_index][c_index]))
					tmp_max_s=max(tmp_max_s,numpy.max(xvg_data_smoothed[f_index][c_index]))
			
	if graph_boundaries["upper"]["y axis"][0]=="auto":
		graph_boundaries["upper"]["y axis"][0]=tmp_min
		if args.nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["y axis"][0]=tmp_min_s
	else:
		graph_boundaries["upper"]["y axis"][0]=float(graph_boundaries["upper"]["y axis"][0])
		if args.nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["y axis"][0]=float(graph_boundaries_smoothed["upper"]["y axis"][0])
	if graph_boundaries["upper"]["y axis"][1]=="auto":
		graph_boundaries["upper"]["y axis"][1]=tmp_max
		if args.nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["y axis"][1]=tmp_max_s
	else:
		graph_boundaries["upper"]["y axis"][1]=float(graph_boundaries["upper"]["y axis"][1])
		if args.nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["y axis"][1]=float(graph_boundaries_smoothed["upper"]["y axis"][1])

	#lower graph
	#===========
	if args.nb_graphs==2:

		#x axis
		#------
		if graph_boundaries["lower"]["x axis"][0]=="auto":
			graph_boundaries["lower"]["x axis"][0]=min(xvg_data[graph_columns["lower"]["x axis"][0]][graph_columns["lower"]["x axis"][1]])
			if args.nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["x axis"][0]=min(xvg_data_smoothed[graph_columns["lower"]["x axis"][0]][graph_columns["lower"]["x axis"][1]])
		else:
			graph_boundaries["lower"]["x axis"][0]=float(graph_boundaries["lower"]["x axis"][0])
			if args.nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["x axis"][0]=float(graph_boundaries_smoothed["lower"]["x axis"][0])
		if graph_boundaries["lower"]["x axis"][1]=="auto":
			graph_boundaries["lower"]["x axis"][1]=max(xvg_data[graph_columns["lower"]["x axis"][0]][graph_columns["lower"]["x axis"][1]])
			if args.nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["x axis"][1]=max(xvg_data_smoothed[graph_columns["lower"]["x axis"][0]][graph_columns["lower"]["x axis"][1]])
		else:
			graph_boundaries["lower"]["x axis"][1]=float(graph_boundaries["lower"]["x axis"][1])
			if args.nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["x axis"][1]=float(graph_boundaries_smoothed["lower"]["x axis"][1])
	
		#y axis
		#------	
		if graph_boundaries["lower"]["y axis"][0]=="auto" or graph_boundaries["lower"]["y axis"][1]=="auto":
			tmp_min=100000000000000000000000000000000
			tmp_max=-100000000000000000000000000000000
			for f_index in graph_columns["lower"]["y axis"].keys():
				for c_index in graph_columns["lower"]["y axis"][f_index]:
					tmp_min=min(tmp_min,numpy.min(xvg_data[f_index][c_index]))
					tmp_max=max(tmp_max,numpy.max(xvg_data[f_index][c_index]))
			if args.nb_smoothing>1:
				tmp_min_s=100000000000000000000000000000000
				tmp_max_s=-100000000000000000000000000000000
				for f_index in graph_columns["lower"]["y axis"].keys():
					for c_index in graph_columns["lower"]["y axis"][f_index]:
						tmp_min_s=min(tmp_min,numpy.min(xvg_data_smoothed[f_index][c_index]))
						tmp_max_s=max(tmp_max,numpy.max(xvg_data_smoothed[f_index][c_index]))
				
		if graph_boundaries["lower"]["y axis"][0]=="auto":
			graph_boundaries["lower"]["y axis"][0]=tmp_min
			if args.nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["y axis"][0]=tmp_min_s
		else:
			graph_boundaries["lower"]["y axis"][0]=float(graph_boundaries["lower"]["y axis"][0])
			if args.nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["y axis"][0]=float(graph_boundaries_smoothed["lower"]["y axis"][0])
		if graph_boundaries["lower"]["y axis"][1]=="auto":
			graph_boundaries["lower"]["y axis"][1]=tmp_max
			if args.nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["y axis"][1]=tmp_max_s
		else:
			graph_boundaries["lower"]["y axis"][1]=float(graph_boundaries["lower"]["y axis"][1])
			if args.nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["y axis"][1]=float(graph_boundaries_smoothed["lower"]["y axis"][1])
				
	return
def graph_xvg(loc_index, loc_counter):

	#create filenames
	#----------------
	filename_png=os.getcwd() + '/' + str(args.output_folder) + '/png/xvg_graph_' + str(int(loc_counter)).zfill(5) + '.png'
	
	#create figure
	#-------------
	fig=plt.figure(figsize=(fig_size_x, fig_size_y))
	x_f_index=graph_columns["upper"]["x axis"][0]
	x_c_index=graph_columns["upper"]["x axis"][1]
	
	#plot data: upper leafet
	#-----------------------
	if 	args.nb_graphs==2:
		ax1 = fig.add_subplot(211)
	else:
		ax1 = fig.add_subplot(111)
	p_upper={}
	for f_index in graph_columns["upper"]["files"]:
		p_upper[f_index]={}
		for c_index in graph_columns["upper"]["y axis"][f_index]:
			p_upper[f_index][c_index]=plt.plot(xvg_data[x_f_index][x_c_index][:loc_index],xvg_data[f_index][c_index][:loc_index], color=xvg_colours[f_index][c_index], linewidth=args.lines_thick, label=xvg_labels[f_index][c_index])
			if args.lines_error!="no" and c_index in xvg_error[f_index].keys():
				e_index=xvg_error[f_index][c_index]
				p_upper[f_index][str(c_index) + "_err"]=plt.fill_between(xvg_data[x_f_index][x_c_index][:loc_index], xvg_data[f_index][c_index][:loc_index]-xvg_data[f_index][e_index][:loc_index], xvg_data[f_index][c_index][:loc_index]+xvg_data[f_index][e_index][:loc_index], color=xvg_colours[f_index][c_index], alpha=0.2)
	fontP.set_size("small")
	if not args.mask_labels:
		ax1.legend(prop=fontP)
	plt.title(graph_captions["title"]["upper"], fontsize="small")
	plt.xlabel(graph_captions["x axis"]["upper"], fontsize="small")
	plt.ylabel(graph_captions["y axis"]["upper"], fontsize="small")
	
	#plot data: lower leafet
	#-----------------------
	if args.nb_graphs==2:
		ax2 = fig.add_subplot(212)
		p_lower={}
		for f_index in graph_columns["lower"]["files"]:
			p_lower[f_index]={}
			for c_index in graph_columns["lower"]["y axis"][f_index]:
				p_lower[f_index][c_index]=plt.plot(xvg_data[x_f_index][x_c_index][:loc_index],xvg_data[f_index][c_index][:loc_index], color=xvg_colours[f_index][c_index], linewidth=args.lines_thick, label=xvg_labels[f_index][c_index])
				if args.lines_error!="no" and c_index in xvg_error[f_index].keys():
					e_index=xvg_error[f_index][c_index]
					p_lower[f_index][str(c_index) + "_err"]=plt.fill_between(xvg_data[x_f_index][x_c_index][:loc_index], xvg_data[f_index][c_index][:loc_index]-xvg_data[f_index][e_index][:loc_index], xvg_data[f_index][c_index][:loc_index]+xvg_data[f_index][e_index][:loc_index], color=xvg_colours[f_index][c_index], alpha=0.2)
		fontP.set_size("small")
		if not args.mask_labels:
			ax2.legend(prop=fontP)
		plt.title(graph_captions["title"]["lower"], fontsize="small")
		plt.xlabel(graph_captions["x axis"]["lower"], fontsize="small")
		plt.ylabel(graph_captions["y axis"]["lower"], fontsize="small")

	#save figure
	#-----------
	ax1.set_xlim(graph_boundaries["upper"]["x axis"][0], graph_boundaries["upper"]["x axis"][1])
	ax1.set_ylim(graph_boundaries["upper"]["y axis"][0], graph_boundaries["upper"]["y axis"][1])
	ax1.xaxis.set_major_locator(MaxNLocator(nbins=5))
	ax1.yaxis.set_major_locator(MaxNLocator(nbins=7))
	plt.setp(ax1.xaxis.get_majorticklabels(), fontsize="small")
	plt.setp(ax1.yaxis.get_majorticklabels(), fontsize="small")
	if args.nb_graphs==2:
		ax2.set_xlim(graph_boundaries["lower"]["x axis"][0], graph_boundaries["lower"]["x axis"][1])
		ax2.set_ylim(graph_boundaries["lower"]["y axis"][0], graph_boundaries["lower"]["y axis"][1])
		ax2.xaxis.set_major_locator(MaxNLocator(nbins=5))
		ax2.yaxis.set_major_locator(MaxNLocator(nbins=7))
		plt.setp(ax2.xaxis.get_majorticklabels(), fontsize="small")
		plt.setp(ax2.yaxis.get_majorticklabels(), fontsize="small")
		plt.subplots_adjust(top=0.9, bottom=0.07, hspace=0.37, left=0.09, right=0.96)
	fig.savefig(filename_png,dpi=args.fig_dpi)
	plt.close()
	
	return
def graph_xvg_smoothed(loc_index, loc_counter):

	#create filenames
	#----------------
	filename_png=os.getcwd() + '/' + str(args.output_folder) + '/png_smoothed/xvg_graph_smoothed_' + str(int(loc_counter)).zfill(5) + '.png'
	
	#create figure
	#-------------
	fig=plt.figure(figsize=(fig_size_x, fig_size_y))
	#fig.suptitle("Evolution of lipid tails order parameter")
	
	x_f_index=graph_columns["upper"]["x axis"][0]
	x_c_index=graph_columns["upper"]["x axis"][1]
	
	#plot data: upper leafet
	#-----------------------
	if 	args.nb_graphs==2:
		ax1 = fig.add_subplot(211)
	else:
		ax1 = fig.add_subplot(111)
	p_upper={}
	for f_index in graph_columns["upper"]["files"]:
		p_upper[f_index]={}
		for c_index in graph_columns["upper"]["y axis"][f_index]:
			p_upper[f_index][c_index]=plt.plot(xvg_data_smoothed[x_f_index][x_c_index][:loc_index],xvg_data_smoothed[f_index][c_index][:loc_index], color=xvg_colours[f_index][c_index], linewidth=args.lines_thick, label=xvg_labels[f_index][c_index])
			if args.lines_error!="no" and c_index in xvg_error[f_index].keys():
				e_index=xvg_error[f_index][c_index]
				p_upper[f_index][str(c_index) + "_err"]=plt.fill_between(xvg_data_smoothed[x_f_index][x_c_index][:loc_index], xvg_data_smoothed[f_index][c_index][:loc_index]-xvg_data_smoothed[f_index][e_index][:loc_index], xvg_data_smoothed[f_index][c_index][:loc_index]+xvg_data_smoothed[f_index][e_index][:loc_index], color=xvg_colours[f_index][c_index], alpha=0.2)
	fontP.set_size("small")
	if not args.mask_labels:
		ax1.legend(prop=fontP)
	plt.title(graph_captions["title"]["upper"], fontsize="small")
	plt.xlabel(graph_captions["x axis"]["upper"], fontsize="small")
	plt.ylabel(graph_captions["y axis"]["upper"], fontsize="small")
	
	#plot data: lower leafet
	#-----------------------
	if args.nb_graphs==2:
		ax2 = fig.add_subplot(212)
		p_lower={}
		for f_index in graph_columns["lower"]["files"]:
			p_lower[f_index]={}
			for c_index in graph_columns["lower"]["y axis"][f_index]:
				p_lower[f_index][c_index]=plt.plot(xvg_data_smoothed[x_f_index][x_c_index][:loc_index],xvg_data_smoothed[f_index][c_index][:loc_index], color=xvg_colours[f_index][c_index], linewidth=args.lines_thick, label=xvg_labels[f_index][c_index])
				if args.lines_error!="no" and c_index in xvg_error[f_index].keys():
					e_index=xvg_error[f_index][c_index]
					p_lower[f_index][str(c_index) + "_err"]=plt.fill_between(xvg_data_smoothed[x_f_index][x_c_index][:loc_index], xvg_data_smoothed[f_index][c_index][:loc_index]-xvg_data_smoothed[f_index][e_index][:loc_index], xvg_data_smoothed[f_index][c_index][:loc_index]+xvg_data_smoothed[f_index][e_index][:loc_index], color=xvg_colours[f_index][c_index], alpha=0.2)
		fontP.set_size("small")
		if not args.mask_labels:
			ax2.legend(prop=fontP)
		plt.title(graph_captions["title"]["lower"], fontsize="small")
		plt.xlabel(graph_captions["x axis"]["lower"], fontsize="small")
		plt.ylabel(graph_captions["y axis"]["lower"], fontsize="small")

	#save figure
	#-----------
	ax1.set_xlim(graph_boundaries_smoothed["upper"]["x axis"][0], graph_boundaries_smoothed["upper"]["x axis"][1])
	ax1.set_ylim(graph_boundaries_smoothed["upper"]["y axis"][0], graph_boundaries_smoothed["upper"]["y axis"][1])
	ax1.xaxis.set_major_locator(MaxNLocator(nbins=5))
	ax1.yaxis.set_major_locator(MaxNLocator(nbins=7))
	plt.setp(ax1.xaxis.get_majorticklabels(), fontsize="small")
	plt.setp(ax1.yaxis.get_majorticklabels(), fontsize="small")
	if args.nb_graphs==2:
		ax2.set_xlim(graph_boundaries_smoothed["lower"]["x axis"][0], graph_boundaries_smoothed["lower"]["x axis"][1])
		ax2.set_ylim(graph_boundaries_smoothed["lower"]["y axis"][0], graph_boundaries_smoothed["lower"]["y axis"][1])
		ax2.xaxis.set_major_locator(MaxNLocator(nbins=5))
		ax2.yaxis.set_major_locator(MaxNLocator(nbins=7))
		plt.setp(ax2.xaxis.get_majorticklabels(), fontsize="small")
		plt.setp(ax2.yaxis.get_majorticklabels(), fontsize="small")
		plt.subplots_adjust(top=0.9, bottom=0.07, hspace=0.37, left=0.09, right=0.96)
	fig.savefig(filename_png,dpi=args.fig_dpi)
	plt.close()
	
	return
def rolling_avg(loc_list):
	
	loc_arr=numpy.asarray(loc_list)
	shape=(loc_arr.shape[-1]-args.nb_smoothing+1,args.nb_smoothing)
	strides=(loc_arr.strides[-1],loc_arr.strides[-1])   	
	return numpy.average(numpy.lib.stride_tricks.as_strided(loc_arr, shape=shape, strides=strides), -1)
def smooth_data():
		
	for f_index in xvg_files:
		for c_index in xvg_columns[f_index]:
			xvg_data_smoothed[f_index][c_index]=rolling_avg(xvg_data[f_index][c_index])
	
	return

################################################################################################################################################
# DATA STRUCTURES
################################################################################################################################################

#the xvg files and the graphs indexes are 1-based while the xvg columns indexes are 0-based
xvg_files=[]
xvg_error={}
xvg_data={}
xvg_data_smoothed={}
xvg_names={}
xvg_index={}
xvg_labels={}
xvg_columns={}
xvg_colours={}
xvg_nb_lines={}
graph_columns={}
graph_captions={}
graph_boundaries={}
graph_boundaries_smoothed={}
graph_boundaries["upper"]={}
graph_boundaries["lower"]={}
graph_boundaries_smoothed["upper"]={}
graph_boundaries_smoothed["lower"]={}

for f_index in range(1, len(args.xvg_names)+1):
	xvg_files.append(f_index)
	xvg_data[f_index]={}
	xvg_error[f_index]={}
	xvg_labels[f_index]={}
	xvg_colours[f_index]={}
	xvg_columns[f_index]=[]
	xvg_nb_lines[f_index]=0
	xvg_data_smoothed[f_index]={}
	xvg_names[f_index]=args.xvg_names[f_index-1]
	xvg_index[args.xvg_names[f_index-1]]=f_index
	
#fig sizes
fig_size_x=float(args.fig_size.split(',')[0])
fig_size_y=float(args.fig_size.split(',')[1])

#graph boundaries
tmp_b=args.boundaries_upper.split('/')
if len(tmp_b)!=2:
	error_format("--upper_range")
else:
	for n in range(0,2):
		tmp_bb=tmp_b[n].split(':')
		if len(tmp_bb)!=2:
			error_format("--upper_range")
		else:
			if tmp_bb[0]=="x":
				graph_boundaries["upper"]["x axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
				graph_boundaries_smoothed["upper"]["x axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
			elif tmp_bb[0]=="y":
				graph_boundaries["upper"]["y axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
				graph_boundaries_smoothed["upper"]["y axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
			else:
				error_format("--upper_range")

tmp_b=args.boundaries_lower.split('/')
if len(tmp_b)!=2:
	error_format("--lower_range")
else:
	for n in range(0,2):
		tmp_bb=tmp_b[n].split(':')
		if len(tmp_bb)!=2:
			error_format("--lower_range")
		else:
			if tmp_bb[0]=="x":
				graph_boundaries["lower"]["x axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
				graph_boundaries_smoothed["lower"]["x axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
			elif tmp_bb[0]=="y":
				graph_boundaries["lower"]["y axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
				graph_boundaries_smoothed["lower"]["y axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
			else:
				error_format("--lower_range")

################################################################################################################################################
# ALGORITHM
################################################################################################################################################

#read data from the xvg files
#----------------------------
print "\nReading data..."
identify_columns()
read_data()

#smooth it if necessary
#----------------------
if args.nb_smoothing>1:
	print "\nSmoothing data..."
	smooth_data()

#set graph parameters
#--------------------
read_captions()
read_colours()
graph_detect_boundaries()

#loop to create graphs
#---------------------
print "\nCreating graphs..."
nb_lines=xvg_nb_lines[1]
counter=0
for line_nb in range(0,nb_lines):
	#display progress
	progress='\r -processing line ' + str(line_nb+1) + '/' + str(nb_lines) + '                      '  
	sys.stdout.flush()
	sys.stdout.write(progress)
	
	#create graphs if necessary
	if ((line_nb-args.lines_offset) % args.lines_skip)==0:						
		graph_xvg(line_nb,counter)
		if args.nb_smoothing>1:
			graph_xvg_smoothed(line_nb,counter)
		counter+=1
print ""

#show frame rate to use
#----------------------
if args.avconv_duration>1:
	avconv_frame_rate=round(counter/float(args.avconv_duration),2)
	print "\n\nUse -r " + str(avconv_frame_rate) + " as frame rate to achieve a duration of " + str(args.avconv_duration) + "s." 
	filename_details=os.getcwd() + '/' + str(output_folder) + '/frame_rate.txt'
	output_stat = open(filename_details, 'w')		
	output_stat.write("Use -r " + str(avconv_frame_rate) + " as frame rate to achieve a duration of " + str(args.avconv_duration) + "s.")
	output_stat.close()

#exit
#====
print "\nFinished successfully! Check output in ./" + args.output_folder + "/"
print ""
sys.exit(0)
