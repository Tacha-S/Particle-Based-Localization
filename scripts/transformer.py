import rospy
import roslib
import tf
import math
import sys
import time
import numpy as np

from nav_msgs.msg import Odometry as OdometryMsg
from geometry_msgs.msg import PointStamped as PointStampedMsg
from geometry_msgs.msg import Point as PointMsg
from tf2_msgs.msg import TFMessage as TFMsg

class Transformer:
	def __init__(self, name, FOV=np.array([54.0, 45.0]) * math.pi / 180.0, imgShape=np.array([640, 480])):
		self.name = name
		self.FOV = FOV
		self.imgShape = imgShape
		self.depth = 1.0

		self.tfListener = tf.TransformListener()

	def transform(self, points):
		horizFOV = self.FOV[0]
		vertFOV = self.FOV[1]
		depth = 1.0

		horizRadsPerPixel = horizFOV / self.imgShape[0]
		vertRadsPerPixel = vertFOV / self.imgShape[1]

		angles = np.array([horizRadsPerPixel, vertRadsPerPixel])

		newPoints = []

		waiting = False
		while True:
			try:
				stamp = self.tfListener.getLatestCommonTime("/realsense_front_color_optical_frame", "/odom")
				pos, quat = self.tfListener.lookupTransform("/odom", "/realsense_front_color_optical_frame", stamp)
				matTransform = self.tfListener.fromTranslationRotation(pos, quat)

				print "Got transform!"

				startPoint = np.array([0, 0, 0, 1])
				startPoint = np.matmul(matTransform, startPoint)

				for point in points:
					endPixel = np.array(point)

					centeredPixel = endPixel - (self.imgShape / 2)

					endAngs = angles * centeredPixel

					# print "Angs: %f \t\t\t %f" % (endAngs[0], endAngs[1])

					endRay = [math.sin(endAngs[0]), -43]

					h1 = math.sqrt(1 + endRay[0]**2)

					endRay[1] = h1 * math.sin(endAngs[1])

					endPoint = np.array([endRay[0], endRay[1], 1, 1])
					endPoint = np.matmul(matTransform, endPoint)

					newPoints.append(endPoint.copy())
				break
			except:
				if not waiting:
					waiting = True
					sys.stdout.write("Waiting for transform")
				else:
					sys.stdout.write('.')
				sys.stdout.flush()
				time.sleep(0.1)

		return (startPoint, newPoints)
