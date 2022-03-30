import math
import os
from skimage.transform import (hough_line, hough_line_peaks)
import numpy as np
import cv2

slope = 20
x_start, y_start, x_end, y_end = 0, 0, 0, 0
cropping = False
finished = False
finishedcrop = False
coords = None

def get_coordinates():
    return coords

def calculate_coordinates(ordered_points, x_start,y_start):
    ordered_points_list = ordered_points.tolist()
    ordered_points_fixed = []
    for i in range(0, len(ordered_points_list)):
        point = ordered_points_list[i]
        ordered_points_fixed.append([point[0] + x_start, point[1] + y_start])
    return ordered_points_fixed

def run(imagename):

    global cropping,finished,finishedcrop, x_start,x_end,y_start,y_end

    name = imagename[:imagename.rfind(".")]+"_framed.jpg"
    outpath = name
    inpath = 'static/uploads/'+imagename
    our_image = cv2.imread(inpath)
    oriImage = our_image.copy()


    def pointInRange(pt):
        condition_x = x_end - x_start
        condition_y = y_end - y_start
        if 0.5 <= pt[0] <= (condition_x - 0.5) and 0.5 <= pt[1] <= (condition_y - 0.5):
            return True
        return False


    def order_points_func(pts):
    # initialzie a list of coordinates that will be ordered
    # such that the first entry in the list is the top-left,
    # the second entry is the top-right, the third is the
    # bottom-right, and the fourth is the bottom-left
        rect = np.zeros((4, 2), dtype="int")

    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
        s = np.sum(pts, axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

    # now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

    # return the ordered coordinates
        return rect

#returns true if the lines intersect
    def line_intersection(line1, line2):
        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

        def det(a, b):
            return a[0] * b[1] - a[1] * b[0]

        div = det(xdiff, ydiff)
        if div == 0:
            return False, (0, 0)

        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
        return True, (int(x), int(y))


    def original_func(dst,max_slider):
        lines = cv2.HoughLines(dst, 1, np.pi / 130, max_slider, None, 0, 0)

        points_array = []

        for i in range(0, min(len(lines),11)):
            rho = lines[i][0][0]
            theta = lines[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + 1000 * (-b)), int(y0 + 1000 * (a)))
            pt2 = (int(x0 - 1000 * (-b)), int(y0 - 1000 * (a)))
            points_array.append([pt1, pt2])

        lines_intersecting = []

    # Points that have the potential to be the 4
        for i in range(0, len(points_array)):
            for j in range(i, len(points_array)):
                if i != j:
                    line_value = line_intersection(points_array[i], points_array[j])
                    if line_value[0] and pointInRange(line_value[1]):
                        lines_intersecting.append(line_value[1])
        return lines_intersecting


    def dot(vA, vB):
        return vA[0] * vB[0] + vA[1] * vB[1]


    def ang(lineA, lineB):
        # Get nicer vector form
        vA = [(lineA[0][0] - lineA[1][0]), (lineA[0][1] - lineA[1][1])]
        vB = [(lineB[0][0] - lineB[1][0]), (lineB[0][1] - lineB[1][1])]
        # Get dot prod
        dot_prod = dot(vA, vB)
        # Get magnitudes
        magA = dot(vA, vA) ** 0.5
        magB = dot(vB, vB) ** 0.5
        # Get cosine value
        cos_ = dot_prod / magA / magB
        # Get angle in radians and then convert to degrees
        angle = math.acos(dot_prod / magB / magA)
        # Basically doing angle <- angle mod 360
        ang_deg = math.degrees(angle) % 360

        if ang_deg - 180 >= 0:
            # As in if statement
            return 360 - ang_deg
        else:

            return ang_deg

    def check_slope(point):
        lineA = [(0,1),(0,0)]
        angleA = ang(point,lineA)
        return angleA < slope or (90 - angleA) < slope

    def mouse_crop(event, x, y, flags, param):
        
    # grab references to the global variables
        global x_start, y_start, x_end, y_end, finished, slope, cropping, coords
    # if the left mouse button was DOWN, start RECORDING
    # (x, y) coordinates and indicate that cropping is being
        if event == cv2.EVENT_LBUTTONDOWN:
            x_start, y_start, x_end, y_end = x, y, x, y
            cropping = True
    # Mouse is Moving
        elif event == cv2.EVENT_MOUSEMOVE:
            if cropping == True:
                x_end, y_end = x, y
    # if the left mouse button was released
        elif event == cv2.EVENT_LBUTTONUP:
        # record the ending (x, y) coordinates
            x_end, y_end = x, y
            cropping = False  # cropping is finished

            refPoint = [(x_start, y_start), (x_end, y_end)]
            print(refPoint)


            if len(refPoint) == 2:  # when two points were found
                roi = oriImage[refPoint[0][1]:refPoint[1][1], refPoint[0][0]:refPoint[1][0]]

                dst = cv2.Canny(roi, 50, 200, None, 3)

            # Set a precision of 1 degree. (Divide into 180 data points)
            # You can increase the number of points if needed.
                tested_angles = np.linspace(-np.pi / 2, np.pi / 2, 180)

            # Perform Hough Transformation to change x, y, to h, theta, dist space.
                hspace, theta, dist = hough_line(dst, tested_angles)

            # Now, to find the location of peaks in the hough space we can use hough_line_peaks
                hough_line_peaks(hspace, theta, dist)

                points_array = []

                for _, angle, dist in zip(*hough_line_peaks(hspace, theta, dist)):
                    a = math.cos(angle)
                    b = math.sin(angle)
                    x0 = a * dist
                    y0 = b * dist
                    pt1 = (int(x0 + 1000 * (-b)), int(y0 + 1000 * (a)))
                    pt2 = (int(x0 - 1000 * (-b)), int(y0 - 1000 * (a)))
                    points_array.append([pt1, pt2])

                lines_intersecting = []

                while len(lines_intersecting) == 0 and slope < 90:
                    points_array_2 = []
                    for i in range (0,len(points_array)):
                        if check_slope(points_array[i]):
                            points_array_2.append(points_array[i])

                    for i in range(0, len(points_array_2)):
                        for j in range(i, len(points_array_2)):
                            if i != j:
                                line_value = line_intersection(points_array_2[i], points_array_2[j])
                                if line_value[0] and pointInRange(line_value[1]):
                                    lines_intersecting.append(line_value[1])

                    slope += 10

                if slope > 90 and len(lines_intersecting) == 0:
                    print("Problem with coordinates.")
                    finished = True
                    return

                ordered_points = None

                if len(lines_intersecting) >= 4:
                    ordered_points = order_points_func(lines_intersecting)
                    if abs(ordered_points[1][0] - ordered_points[0][0]) < 70 or abs(ordered_points[3][1] - ordered_points[0][1]) < 50:
                        lines_intersecting = original_func(dst,100)
                        ordered_points = order_points_func(lines_intersecting)

                if len(lines_intersecting) < 4:
                        lines_intersecting = original_func(dst,100)
                        ordered_points = order_points_func(lines_intersecting)


                if ordered_points is not None:
                    if abs(ordered_points[1][0] - ordered_points[0][0]) < 100 or abs(ordered_points[3][1] - ordered_points[0][1]) < 100:
                            lines_intersecting = original_func(dst,10)
                            ordered_points = order_points_func(lines_intersecting)

                else:
                    print("Error with ordered_points")
                    exit(0)

                for i in range(0, len(ordered_points)):
                    cv2.circle(roi, ordered_points[i], 1, (255, 0, 0), thickness=2)

                lines_arr = []
                for i in range(0, len(ordered_points)):
                    for j in range(i, len(ordered_points)):
                        if i != j:
                            lines_arr.append([tuple(ordered_points[i]), tuple(ordered_points[j])])

                counter = 0
                for i in range(0, len(lines_arr)):
                    for j in range(0, len(lines_arr)):
                        if i != j:
                            ret = line_intersection(lines_arr[i], lines_arr[j])
                            if ret[0] and pointInRange(ret[1]):
                                counter = counter + 1
                    if counter == 4:
                        cv2.line(roi, lines_arr[i][0], lines_arr[i][1], (255, 0, 0), 2, cv2.LINE_AA)
                    counter = 0
                writepath = './static/uploads'


                coords = calculate_coordinates(ordered_points,x_start,y_start)
                cv2.imwrite(os.path.join(writepath, name), roi)
                cv2.destroyAllWindows()
                cv2.waitKey()

                finished = True
                return 0


    cv2.namedWindow("image")
    cv2.setMouseCallback("image", mouse_crop)

    while not finished :
        i = our_image.copy()
        if not cropping:
            cv2.imshow("image", our_image)
            cv2.setWindowProperty("image", cv2.WND_PROP_TOPMOST, 1)
        elif cropping:
            cv2.rectangle(i, (x_start, y_start), (x_end, y_end), (0, 255, 0), 2)
            cv2.imshow("image", i)
            cv2.setWindowProperty("image", cv2.WND_PROP_TOPMOST, 1)
            
        cv2.waitKey(1) 

    finished = False    
    return outpath

