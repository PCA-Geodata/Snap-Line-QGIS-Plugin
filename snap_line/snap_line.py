# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Snap_Line
                                 A QGIS plugin
 This plugin snaps a selected point to the closest point of a feature from a defined layer
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-09-20
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Valerio Pinna
        email                : pinnavalerio@yahoo.co.uk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import sys
import subprocess
from math import sqrt
from qgis.PyQt.QtCore import *

from qgis.PyQt.QtGui import *
from PyQt5.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt import uic
from PyQt5.QtWidgets import QMessageBox
from qgis.core import *
                       
from qgis.utils import iface


# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
import os.path

Ui_ConfigureSnapLineDialogBase = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'configuresnapline.ui'))[0]


def max_distance_value():
    settings = QSettings()
    return settings.value('max_distance_value', type=float)

def setMaxDistance(max_distance):
    settings = QSettings()
    return settings.setValue('max_distance_value', max_distance)
    
def polygon_layer_value():
    settings = QSettings()
    return settings.value('polygon_layer_value')

def setPolygonLayer(polygon_layer):
    settings = QSettings()
    return settings.setValue('polygon_layer_value', polygon_layer)



class ConfigureSnapLineDialog (QDialog, Ui_ConfigureSnapLineDialogBase):
    def __init__(self, parent):
        super().__init__()
        self.iface = parent
        self.setupUi(self)
        
        #update the dialog with the last entered value
        self.distance_doubleSpinBox.setValue(max_distance_value())
        max_distance = max_distance_value()
               
        self.polygon_mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        
        layers_list = QgsProject.instance().mapLayers()
        if len(layers_list)!= 0: 
            if not polygon_layer_value():
                return self.dontdonothing()
                
            else:
                self.polygon_mMapLayerComboBox.setLayer(polygon_layer_value())
                polygon_layer = polygon_layer_value()

    def dontdonothing(self):
            pass

