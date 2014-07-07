

import bpy
import mathutils
import math
from bpy import context
from mathutils import Vector
		
def normalize(active_object):
	bpy.ops.object.mode_set(mode = 'OBJECT')
	bpy.ops.object.convert(target = 'CURVE', keep_original = False)
	active_object.data.dimensions = '2D'
	bpy.ops.object.convert(target = 'MESH', keep_original = False)
	
	v = active_object.data.vertices							#Gets the list of mesh vertices.
	ln = len(active_object.data.vertices)					#Gets length of list.
	wm = bpy.context.active_object.matrix_world				#Gets another local-to-world matrix.
	
	n1 = 0													#The rest of this function tries to rotate the trace to make the bottom of the trace parallel with the X axis.
	n2 = 0

	if(v[ln - 1].co.y > v[0].co.y):							#If blender made the array backwards (last index in trace is the top of the object).
		for n in range(0, ln - 2):							#Finds the point near the end of the trace where the trace starts to get flat.
			dy1 = (v[n + 1].co.y - v[n].co.y)
			dx1 = (v[n + 1].co.x - v[n].co.x)
			if((math.fabs(dx1) > math.fabs(dy1))):			#If the change in x is greater than the change in y.				
				n1 = n
				n2 = n + 1
				break
	else:													#The array is forwards.
		for n in range(0, ln - 2):							#Finds the point where the X-axis gets flat.
			dy1 = (v[n + 1].co.y - v[n].co.y)				#This does the same thing as above, it finds the flattest secant in the bottom of the trace.
			dx1 = (v[n + 1].co.x - v[n].co.x)
			if((math.fabs(dx1) > math.fabs(dy1))):			#If the change in x is greater than the change in y.
				n1 = n
				n2 = n + 1
				for m in range(n, ln - 1):
					dy2 = (v[m + 1].co.y - v[m].co.y)
					dx2 = (v[m + 1].co.x - v[m].co.x)
					if((math.fabs(dx2) > math.fabs(dy2))):
						n2 = m + 1
					else:
						n = m
						break
	
	
	xlen = (wm*v[n2].co).x - (wm*v[n1].co).x				#Gets the x and y differences in the secant. These will be the legs of the
	ylen = (wm*v[n2].co).y - (wm*v[n1].co).y				#right triangle.
	angle = - math.atan(ylen/xlen)							#The angle to rotate the trace by.

	bpy.ops.object.mode_set(mode = 'EDIT')					#The rest of this function just sets up the trace to be rotated, and then rotates it around the global Z axis.
	bpy.ops.mesh.select_all()
	bpy.ops.object.mode_set(mode = 'OBJECT')
	bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
	bpy.ops.object.mode_set(mode = 'EDIT')			
	bpy.ops.transform.rotate(value=angle, axis=(0,0,1), constraint_axis=(False, False, True), constraint_orientation='GLOBAL')
	bpy.ops.mesh.select_all()
	bpy.ops.object.mode_set(mode = 'OBJECT')
	
def getTopAngle(tMajp, tMinp):														#Calculates top viewing angle.

	top_inner_angle = math.asin(tMinp/tMajp)										#Top viewing angle.
	ecupper = math.sqrt( 1 - ((tMinp * tMinp) / (tMajp * tMajp)))					#Eccentricity of top ellipse.
	
	return top_inner_angle, ecupper
	
def getBottomAngle(botMajp, botMinp):												#Calculates bottom viewing angle.

	bottom_inner_angle = math.asin(botMinp/botMajp)
	eclower = math.sqrt(1 - ((botMinp * botMinp) / (botMajp * botMajp)))
	
	return bottom_inner_angle, eclower
	
