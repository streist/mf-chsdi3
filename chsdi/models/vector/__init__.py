# -*- coding: utf-8 -*-

from sys import maxsize
from shapely import wkb
from shapely.geometry import asShape
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.orm.properties import ColumnProperty
from geoalchemy import Geometry, WKBSpatialElement, functions

import geojson
from papyrus.geo_interface import GeoInterface
from chsdi.esrigeojsonencoder import loads
from shapely.geometry import asShape


def getScale(imageDisplay, mapExtent):
    inchesPerMeter = 1.0 / 0.0254
    imgPixelPerInch = imageDisplay[2]
    imgPixelWidth = imageDisplay[0]
    bounds = mapExtent.bounds

    mapMeterWidth = abs(bounds[0] - bounds[2])
    imgMeterWidth = (imgPixelWidth / imgPixelPerInch) * inchesPerMeter

    resolution = imgMeterWidth / mapMeterWidth
    scale = 1 / resolution

    return scale


def getToleranceMeters(imageDisplay, mapExtent, tolerance):
    bounds = mapExtent.bounds
    mapMeterWidth = abs(bounds[0] - bounds[2])
    imgPixelWidth = imageDisplay[0]

    toleranceMeters = (mapMeterWidth / imgPixelWidth) * tolerance
    return toleranceMeters


class Vector(GeoInterface):
    __minscale__ = 0
    __maxscale__ = maxsize
    attributes = {}

    # Overrides GeoInterface
    def __read__(self):
        id = None
        geom = None
        properties = {}

        for p in class_mapper(self.__class__).iterate_properties:
            if isinstance(p, ColumnProperty):
                if len(p.columns) != 1:  # pragma: no cover
                    raise NotImplementedError
                col = p.columns[0]
                val = getattr(self, p.key)
                if col.primary_key:
                    id = val
                elif isinstance(col.type, Geometry) and col.name == self.geometry_column_to_return().name:
                    if hasattr(self, '_shape'):
                        geom = self._shape
                    else:
                        geom = wkb.loads(str(val.geom_wkb))
                elif not col.foreign_keys and not isinstance(col.type, Geometry):
                    properties[p.key] = val

        if self.__add_properties__:
            for k in self.__add_properties__:
                properties[k] = getattr(self, k)

        return geojson.Feature(id=id, geometry=geom, properties=properties)

    @property
    def srid(self):
        return self.geometry_column().type.srid

    # Overrides GeoInterface
    @property
    def __geo_interface__(self):
        feature = self.__read__()
        shape = None
        try:
            shape = asShape(feature.geometry)
        except:
            pass
        return geojson.Feature(
            id=self.id,
            geometry=feature.geometry,
            bbox=shape.bounds if shape else None,
            properties=feature.properties,
            # For ESRI
            layerBodId=self.__bodId__,
            layerName='',
            featureId=self.id,
            geometryType=feature.type
        )

    @property
    def __interface__(self):
        return {
            "layerBodId": self.__bodId__,
            "layerName": '',
            "featureId": self.id,
            "attributes": self.getAttributes()
        }

    @classmethod
    def queryable_attributes(cls):
        if hasattr(cls, '__queryable_attributes__'):
            return [cls.__table__.columns[col] for col in cls.__queryable_attributes__]
        else:
            return [None]

    @classmethod
    def geometry_column(cls):
        return cls.__table__.columns['the_geom']

    def geometry_column_to_return(cls):
        geomColumnName = cls.__returnedGeometry__ if hasattr(cls, '__returnedGeometry__') else 'the_geom'
        return cls.__table__.columns[geomColumnName]

    @classmethod
    def primary_key_column(cls):
        return cls.__table__.primary_key

    @classmethod
    def time_instant_column(cls):
        return getattr(cls, cls.__timeInstant__)

    @classmethod
    def geom_filter(cls, geometry, geometryType, imageDisplay, mapExtent, tolerance):
        toleranceMeters = getToleranceMeters(imageDisplay, mapExtent, tolerance)
        scale = None
        minScale = cls.__minscale__ if hasattr(cls, '__minscale__') else None
        maxScale = cls.__maxscale__ if hasattr(cls, '__maxscale__') else None
        if minScale is not None and maxScale is not None:
            scale = getScale(imageDisplay, mapExtent)
        if scale is None or (scale > cls.__minscale__ and scale <= cls.__maxscale__):
            geom = esriRest2Shapely(geometry, geometryType)
            wkbGeometry = WKBSpatialElement(buffer(geom.wkb), 21781)
            geomColumn = cls.geometry_column()
            geomFilter = functions.within_distance(geomColumn, wkbGeometry, toleranceMeters)
            return geomFilter
        return None

    def getAttributes(self):
        attributes = dict()
        fidColumnName = self.primary_key_column().name
        geomColumnName = self.geometry_column().name
        geomColumnNameToReturn = self.geometry_column_to_return().name
        for column in self.__table__.columns:
            columnName = str(column.key)
            if columnName not in (fidColumnName, geomColumnName, geomColumnNameToReturn) and hasattr(self, columnName):
                attribute = getattr(self, columnName)
                if attribute.__class__.__name__ == 'Decimal':
                    attributes[columnName] = attribute.__float__()
                elif attribute.__class__.__name__ == 'datetime':
                    attributes[columnName] = attribute.strftime("%d.%m.%Y")
                else:
                    attributes[columnName] = attribute
        return attributes


def esriRest2Shapely(geometry, geometryType):

    try:
        return asShape(geometry)
    except ValueError:
        return geometry
