################################################################################################################################################
# IMPORT MODULES
################################################################################################################################################

#import general python tools
import operator
from operator import itemgetter
import sys, os, shutil
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
#xvg_animate.py $xvgfilename1 $xvgfilename2 $output_foldername $nb_graphs $lines_offset $lines_skip $lines_upper $lines_lower $lines_err "${captions_x}" "${captions_y}" "${captions_t}" $colour_file $nb_smoothing $fig_dpi $fig_size $boundaries_upper $boundaries_lower $lines_thick $mask_labels $version
xvgfilename1=sys.argv[1]
xvgfilename2=sys.argv[2]
output_folder=sys.argv[3]
nb_graphs=int(sys.argv[4])
lines_offset=int(sys.argv[5])
lines_skip=int(sys.argv[6])
lines_upper=sys.argv[7]
lines_lower=sys.argv[8]
lines_err=sys.argv[9]
captions_x=sys.argv[10]
captions_y=sys.argv[11]
captions_t=sys.argv[12]
colour_file=sys.argv[13]
nb_smoothing=int(sys.argv[14])
fig_dpi=int(sys.argv[15])
fig_size=sys.argv[16]
boundaries_upper=sys.argv[17]
boundaries_lower=sys.argv[18]
lines_thick=float(sys.argv[19])
mask_labels=sys.argv[20]
avconv_duration=float(sys.argv[21])
version=sys.argv[22]

################################################################################################################################################
# DATA STRUCTURES
################################################################################################################################################

#the xvg files are referred as 1 and 2, all the other indexes (columns of xvg) are 0-based
xvg_err={}
xvg_data={}
xvg_data_smoothed={}
xvg_names={}
xvg_names_r={}
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
if xvgfilename2=="no":
	xvg_files=[1]
	xvg_err[1]={}
	xvg_data[1]={}
	xvg_data_smoothed[1]={}
	xvg_labels[1]={}
	xvg_colours[1]={}
	xvg_columns[1]=[]
	xvg_names[1]=xvgfilename1
	xvg_names_r[xvgfilename1]=1
	xvg_nb_lines[1]=0
else:
	xvg_files=[1,2]
	xvg_err[1]={}
	xvg_data[1]={}
	xvg_data_smoothed[1]={}
	xvg_labels[1]={}
	xvg_colours[1]={}
	xvg_columns[1]=[]
	xvg_names[1]=xvgfilename1
	xvg_names_r[xvgfilename1]=1
	xvg_nb_lines[1]=0
	xvg_err[2]={}
	xvg_data[2]={}
	xvg_data_smoothed[2]={}
	xvg_labels[2]={}
	xvg_colours[2]={}
	xvg_columns[2]=[]
	xvg_names[2]=xvgfilename2
	xvg_names_r[xvgfilename2]=2
	xvg_nb_lines[2]=0

#fig sizes
fig_size_x=float(fig_size.split(',')[0])
fig_size_y=float(fig_size.split(',')[1])

#graph boundaries
tmp_b=boundaries_upper.split('/')
if len(tmp_b)!=2:
	error_format("-v")