def setCenterAndAxis(active_object, length, right, open):
	bpy.ops.object.mode_set(mode = 'OBJECT')
	bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')				#Sets the object's local origin to be the median of all vertices in its geometry.
	wm = bpy.context.active_object.matrix_world
	ep1 = wm * active_object.data.vertices[0].co									#ep1 is a vertex represented by the global coordinates of the object's first endpoint.
	ep2 = wm * active_object.data.vertices[length - 1].co							#Global coordinates of other endpoint.
	
	if(open and (not right)):														#If the top of the trace is supposed to be open, and the trace is to the left of the rotation axis,
		if(ep1.x <= ep2.x):															#and if the first endpoint is farther to the left of the rotation axis than the second endpoint is,
			x = ep2.x																#use the second endpoint's x-coordinate as the x-coordinate for the axis of rotation.
		else:
			x = ep1.x																#Otherwise, use the first endpoint's x-coordinate for the x-coordinate of the axis of rotation.

	elif(open and right):															#If the trace has an open top and is to the right of the axis of rotation,
		if(ep1.x >= ep2.x):															#and if the first endpoint is further to the right of the axis than the second endpoint is,
			x = ep2.x																#use the second endpoint's x-coordinate as the x-coordinate for the axis of rotation.
		else:
			x = ep1.x

	elif(not open):																	#If the shape is closed, then each endpoint should be at almost exactly the same x-coordinate, because
		v = active_object.data.vertices												#the top and bottom should each extend all the way to the rotation axis. So I take the average of
		x = (ep1.x + ep2.x) / 2														#the top and bottom x-coordinates, and use that as the x-coordinate of the rotation axis.
		v[0].co.x = x
		v[0].co.x = ((wm.inverted()) * v[0].co).x
		v[length - 1].co.x = x
		v[length - 1].co.x = ((wm.inverted()) * v[length - 1].co).x

	yavg = (ep1.y + ep2.y)/2
	zavg = (ep1.z + ep2.z)/2

	center = x, yavg, zavg															#Makes center a tuple of x, yavg, and zavg.
	
	v1 = 0
	v2 = (ep2.y - yavg)
	v3 = (ep2.z - zavg)

	vector = v1, v2, v3																#Makes another tuple.
	center_and_axis = center, vector												#A tuple of tuples.
	
	return center_and_axis

