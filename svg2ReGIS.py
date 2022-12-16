from svgpathtools import svg2paths2
from svgpathtools.parser import parse_transform
from svgpathtools.path import transform as path_transform
from math import ceil
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('svgfile')
parser.add_argument(
    "-s", "--scale", help="Ammount to scale image. Provide 0 as argument to fit the window", type=float)
parser.add_argument(
    "-x", "--xhome", help="Origin point for X", type=int, default=0)
parser.add_argument(
    "-y", "--yhome", help="Origin point for Y", type=int, default=0)
parser.add_argument(
    "-f", "--fill", help="Flag. Set to fill in polygons", action='store_true')
parser.add_argument(
    "-c", "--dontclear", help="Flag. Set to disable clearing screen before starting to draw", action='store_true')
parser.add_argument(
    "-e", "--escape", help="Flag. Set to replace ascii ESC character with escapped version (\\033)", action='store_true')


def head_to(x, y, draw=True):
    x = x + args.xhome
    y = y+ args.yhome
    if draw:
        string = "V[" + str(round(x)) + "," + str(round(y)) + "]"
    else:
        string = "\nP[" + str(round(x)) + "," + str(round(y)) + "]"
    return string


def draw_polygon(poly, fill=False):
    # t.color(fill,fill)
    p = poly[0]

    stringLocal = head_to(p[0], (p[1]), draw=False)
    if fill:
        stringLocal += "\nF("
    for p in poly[1:]:
        stringLocal += head_to(p[0], (p[1]))
    # t.up()
    if fill:
        stringLocal += ")"
    return stringLocal


def draw_multipolygon(mpoly, fill=False):
    p = mpoly[0][0]
    stringLocal = head_to(p[0], (p[1]), draw=False)
    for i, poly in enumerate(mpoly):
        stringLocal += draw_polygon(poly, fill)
        if i != 0:
            stringLocal += head_to(p[0], (p[1]), draw=False)

    return stringLocal


args = parser.parse_args()

svg_file = args.svgfile
windowSize = {'width': 800-args.xhome, 'height': 480-args.yhome}
orig_paths, orig_attrs, svg_attr = svg2paths2(svg_file)
if 'width' in svg_attr and args.scale is not None:
    origWidthFloat = float(svg_attr['width'].strip("px"))
    origHeightFloat = float(svg_attr['height'].strip("px"))
    if args.scale == 0:
        if (windowSize['width'] / origWidthFloat) < (windowSize['height'] / origHeightFloat):
            # limited by width
            scaleRatio = (windowSize['width'] - 10) / origWidthFloat
        else:
            # limited by height
            scaleRatio = (windowSize['height'] - 10) / origHeightFloat
    else:
        scaleRatio = args.scale
    paths = []
    attrs = []
    for i, (path, attribute) in enumerate(zip(orig_paths, orig_attrs)):
        new_path = path_transform(path, parse_transform(
            'scale('+str(scaleRatio)+' '+str(scaleRatio)+')'))
        orig_attrs[i]['d'] = new_path.d()  # to make it consistent
        paths.append(new_path)
        attrs.append(orig_attrs[i])
else:
    paths = orig_paths
    attrs = orig_attrs
seg_res = 5
polys = []
for path in paths:
    poly = []
    for subpaths in path.continuous_subpaths():
        points = []
        for seg in subpaths:
            interp_num = ceil(seg.length()/seg_res)
            points.append(seg.point(np.arange(interp_num)/interp_num))
        points = np.concatenate(points)
        points = np.append(points, points[0])
        poly.append(points)
    polys.append([[(p.real, p.imag) for p in pl] for pl in poly])

if args.escape:
    # Start regis command, clear screen, set cursor on.
    RegisString = "\\033P1p"
else:
    # Start regis command, clear screen, set cursor on.
    RegisString = "\033P1p"
if args.dontclear:
    RegisString += "S(I0,C1)"
else:
    RegisString += "S(I0,C1,E)"

for poly, attr in zip(polys, attrs):
    RegisString += draw_multipolygon(poly, fill=args.fill)

if args.escape:
    RegisString += "\n\\033\\"
else:
    RegisString += "\n\033\\"

print(RegisString)
