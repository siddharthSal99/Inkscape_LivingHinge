'''
Helpful links for creating an extension:
https://wiki.inkscape.org/wiki/index.php/Generating_objects_from_extensions

https://gitlab.com/inkscape/extensions/-/wikis/My-First-Effect-Extension

https://inkscape.org/develop/extensions/ <-- for the xml formatting in the inx file

https://www.w3schools.com/graphics/svg_path.asp

'''

#! /usr/bin/env python
"""
hinge_cuts.py
A module for creating lines to laser cut living hinges

Copyright (C) 2013 Mark Endicott; drphonon@gmail.com

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For a copy of the GNU General Public License
write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

""" 
Change in version 0.2.
Changed self.unittouu to self.unittouu
and self.uutounit to self.uutounit
to make it work with Inkscape 0.91
Thanks to Pete Prodoehl for pointing this out.
"""

"""
Latest version: 
Author: Siddharth Salunkhe
github: siddharthSal99

Newest version compatible with inkscape 1.0
 - removal of inkex.etree
 - OptionParser to arg_parser syntax
 - Effect.uutounit to self.svg.uutounit

"""

__version__ = "0.2" 
from lxml import etree
import sys,inkex,simplestyle,gettext
_ = gettext.gettext

def drawS(parent, XYstring):         # Draw lines from a list
  name='part'
  style = { 'stroke': '#000000', 'fill': 'none', 'stroke-width': self.svg.unittouu("0.1 mm") }
  drw = {'style':simplestyle.formatStyle(style),inkex.addNS('label','inkscape'):name,'d':XYstring}
  etree.SubElement(parent, inkex.addNS('path','svg'), drw )
  return


class HingeCuts(inkex.Effect):
  def __init__(self):
      # Call the base class constructor.
      inkex.Effect.__init__(self)
      # Define options - Must match to the <param> elements in the .inx file
      self.arg_parser.add_argument('--unit',action='store',type=str, dest='unit',default='mm',help='units of measurement')
      self.arg_parser.add_argument('--cut_length',action='store',type=float, dest='cut_length',default=0,help='length of the cuts for the hinge.')
      self.arg_parser.add_argument('--gap_length',action='store',type=float, dest='gap_length',default=0,help='separation distance between successive hinge cuts.')
      self.arg_parser.add_argument('--sep_distance',action='store',type=float, dest='sep_distance',default=0,help='distance between successive lines of hinge cuts.')

  def effect(self):
    
    unit=self.options.unit
    # starting cut length. Will be adjusted for get an integer number of cuts in the y-direction.
    l = self.svg.unittouu(str(self.options.cut_length) + unit)
    # cut separation in the y-direction
    d = self.svg.unittouu(str(self.options.gap_length) + unit)
    # starting separation between lines of cuts in the x-direction. Will be adjusted to get an integer
    # number of cut lines in the x-direction.
    dd = self.svg.unittouu(str(self.options.sep_distance) + unit)

    
    
    # get selected nodes
    if self.svg.selected:
      # put lines on the current layer        
      parent = self.svg.get_current_layer()
      for id, node in self.svg.selected.items():
      #        inkex.debug("id:" + id)
      #         for key in node.attrib.keys():
      #           inkex.debug(key + ": " + node.get(key))
        x = float(node.get("x"))
        dx = float(node.get("width"))
        y = float(node.get("y"))
        dy = float(node.get("height"))
        
        # calculate the cut lines for the hinge
        lines, l_actual, d_actual, dd_actual = self.calcCutLines(x, y, dx, dy, l, d, dd)

        # all the lines are one path. Prepare the string that describes the path.
        s = ''
        for line in lines:
          s = s + "M %s, %s L %s, %s " % (line['x1'], line['y1'], line['x2'], line['y2'])
        # add the path to the document
        style = { 'stroke': '#000000', 'fill': 'none', 'stroke-width': self.svg.unittouu("0.1 mm")}
        drw = {'style':str(inkex.Style(style)), 'd': s}
        hinge = etree.SubElement(parent, inkex.addNS('path', 'svg'), drw)
        # add a description element to hold the parameters used to create the cut lines
        desc = etree.SubElement(hinge, inkex.addNS('desc', 'svg'))
        desc.text = "Hinge cut parameters: actual(requested)\n" \
          "cut length: %.2f %s (%.2f %s)\n" \
          "gap length: %.2f %s (%.2f %s)\n" \
          "separation distance: %.2f %s (%.2f %s)" % (self.svg.uutounit(l_actual, unit), unit, self.svg.uutounit(l, unit), unit, 
                                 self.svg.uutounit(d_actual, unit), unit, self.svg.uutounit(d, unit), unit,
                                 self.svg.uutounit(dd_actual, unit), unit, self.svg.uutounit(dd, unit), unit)
    else:
      inkex.debug("No rectangle(s) have been selected.")
      
  def calcCutLines(self, x, y, dx, dy, l, d, dd):
    """
    Return a list of cut lines as dicts. Each dict contains the end points for one cut line.
    [{x1, y1, x2, y2}, ... ]
    
    Parameters
    x, y: the coordinates of the lower left corner of the bounding rect
    dx, dy: width and height of the bounding rect
    l: the nominal length of a cut line
    d: the separation between cut lines in the y-direction
    dd: the nominal separation between cut lines in the x-direction
    
    l will be adjusted so that there is an integral number of cuts in the y-direction.
    dd will be adjusted so that there is an integral number of cuts in the x-direction.
    """
    ret = []
    
    # use l as a starting guess. Adjust it so that we get an integer number of cuts in the y-direction
    # First compute the number of cuts in the y-direction using l. This will not in general be an integer.
    p = (dy-d)/(d+l)
    #round p to the nearest integer
    p = round(p)
    #compute the new l that will result in p cuts in the y-direction.
    l = (dy-d)/p - d
    
    # use dd as a starting guess. Adjust it so that we get an even integer number of cut lines in the x-direction.
    p = dx/dd
    p = round(p)
    if p % 2 == 1:
      p = p + 1
    dd = dx/p
    
    #
    # Column A cuts
    #
    currx = 0
    donex = False
    while not donex:
      doney = False
      starty = 0
      endy = (l + d)/2.0
      while not doney:
        if endy >= dy:
          endy = dy
        # Add the end points of the line
        ret.append({'x1' : x + currx, 'y1' : y + starty, 'x2': x + currx, 'y2': y + endy})
        starty = endy + d
        endy = starty + l
        if starty >= dy:
          doney = True
      currx = currx + dd * 2.0
      if currx - dx > dd:
        donex = True
#        inkex.debug("lastx: " + str(lastx) + "; currx: " + str(currx))
    #
    #Column B cuts
    #
    currx = dd
    donex = False
    while not donex:
      doney = False
      starty = d
      endy = starty + l
      while not doney:
        if endy >= dy:
          endy = dy
        # create a line
        ret.append({'x1' : x + currx, 'y1' : y + starty, 'x2': x + currx, 'y2': y + endy})
        starty = endy + d
        endy = starty + l
        if starty >= dy:
          doney = True
      currx = currx + dd*2.0
      if currx > dx:
        donex = True
    
    return (ret, l, d, dd)
    
# Create effect instance and apply it.
effect = HingeCuts()
effect.run()