class Snap_Line:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.canvas = iface.mapCanvas()
        self.iface = iface
        self.toolButton = QToolButton()
        self.toolButton.setMenu(QMenu())
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolBtnAction = self.iface.addToolBarWidget(self.toolButton)
        
        
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        
        
        
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Snap_Line_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Snap Line')

        self.iface.currentLayerChanged["QgsMapLayer*"].connect(self.toggle)

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Snap_Line', message)


    def initGui(self):    
        self.actionRun = QAction(
          QIcon(os.path.join(os.path.dirname(__file__), "icons/snap_line_icon.png")),
          self.tr('Snap a selected line to the closest feature in the selected layer'),
          self.iface.mainWindow()
        )
        self.actionRun.setEnabled(False)
        
        self.iface.addPluginToMenu(self.tr(u'&Snap Line'), self.actionRun)
        m = self.toolButton.menu()
        m.addAction(self.actionRun)
        self.toolButton.setDefaultAction(self.actionRun)
        self.actionRun.triggered.connect(self.run)
        self.actionConfigure = QAction(
          QIcon(os.path.join(os.path.dirname(__file__), "icons/snap_line_configure_icon.png")),
          self.tr('Configure'),
          self.iface.mainWindow()
        )
        self.iface.registerMainWindowAction(self.actionConfigure, "")
        self.actionConfigure.setToolTip(self.tr('Configure the snapping line tool'))
        m.addAction(self.actionConfigure)
        self.iface.addPluginToMenu(self.tr(u'&Snap Line'), self.actionConfigure)
        self.actionConfigure.triggered.connect(self.configure)
      
      
    def unload(self):
       for action in [self.actionRun,self.actionConfigure]:
           self.iface.removePluginMenu(self.tr(u'&Snap Line'),action)
           self.iface.removeToolBarIcon(action)
           self.iface.unregisterMainWindowAction(action)

       self.iface.removeToolBarIcon(self.toolBtnAction)

    def enable_icon(self):
        self.actionRun.setEnabled(True)

    def run(self):
        settings = QSettings
        max_distance = max_distance_value()      
        polygon_layer= polygon_layer_value()
        
        if polygon_layer == None:
            iface.messageBar().pushMessage('Snap Line Plugin:', 'No snapping layer selected. Plese configure the plugin and retry', level=Qgis.Warning)   
            return self.dontdonothing()          
        
        else:
            polygon_layer_name = polygon_layer.name()
            
            print (polygon_layer_name)
      
            polylayer = QgsProject.instance().mapLayersByName(polygon_layer_name)[0]
            
            
            line_layer = iface.activeLayer()
            if line_layer is not None:
                provider = polylayer.dataProvider()

                #spatial index for polygonal layer (Archaeological Features)
                spIndex = QgsSpatialIndex() #create spatial index object
                polylayer.removeSelection()
                feat = QgsFeature()
                fit = provider.getFeatures() #gets all features in layer


                #points on selected line
                selected_starting_line = []
                selected_end_line = []


                for l_feat in line_layer.selectedFeatures():
    
                    if l_feat.geometry().wkbType() == 2: # LineString
                        l_geom = l_feat.geometry().asPolyline()
                    if l_feat.geometry().wkbType() == 5: # MultiLineString
                        l_geom_list = l_feat.geometry().asMultiPolyline()
                        l_geom = l_geom_list[0]

                    old_start_point = QgsPointXY(l_geom[0])
                    old_end_point = QgsPointXY(l_geom[-1])
                    old_start_point_Wkt = l_geom[0].asWkt()
                    old_end_point_Wkt = l_geom[-1].asWkt()
                    selected_starting_line.append(old_start_point)
                    selected_end_line.append(old_end_point)
                    old_line_id = [l_feat.id()]

                    
                    ###starting point###
                    
                    # insert polygon features to index
                    while fit.nextFeature(feat):
                        spIndex.addFeature(feat)
                    pt_start = selected_starting_line[0]
                    
                    # QgsSpatialIndex.nearestNeighbor (QgsPoint point, int neighbors)
                    nearestIds = spIndex.nearestNeighbor(pt_start,1) # we need only one neighbour
                    print (nearestIds)
                    single_nearestIds = []
                    if len(nearestIds) == 1:
                        single_nearestIds = nearestIds
                    if len(nearestIds) > 1:
                        single_nearestIds.append(nearestIds[-1])
                    print (single_nearestIds)
                    #select nearest polygon by id
                    polylayer.select(nearestIds)



                    # for feature in polylayer.selectedFeatures():   ###old method for segments snapping
                        # g_poly = feature.geometry()
                        # calc_new_geom = g_poly.closestSegmentWithContext(old_start_point)
                        # new_start_geom = calc_new_geom[1]
                        # sqrDist = calc_new_geom[0]
                        
                    for feature in polylayer.selectedFeatures():   ###new method for vertex snapping
                        g_poly = feature.geometry()
                    
                        calc_new_geom = g_poly.closestVertex(old_start_point)
                        new_start_geom = calc_new_geom[0]
                        sqrDist = calc_new_geom[4]    
                        
                        

                        real_distance = sqrt(sqrDist)
                        print (real_distance)
                        
                        
                    ###end point###
                    
                    # insert polygon features to index
                    while fit.nextFeature(feat):
                        spIndex.insertFeature(feat)
                    pt_end = selected_end_line[0]
                    
                    # QgsSpatialIndex.nearestNeighbor (QgsPoint point, int neighbors)
                    nearestIds = spIndex.nearestNeighbor(pt_end,1) # we need only one neighbour
                    print (nearestIds)
                    single_nearestIds = []
                    if len(nearestIds) == 1:
                        single_nearestIds = nearestIds
                    if len(nearestIds) > 1:
                        single_nearestIds.append(nearestIds[-1])
                    print (single_nearestIds)
                    #select nearest polygon by id
                    polylayer.select(nearestIds)

                    # for feature in polylayer.selectedFeatures():   ### old method for segments
                        # g_poly = feature.geometry()
                        # calc_new_geom = g_poly.closestSegmentWithContext(old_end_point)
                        # new_end_geom = calc_new_geom[1]
                        # sqrDist = calc_new_geom[0]
                        
                        
                    for feature in polylayer.selectedFeatures():   ###new method for vertex snapping
                        g_poly = feature.geometry()
                    
                        calc_new_geom = g_poly.closestVertex(old_end_point)
                        new_end_geom = calc_new_geom[0]
                        sqrDist = calc_new_geom[4]    
                            
                        

                        real_distance = sqrt(sqrDist)
                        print (real_distance)
                        polylayer.removeSelection()
                        if real_distance <= max_distance:
                            #new_pt_wtk = new_geom.asWkt()
                            new_line_wkt = 'Linestring ({0} {1}, {2} {3})'.format(new_start_geom.x(), new_start_geom.y(), new_end_geom.x(), new_end_geom.y())
                      
                            line_layer.startEditing()
                            line_layer.beginEditCommand("Snap Section Line")
                            line_layer.selectByIds(old_line_id)
                            new_geometry = QgsGeometry.fromWkt(new_line_wkt)
                            line_layer.changeGeometry(old_line_id[0], new_geometry)

                            # Save the changes in the buffer 
                            line_layer.triggerRepaint()
                            #iface.mapCanvas().refresh()
                            
                            line_layer.endEditCommand()
                        else:
                            iface.messageBar().pushMessage('Snap Layer Plugin:', 'No features available within the set distance range', level=Qgis.Info)   
                            polylayer.removeSelection()
                            return self.dontdonothing() 

        
    def configure(self):
        dlg = ConfigureSnapLineDialog(self.iface)
        dlg.exec_()
        if dlg.result():
            
            
            max_distance = dlg.distance_doubleSpinBox.value()
            setMaxDistance(max_distance)

            
            polygon_layer = dlg.polygon_mMapLayerComboBox.currentLayer() 
            setPolygonLayer(polygon_layer)


    def dontdonothing(self):
            pass

    def toggle(self):
        _point = QgsWkbTypes.LineGeometry  # QGis3
        

        # QgsMessageLog.logMessage("Toggle")
        layer = self.canvas.currentLayer()
        # Decide whether the plugin button/menu is enabled or disabled
        if layer is not None:
            if layer.type() == QgsMapLayer.VectorLayer:
                try:
                # disconnect, will be reconnected
                    layer.editingStarted.disconnect(self.toggle)
                except:
                    pass
                try:
                    # when it becomes active layer again
                    layer.editingStopped.disconnect(self.toggle)
                except:
                    pass
                
                if layer.geometryType() == _point:
                    self.actionConfigure.setEnabled(True)
                    self.actionRun.setEnabled(True)
                   
                else:
                    self.actionConfigure.setEnabled(False)
                    self.actionRun.setEnabled(False)
                