else:
	for n in range(0,2):
		tmp_bb=tmp_b[n].split(':')
		if len(tmp_bb)!=2:
			error_format("-v")
		else:
			if tmp_bb[0]=="x":
				graph_boundaries["upper"]["x axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
				graph_boundaries_smoothed["upper"]["x axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
			elif tmp_bb[0]=="y":
				graph_boundaries["upper"]["y axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
				graph_boundaries_smoothed["upper"]["y axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
			else:
				error_format("-v")

tmp_b=boundaries_lower.split('/')
if len(tmp_b)!=2:
	error_format("-w")
else:
	for n in range(0,2):
		tmp_bb=tmp_b[n].split(':')
		if len(tmp_bb)!=2:
			error_format("-w")
		else:
			if tmp_bb[0]=="x":
				graph_boundaries["lower"]["x axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
				graph_boundaries_smoothed["lower"]["x axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
			elif tmp_bb[0]=="y":
				graph_boundaries["lower"]["y axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
				graph_boundaries_smoothed["lower"]["y axis"]=[tmp_bb[1].split(',')[0],tmp_bb[1].split(',')[1]]
			else:
				error_format("-w")

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
	tmp_files=lines_upper.split('/')
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
	if nb_graphs==2:
		tmp_files=lines_lower.split('/')
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
	if lines_err!="no":
		#create pair assocations
		tmp_files=lines_err.split('/')
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
						xvg_err[f_index][int(pair.split('-')[0])]=int(pair.split('-')[1])
						
		#add error columns to data to read
		for f_index in xvg_files:
			for c_index in xvg_err[f_index].keys():
				xvg_columns[f_index].append(xvg_err[f_index][c_index])
				if xvg_err[f_index][c_index] not in xvg_data[f_index].keys():
					xvg_data[f_index][xvg_err[f_index][c_index]]=[]

	
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
	if xvgfilename2!="no":
		if xvg_nb_lines[1]!=xvg_nb_lines[2]:
			print "Error: the two xvg files have a different number of data lines: " + str(xvg_nb_lines[1]) + " (" + str(xvg_names[1]) + ") and " + str(xvg_nb_lines[2]) + " (" + str(xvg_names[2]) + ")."
			sys.exit(1)
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
	tmp=captions_x.split('/')
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
	tmp=captions_y.split('/')
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
	tmp=captions_t.split('/')
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
	if colour_file=="no":
		#set everyone to "auto"
		#----------------------
		for f_index in xvg_files:
			for c_index in xvg_columns[f_index]:
				xvg_labels[f_index][c_index]="xvg" + str(f_index) + "_col" + str(c_index)
				xvg_colours[f_index][c_index]="auto"
	
		#use jet colour map unless 1 line only in each plot (use 'k')
		#------------------------------------------------------------
		if nb_graphs==1 and len(graph_columns["upper"]["y axis"].keys())==1 and len(graph_columns["upper"]["y axis"][graph_columns["upper"]["y axis"].keys()[0]])==1:
			f_index_upper=graph_columns["upper"]["y axis"].keys()[0]
			xvg_colours[f_index_upper][graph_columns["upper"]["y axis"][f_index_upper][0]]='k'				
		elif nb_graphs==2 and len(graph_columns["upper"]["y axis"].keys())==1 and len(graph_columns["upper"]["y axis"][graph_columns["upper"]["y axis"].keys()[0]])==1 and len(graph_columns["lower"]["y axis"].keys())==1 and len(graph_columns["lower"]["y axis"][graph_columns["lower"]["y axis"].keys()[0]])==1:
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
		with open(colour_file) as f:
			lines = f.readlines()
		tmp_nb=len(lines)
		for l_index in range(0,tmp_nb):
			#only process line if not a comment
			if lines[l_index][0]!='@' and lines[l_index][0]!='#':
				#read line
				line=lines[l_index].split(',')
				
				#retrieve data
				xvg_labels[xvg_names_r[line[0]]][int(line[1])]=str(line[2])
				xvg_colours[xvg_names_r[line[0]]][int(line[1])]=str(line[3][:-1])

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
		if nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["x axis"][0]=min(xvg_data_smoothed[graph_columns["upper"]["x axis"][0]][graph_columns["upper"]["x axis"][1]])
	else:
		graph_boundaries["upper"]["x axis"][0]=float(graph_boundaries["upper"]["x axis"][0])
		if nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["x axis"][0]=float(graph_boundaries_smoothed["upper"]["x axis"][0])
	if graph_boundaries["upper"]["x axis"][1]=="auto":
		graph_boundaries["upper"]["x axis"][1]=max(xvg_data[graph_columns["upper"]["x axis"][0]][graph_columns["upper"]["x axis"][1]])
		if nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["x axis"][1]=max(xvg_data_smoothed[graph_columns["upper"]["x axis"][0]][graph_columns["upper"]["x axis"][1]])
	else:
		graph_boundaries["upper"]["x axis"][1]=float(graph_boundaries["upper"]["x axis"][1])
		if nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["x axis"][1]=float(graph_boundaries_smoothed["upper"]["x axis"][1])
	
	#y axis
	#------
	if graph_boundaries["upper"]["y axis"][0]=="auto" or graph_boundaries["upper"]["y axis"][1]=="auto":
		tmp_min=100000000000000000000000000000000
		tmp_max=-100000000000000000000000000000000
		for f_index in graph_columns["upper"]["y axis"].keys():
			for c_index in graph_columns["upper"]["y axis"][f_index]:
				#debug
				print "c_index, max", c_index, numpy.max(xvg_data[f_index][c_index])
				tmp_min=min(tmp_min,numpy.min(xvg_data[f_index][c_index]))
				tmp_max=max(tmp_max,numpy.max(xvg_data[f_index][c_index]))
		if nb_smoothing>1:
			tmp_min_s=100000000000000000000000000000000
			tmp_max_s=-100000000000000000000000000000000
			for f_index in graph_columns["upper"]["y axis"].keys():
				for c_index in graph_columns["upper"]["y axis"][f_index]:
					tmp_min_s=min(tmp_min_s,numpy.min(xvg_data_smoothed[f_index][c_index]))
					tmp_max_s=max(tmp_max_s,numpy.max(xvg_data_smoothed[f_index][c_index]))
			
	if graph_boundaries["upper"]["y axis"][0]=="auto":
		graph_boundaries["upper"]["y axis"][0]=tmp_min
		if nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["y axis"][0]=tmp_min_s
	else:
		graph_boundaries["upper"]["y axis"][0]=float(graph_boundaries["upper"]["y axis"][0])
		if nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["y axis"][0]=float(graph_boundaries_smoothed["upper"]["y axis"][0])
	if graph_boundaries["upper"]["y axis"][1]=="auto":
		graph_boundaries["upper"]["y axis"][1]=tmp_max
		if nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["y axis"][1]=tmp_max_s
	else:
		graph_boundaries["upper"]["y axis"][1]=float(graph_boundaries["upper"]["y axis"][1])
		if nb_smoothing>1:
			graph_boundaries_smoothed["upper"]["y axis"][1]=float(graph_boundaries_smoothed["upper"]["y axis"][1])

	#lower graph
	#===========
	if nb_graphs==2:

		#x axis
		#------
		if graph_boundaries["lower"]["x axis"][0]=="auto":
			graph_boundaries["lower"]["x axis"][0]=min(xvg_data[graph_columns["lower"]["x axis"][0]][graph_columns["lower"]["x axis"][1]])
			if nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["x axis"][0]=min(xvg_data_smoothed[graph_columns["lower"]["x axis"][0]][graph_columns["lower"]["x axis"][1]])
		else:
			graph_boundaries["lower"]["x axis"][0]=float(graph_boundaries["lower"]["x axis"][0])
			if nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["x axis"][0]=float(graph_boundaries_smoothed["lower"]["x axis"][0])
		if graph_boundaries["lower"]["x axis"][1]=="auto":
			graph_boundaries["lower"]["x axis"][1]=max(xvg_data[graph_columns["lower"]["x axis"][0]][graph_columns["lower"]["x axis"][1]])
			if nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["x axis"][1]=max(xvg_data_smoothed[graph_columns["lower"]["x axis"][0]][graph_columns["lower"]["x axis"][1]])
		else:
			graph_boundaries["lower"]["x axis"][1]=float(graph_boundaries["lower"]["x axis"][1])
			if nb_smoothing>1:
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
			if nb_smoothing>1:
				tmp_min_s=100000000000000000000000000000000
				tmp_max_s=-100000000000000000000000000000000
				for f_index in graph_columns["lower"]["y axis"].keys():
					for c_index in graph_columns["lower"]["y axis"][f_index]:
						tmp_min_s=min(tmp_min,numpy.min(xvg_data_smoothed[f_index][c_index]))
						tmp_max_s=max(tmp_max,numpy.max(xvg_data_smoothed[f_index][c_index]))
				
		if graph_boundaries["lower"]["y axis"][0]=="auto":
			graph_boundaries["lower"]["y axis"][0]=tmp_min
			if nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["y axis"][0]=tmp_min_s
		else:
			graph_boundaries["lower"]["y axis"][0]=float(graph_boundaries["lower"]["y axis"][0])
			if nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["y axis"][0]=float(graph_boundaries_smoothed["lower"]["y axis"][0])
		if graph_boundaries["lower"]["y axis"][1]=="auto":
			graph_boundaries["lower"]["y axis"][1]=tmp_max
			if nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["y axis"][1]=tmp_max_s
		else:
			graph_boundaries["lower"]["y axis"][1]=float(graph_boundaries["lower"]["y axis"][1])
			if nb_smoothing>1:
				graph_boundaries_smoothed["lower"]["y axis"][1]=float(graph_boundaries_smoothed["lower"]["y axis"][1])
				
	return
def graph_xvg(loc_index, loc_counter):

	#create filenames
	#----------------
	filename_png=os.getcwd() + '/' + str(output_folder) + '/png/xvg_graph_' + str(int(loc_counter)).zfill(5) + '.png'
	
	#create figure
	#-------------
	fig=plt.figure(figsize=(fig_size_x, fig_size_y))
	x_f_index=graph_columns["upper"]["x axis"][0]
	x_c_index=graph_columns["upper"]["x axis"][1]
	
	#plot data: upper leafet
	#-----------------------
	if 	nb_graphs==2:
		ax1 = fig.add_subplot(211)
	else:
		ax1 = fig.add_subplot(111)
	p_upper={}
	for f_index in graph_columns["upper"]["files"]:
		p_upper[f_index]={}
		for c_index in graph_columns["upper"]["y axis"][f_index]:
			p_upper[f_index][c_index]=plt.plot(xvg_data[x_f_index][x_c_index][:loc_index],xvg_data[f_index][c_index][:loc_index], color=xvg_colours[f_index][c_index], linewidth=lines_thick, label=xvg_labels[f_index][c_index])
			if lines_err!="no" and c_index in xvg_err[f_index].keys():
				e_index=xvg_err[f_index][c_index]
				p_upper[f_index][str(c_index) + "_err"]=plt.fill_between(xvg_data[x_f_index][x_c_index][:loc_index], xvg_data[f_index][c_index][:loc_index]-xvg_data[f_index][e_index][:loc_index], xvg_data[f_index][c_index][:loc_index]+xvg_data[f_index][e_index][:loc_index], color=xvg_colours[f_index][c_index], alpha=0.2)
	fontP.set_size("small")
	if mask_labels=="no":
		ax1.legend(prop=fontP)
	plt.title(graph_captions["title"]["upper"], fontsize="small")
	plt.xlabel(graph_captions["x axis"]["upper"], fontsize="small")
	plt.ylabel(graph_captions["y axis"]["upper"], fontsize="small")
	
	#plot data: lower leafet
	#-----------------------
	if nb_graphs==2:
		ax2 = fig.add_subplot(212)
		p_lower={}
		for f_index in graph_columns["lower"]["files"]:
			p_lower[f_index]={}
			for c_index in graph_columns["lower"]["y axis"][f_index]:
				p_lower[f_index][c_index]=plt.plot(xvg_data[x_f_index][x_c_index][:loc_index],xvg_data[f_index][c_index][:loc_index], color=xvg_colours[f_index][c_index], linewidth=lines_thick, label=xvg_labels[f_index][c_index])
				if lines_err!="no" and c_index in xvg_err[f_index].keys():
					e_index=xvg_err[f_index][c_index]
					p_lower[f_index][str(c_index) + "_err"]=plt.fill_between(xvg_data[x_f_index][x_c_index][:loc_index], xvg_data[f_index][c_index][:loc_index]-xvg_data[f_index][e_index][:loc_index], xvg_data[f_index][c_index][:loc_index]+xvg_data[f_index][e_index][:loc_index], color=xvg_colours[f_index][c_index], alpha=0.2)
		fontP.set_size("small")
		if mask_labels=="no":
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
	if nb_graphs==2:
		ax2.set_xlim(graph_boundaries["lower"]["x axis"][0], graph_boundaries["lower"]["x axis"][1])
		ax2.set_ylim(graph_boundaries["lower"]["y axis"][0], graph_boundaries["lower"]["y axis"][1])
		ax2.xaxis.set_major_locator(MaxNLocator(nbins=5))
		ax2.yaxis.set_major_locator(MaxNLocator(nbins=7))
		plt.setp(ax2.xaxis.get_majorticklabels(), fontsize="small")
		plt.setp(ax2.yaxis.get_majorticklabels(), fontsize="small")
		plt.subplots_adjust(top=0.9, bottom=0.07, hspace=0.37, left=0.09, right=0.96)
	fig.savefig(filename_png,dpi=fig_dpi)
	plt.close()
	
	return
def graph_xvg_smoothed(loc_index, loc_counter):

	#create filenames
	#----------------
	filename_png=os.getcwd() + '/' + str(output_folder) + '/png_smoothed/xvg_graph_smoothed_' + str(int(loc_counter)).zfill(5) + '.png'
	
	#create figure
	#-------------
	fig=plt.figure(figsize=(fig_size_x, fig_size_y))
	#fig.suptitle("Evolution of lipid tails order parameter")
	
	x_f_index=graph_columns["upper"]["x axis"][0]
	x_c_index=graph_columns["upper"]["x axis"][1]
	
	#plot data: upper leafet
	#-----------------------
	if 	nb_graphs==2:
		ax1 = fig.add_subplot(211)
	else:
		ax1 = fig.add_subplot(111)
	p_upper={}
	for f_index in graph_columns["upper"]["files"]:
		p_upper[f_index]={}
		for c_index in graph_columns["upper"]["y axis"][f_index]:
			p_upper[f_index][c_index]=plt.plot(xvg_data_smoothed[x_f_index][x_c_index][:loc_index],xvg_data_smoothed[f_index][c_index][:loc_index], color=xvg_colours[f_index][c_index], linewidth=lines_thick, label=xvg_labels[f_index][c_index])
			if lines_err!="no" and c_index in xvg_err[f_index].keys():
				e_index=xvg_err[f_index][c_index]
				p_upper[f_index][str(c_index) + "_err"]=plt.fill_between(xvg_data_smoothed[x_f_index][x_c_index][:loc_index], xvg_data_smoothed[f_index][c_index][:loc_index]-xvg_data_smoothed[f_index][e_index][:loc_index], xvg_data_smoothed[f_index][c_index][:loc_index]+xvg_data_smoothed[f_index][e_index][:loc_index], color=xvg_colours[f_index][c_index], alpha=0.2)
	fontP.set_size("small")
	if mask_labels=="no":
		ax1.legend(prop=fontP)
	plt.title(graph_captions["title"]["upper"], fontsize="small")
	plt.xlabel(graph_captions["x axis"]["upper"], fontsize="small")
	plt.ylabel(graph_captions["y axis"]["upper"], fontsize="small")
	
	#plot data: lower leafet
	#-----------------------
	if nb_graphs==2:
		ax2 = fig.add_subplot(212)
		p_lower={}
		for f_index in graph_columns["lower"]["files"]:
			p_lower[f_index]={}
			for c_index in graph_columns["lower"]["y axis"][f_index]:
				p_lower[f_index][c_index]=plt.plot(xvg_data_smoothed[x_f_index][x_c_index][:loc_index],xvg_data_smoothed[f_index][c_index][:loc_index], color=xvg_colours[f_index][c_index], linewidth=lines_thick, label=xvg_labels[f_index][c_index])
				if lines_err!="no" and c_index in xvg_err[f_index].keys():
					e_index=xvg_err[f_index][c_index]
					p_lower[f_index][str(c_index) + "_err"]=plt.fill_between(xvg_data_smoothed[x_f_index][x_c_index][:loc_index], xvg_data_smoothed[f_index][c_index][:loc_index]-xvg_data_smoothed[f_index][e_index][:loc_index], xvg_data_smoothed[f_index][c_index][:loc_index]+xvg_data_smoothed[f_index][e_index][:loc_index], color=xvg_colours[f_index][c_index], alpha=0.2)
		fontP.set_size("small")
		if mask_labels=="no":
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
	if nb_graphs==2:
		ax2.set_xlim(graph_boundaries_smoothed["lower"]["x axis"][0], graph_boundaries_smoothed["lower"]["x axis"][1])
		ax2.set_ylim(graph_boundaries_smoothed["lower"]["y axis"][0], graph_boundaries_smoothed["lower"]["y axis"][1])
		ax2.xaxis.set_major_locator(MaxNLocator(nbins=5))
		ax2.yaxis.set_major_locator(MaxNLocator(nbins=7))
		plt.setp(ax2.xaxis.get_majorticklabels(), fontsize="small")
		plt.setp(ax2.yaxis.get_majorticklabels(), fontsize="small")
		plt.subplots_adjust(top=0.9, bottom=0.07, hspace=0.37, left=0.09, right=0.96)
	fig.savefig(filename_png,dpi=fig_dpi)
	plt.close()
	
	return
def rolling_avg(loc_list):
	
	loc_arr=numpy.asarray(loc_list)
	shape=(loc_arr.shape[-1]-nb_smoothing+1,nb_smoothing)
	strides=(loc_arr.strides[-1],loc_arr.strides[-1])   	
	return numpy.average(numpy.lib.stride_tricks.as_strided(loc_arr, shape=shape, strides=strides), -1)
def smooth_data():
		
	for f_index in xvg_files:
		for c_index in xvg_columns[f_index]:
			xvg_data_smoothed[f_index][c_index]=rolling_avg(xvg_data[f_index][c_index])
	
	return

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
if nb_smoothing>1:
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
	if ((line_nb-lines_offset) % lines_skip)==0:						
		graph_xvg(line_nb,counter)
		if nb_smoothing>1:
			graph_xvg_smoothed(line_nb,counter)
		counter+=1

#show frame rate to use
#----------------------
if avconv_duration>1:
	avconv_frame_rate=round(counter/float(avconv_duration),2)
	print "\n\nUse -r " + str(avconv_frame_rate) + " as frame rate to achieve a duration of " + str(avconv_duration) + "s." 
	filename_details=os.getcwd() + '/' + str(output_folder) + '/frame_rate.txt'
	output_stat = open(filename_details, 'w')		
	output_stat.write("Use -r " + str(avconv_frame_rate) + " as frame rate to achieve a duration of " + str(avconv_duration) + "s.")
	output_stat.close()

#exit
#====
sys.exit(0)