def correctForDistortion(active_object, angleTop, angleBot, ln, right, axis, eup, elow):

	bpy.ops.object.mode_set(mode = 'OBJECT')
	wm = bpy.context.active_object.matrix_world
	wm_inverted = wm.inverted()
	v = active_object.data.vertices

	delta = math.fabs(angleBot - angleTop)															#Difference between top and bottom viewing angles.
	magnitude = math.sqrt(math.pow(axis[0], 2) + math.pow(axis[1], 2) + math.pow(axis[2], 2))		#The magnitude of the vector representing the rotation axis.
	unit_vector = axis[0]/magnitude, axis[1]/magnitude, axis[2]/magnitude							#The unit vector representing the rotation axis.
	count = 0																						#Used to adjust y-values of each coordinate by cross-section.
	points = ln - 1																					#Records number of points that exist in a downward-sloping part of the trace. Used to adjust y-values.
	yhigh = v[0].co.y																				#Highest y-value
	ylow = v[0].co.y																				#Lowest y-value.
	slope = 1 / (((eup - elow) * (eup - elow)) + .0001)												#The apparent slope of the horizontal foreshortening that is caused by perspective distortion.
	#Adding 0.0001 prevents a division by zero in the rare case that both ellipses have the same eccentricity, but doesn't cause a noticeable difference otherwise.
	if(v[ln - 1].co.y > v[0].co.y):																	#If the last element in the trace has a higher Y-coordinate than the first, then Blender probably made 
		for n in range(0, math.floor(ln/2)):														#the array "backwards" (the lowest array index points to the last vertex in the trace). If so,
			temp_vector = Vector((v[n].co.x, v[n].co.y, v[n].co.z))									#reverse the array. This way, index 0 should always point to the top of the shape, and the code can
			v[n].co = v[(ln - 1) - n].co															#iterate over the trace in a consistent manner.
			v[(ln - 1) - n].co = temp_vector
	
	for n in range(0, ln):
		if(v[n].co.y > yhigh):																		#Finds the highest and lowest y-coordinates in the trace. This helps calculate the degree of horizontal foreshortening later.
			yhigh = v[n].co.y
		if(v[n].co.y < ylow):
			ylow = v[n].co.y
		if((v[n].co.y - v[n - 1].co.y) >= 0):														#Decrements 'points' for every instance of positive slope encountered.
			print("here")
			points = points - 1
	
	#Case 1
	if((not right) and (angleBot > angleTop)): 																	#Profile is left-handed, and the bottom is farther away than the top, so start at the top of the shape, and gradually
		for n in range(0, ln):																					#extend points downwards and leftwards, with the most extreme adjustment (for most typical shapes) occurring near index ln - 1.
			v[n].co.x = ((wm * v[n].co).x - (unit_vector[0] * (math.sin(angleTop + ((count * delta/points))))))	#Without this, the whole trace shifts over to the left or right.
			v[n].co.y = ((wm * v[n].co).y - (unit_vector[1] * (math.sin(angleTop + ((count * delta/points))))))	#Stretch out Y by the sine of the viewing angle. Count*delta/points changes viewing angle as the code moves up and down the trace.
			del_x = math.fabs(yhigh - v[n].co.y) / slope														#Calculate the x-difference resulting from horizontal foreshortening.
			v[n].co.x = v[n].co.x - del_x																		#Move point by that amount in the x direction.
			v[n].co = wm_inverted * v[n].co																		#Saves newly calculated point.
			if(math.fabs((v[n].co.y - v[n - 1].co.y) / (v[n].co.x - v[n - 1].co.x)) <= 0.1):					#For cross-sections that are close to flat, this won't change the Y value by any more than what it changed the
				continue																						#previous Y-value by. This prevents addition of unnecessary curves on the top and bottom edges of the trace.
			elif((v[n].co.y - v[n - 1].co.y) <= 0):																#This part changes the Y values of each coordinate by cross-section. While the trace has a negative slope,
				count = count + 1																				#increase count, so the terms in lines 210 and 211 get larger. While the trace has a positive slope,
			else:																								#decrease count, causing the terms in those lines to get smaller. In this way, points on the same horizontal
				count = count - 1
		#cross-sections should always be changed by about the same amount. Similar logic applies to lines 212-214; since del_x depends on the height at that point, it should be the same for points in the same cross-section.
	#Case 2
	elif(right and (angleBot < angleTop)):																		#Profile is right-handed, and the bottom is closer than the top.
		for n in range(0, ln):																					#This loop is pretty much the same as the one above, but since the bottom is closer than the top,
			v[(ln - 1) - n].co.x = ((wm * v[(ln - 1) - n].co).x - (unit_vector[0] * (math.sin(angleBot + ((count * delta/points)))))) #use a + sign to stretch things in the Y direction, and iterate from bottom to top. Also,
			v[(ln - 1) - n].co.y = ((wm * v[(ln - 1) - n].co).y + (unit_vector[1] * (math.sin(angleBot + ((count * delta/points)))))) #use a + sign to stretch the X direction because the trace is right-handed.
			del_x = math.fabs(yhigh - v[ln - 1 - n].co.y) / slope
			v[(ln - 1) - n].co.x = v[(ln - 1) - n].co.x + del_x
			v[(ln - 1) - n].co = wm_inverted * v[(ln - 1) - n].co
			if(math.fabs((v[(ln - 1) - n].co.y - v[(ln - 1) - n - 1].co.y) / (v[(ln - 1) - n].co.x - v[(ln - 1) - n - 1].co.x)) <= 0.1):
				continue
			elif((v[(ln - 1) - n].co.y - v[(ln - 1) - n - 1].co.y) <= 0):
				count = count - 1
			else:
				count = count + 1
	#Case 3		
	elif((not right) and (angleBot < angleTop)):																#Profile is left-handed, and the bottom is closer than the top.
		for n in range(0, ln):																					#This iterates from bottom to top and uses a + sign for the Y, but it uses a - sign for the X.
			v[(ln - 1) - n].co.x = ((wm * v[(ln - 1) - n].co).x - (unit_vector[0] * (math.sin(angleBot + ((count * delta/points))))))
			v[(ln - 1) - n].co.y = ((wm * v[(ln - 1) - n].co).y + (unit_vector[1] * (math.sin(angleBot + ((count * delta/points))))))
			del_x = math.fabs(yhigh - v[n].co.y) / slope
			v[(ln - 1) - n].co.x = v[(ln - 1) - n].co.x - del_x
			v[(ln - 1) - n].co = wm_inverted * v[(ln - 1) - n].co
			if(math.fabs((v[(ln - 1) - n].co.y - v[(ln - 1) - n - 1].co.y) / (v[(ln - 1) - n].co.x - v[(ln - 1) - n - 1].co.x)) <= 0.1):
				continue
			elif((v[(ln - 1) - n].co.y - v[(ln - 1) - n - 1].co.y) <= 0):
				count = count - 1
			else:
				count = count + 1
	#Case 4			
	elif(right and (angleBot > angleTop)):																		#Profile is right-handed, and the bottom is further away than the top.
		for n in range(0, ln):																					#This iterates from top to bottom but and uses a - sign for the Y, but a + sign for the X.
			v[n].co.x = ((wm * v[n].co).x - (unit_vector[0] * (math.sin(angleTop + ((count * delta/points))))))
			v[n].co.y = ((wm * v[n].co).y - (unit_vector[1] * (math.sin(angleTop + ((count * delta/points))))))
			del_x = math.fabs(yhigh - v[n].co.y) / slope
			if(n < ln - 1):
				v[n].co.x = v[n].co.x + del_x
			v[n].co = wm_inverted * v[n].co
			if(math.fabs((v[n].co.y - v[n - 1].co.y) / (v[n].co.x - v[n - 1].co.x)) <= 0.1):
				continue
			elif((v[n].co.y - v[n - 1].co.y) <= 0):
				count = count + 1
			else:
				count = count - 1	
			
def rotate(c, a, steps):																		#Makes a shell of revolution from the trace by calling Blender's spin() function.
	bpy.ops.object.mode_set(mode = 'EDIT')
	bpy.ops.mesh.select_all()
	bpy.ops.mesh.spin(steps=20, dupli=False, angle=6.28318530718, center=c, axis=a)				#Blender's spin().
	bpy.ops.mesh.select_all(action='TOGGLE')													#These make sure everything is selected.
	bpy.ops.mesh.select_all(action='TOGGLE')
	bpy.ops.mesh.remove_doubles(threshold = 0.001, use_unselected=False)						#Removes extra geometry that might be left over from spin(). Very helpful.
	
def extrude():																					#Turns the shell into a solid by applying the solidify modifier. Setting the offset to
	bpy.ops.object.mode_set(mode = 'OBJECT')													#positive 1 extrudes the shell along the vector normal to the trace at every point, or
	bpy.ops.object.modifier_add(type = 'SOLIDIFY')												#outside the solid. If the offset was -1, it would extrude opposite to the normal, or
	bpy.context.object.modifiers["Solidify"].offset = 1											#inside the shape.
	bpy.context.object.modifiers["Solidify"].thickness = .02
	bpy.ops.object.modifier_apply(apply_as = 'DATA', modifier = "Solidify")

def makeSymmetricSolid(open, right, topMajp, topMinp, botMajp, botMinp):						#Basically main(). Calls everything else
	active_object = bpy.context.scene.objects.active											#This is the trace.
	normalize(active_object)																	#Makes sure the active object is a 2D mesh. Also, if the bottom of the trace is not parallel to the X-axis, this rotates it so that it is.
	
	ln = len(active_object.data.vertices)														#The number of vertices in the trace.
	wm = bpy.context.active_object.matrix_world													#The matrix Blender uses to transform coordinates that are local to an object's internal axis into global coordinates.
	wm_inverted = wm.inverted()																	#The matrix Blender uses to transform global coordinates into coordinates local to an object's internal axis.
	
	aT_and_eup = getTopAngle(topMajp, topMinp)													#A tuple containing the viewing angle for the top ellipse, and the eccentricity of that ellipse.
	aB_and_elow = getBottomAngle(botMajp, botMinp)												#A tuple containing the viewing angle for the bottom ellipse, and the eccentricity of that ellipse.
	angleTop = aT_and_eup[0]																	#The viewing angle for the top ellipse.
	eupper = aT_and_eup[1]																		#The eccentricity of the top ellipse.
	angleBot = aB_and_elow[0]																	#The viewing angle of the lower ellipse.
	elower = aB_and_elow[1]																		#The eccentricity of the lower ellipse.
	
	center_and_axis = setCenterAndAxis(active_object, ln, right, open)							#A tuple containing the center of the trace, and the vector representing the trace's rotation axis (which passes through the trace's center).
	
	axis = center_and_axis[1]
	correctForDistortion(active_object, angleTop, angleBot, ln, right, axis, eupper, elower)	#Attempts to remove perspective distortion from the trace.
	
	center_and_axis = setCenterAndAxis(active_object, ln, right, open)							#Call setCenterAndAxis one more time. This will contain the center and axis the trace rotates around.
	center = center_and_axis[0]
	axis = center_and_axis[1]
	rotate(center, axis, 20)																	#Creates a shell of revolution using Blender's spin() function. '20' is the number of discrete steps in the spin.
	extrude()																					#Adds thickness to the shell using Blender's solidify modifier, transforming the shell of revolution into a solid of revolution.
	
class DialogOperator(bpy.types.Operator):														#This class provides the visual interface for the script.
	bl_idname = "object.dialog_operator"
	bl_label = "Create Symmetric Solid"
	
	open = bpy.props.BoolProperty(name="Open?")													#Each of these properties just gets the data from the checkbox, input field, etc.
	right = bpy.props.BoolProperty(name="Right-Handed Profile?")
	
	tMajp = bpy.props.FloatProperty(name="Top Major: ") 
	tMinp = bpy.props.FloatProperty(name="Top Minor: ")
	botMajp = bpy.props.FloatProperty(name= "Bottom Major: ")
	botMinp = bpy.props.FloatProperty(name= "Bottom Minor: ")
		
	def execute(self, context):																	#Runs the script on clicking the 'OK' button
		makeSymmetricSolid(self.open, self.right, self.tMajp, self.tMinp, self.botMajp, self.botMinp)
		
		return {'FINISHED'}
	
	def invoke(self, context, event):
		wm = context.window_manager
		
		return wm.invoke_props_dialog(self)

bpy.utils.register_class(DialogOperator)														#Registers the DialogOperator class with Blender, and puts the script in Blender's spacebar menu.