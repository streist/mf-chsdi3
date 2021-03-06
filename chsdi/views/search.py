# -*- coding: utf-8 -*-

from pyramid.view import view_config
import pyramid.httpexceptions as exc

from chsdi.lib.validation import SearchValidation
from chsdi.lib.helpers import remove_accents
from chsdi.lib.helpers import transformCoordinate
from chsdi.lib.sphinxapi import sphinxapi
from chsdi.lib import mortonspacekey as msk


class Search(SearchValidation):

    LIMIT = 50
    LAYER_LIMIT = 30
    FEATURE_LIMIT = 20
    FEATURE_GEO_LIMIT = 200

    def __init__(self, request):
        super(Search, self).__init__()
        self.quadtree = msk.QuadTree(
            msk.BBox(420000, 30000, 900000, 510000), 20)
        self.sphinx = sphinxapi.SphinxClient()
        sphinxHost = request.registry.settings['sphinxhost']
        self.sphinx.SetServer(sphinxHost, 9312)
        self.sphinx.SetMatchMode(sphinxapi.SPH_MATCH_EXTENDED)

        self.mapName = request.matchdict.get('map')
        self.hasMap(request.db, self.mapName)
        self.lang = request.lang
        self.cbName = request.params.get('callback')
        self.bbox = request.params.get('bbox')
        self.quadindex = None
        self.featureIndexes = request.params.get('features')
        self.timeInstant = request.params.get('timeInstant')
        self.typeInfo = request.params.get('type')

        self.geodataStaging = request.registry.settings['geodata_staging']
        self.results = {'results': []}
        self.request = request

    @view_config(route_name='search', renderer='jsonp')
    def search(self):
        # create a quadindex if the bbox is defined
        if self.bbox is not None and self.typeInfo != 'layers':
            self._get_quad_index()
        if self.typeInfo == 'layers':
            # search all layers
            self.searchText = remove_accents(
                self.request.params.get('searchText')
            )
            self._layer_search()
        if self.typeInfo in ('features', 'featureidentify'):
            # search all features within bounding box
            self._feature_bbox_search()
        if self.typeInfo == 'locations':
            # search all features with text and bounding box
            self.searchText = remove_accents(
                self.request.params.get('searchText')
            )
            self._feature_search()
            # swiss search
            self._swiss_search(self.LIMIT)
        return self.results

    def _swiss_search(self, limit):
        if len(self.searchText) < 1:
            return 0
        self.sphinx.SetLimits(0, limit)
        self.sphinx.SetRankingMode(sphinxapi.SPH_RANK_WORDCOUNT)
        self.sphinx.SetSortMode(sphinxapi.SPH_SORT_EXTENDED, 'rank ASC, @weight DESC, num ASC')
        searchText = self._query_fields('@detail')
        temp = self.sphinx.Query(searchText, index='swisssearch')
        temp = temp['matches'] if temp is not None else temp
        if temp is not None and len(temp) != 0:
            nb_address = 0
            for res in temp:
                if res['attrs']['origin'] == 'address':
                    if nb_address < 20:
                        self.results['results'].append(res)
                        nb_address += 1
                else:
                    self.results['results'].append(res)
            return len(temp)
        return 0

    def _layer_search(self):
        # 10 features per layer are returned at max
        self.sphinx.SetLimits(0, self.LAYER_LIMIT)
        self.sphinx.SetRankingMode(sphinxapi.SPH_RANK_WORDCOUNT)
        self.sphinx.SetSortMode(sphinxapi.SPH_SORT_EXTENDED, '@weight DESC')
        index_name = 'layers_' + self.lang
        searchText = self._query_fields('@(detail,layer)')
        searchText += ' & @topics ' + self.mapName
        # We only take the layers in prod for now
        searchText += ' & @staging prod'
        temp = self.sphinx.Query(searchText, index=index_name)
        temp = temp['matches'] if temp is not None else temp
        if temp is not None and len(temp) != 0:
            self.results['results'] += temp
            return len(temp)
        return 0

    def _feature_search(self):
        # all features in given bounding box
        if self.featureIndexes is None:
            # we need bounding box and layernames. FIXME: this should be error
            return 0

        self.sphinx.SetLimits(0, self.FEATURE_LIMIT)
        self.sphinx.SetRankingMode(sphinxapi.SPH_RANK_WORDCOUNT)
        self.sphinx.SetSortMode(sphinxapi.SPH_SORT_EXTENDED, '@weight DESC')
        if self.timeInstant is not None:
            self.sphinx.SetFilter('year', [self.timeInstant])
        searchText = self._query_fields('@detail')
        if self.quadindex is not None:
            searchText += ' & @geom_quadindex ' + self.quadindex + '*'
        self._add_feature_queries(searchText)
        temp = self.sphinx.RunQueries()
        return self._parse_feature_results(temp)

    def _get_geoanchor_from_bbox(self):
        centerX = (self.bbox[2] + self.bbox[0]) / 2
        centerY = (self.bbox[3] + self.bbox[1]) / 2
        wkt = 'POINT(%s %s)' % (centerX, centerY)
        return transformCoordinate(wkt, 21781, 4326)

    def _feature_bbox_search(self):
        if self.quadindex is None:
            raise exc.HTTPBadRequest('Please provide a bbox parameter')

        if self.featureIndexes is None:
            raise exc.HTTPBadRequest('Please provide a parameter features')

        self.sphinx.SetLimits(0, self.FEATURE_GEO_LIMIT)

        if self.timeInstant is not None:
            self.sphinx.SetFilter('year', [self.timeInstant])
        geoAnchor = self._get_geoanchor_from_bbox()
        self.sphinx.SetGeoAnchor('lat', 'lon', geoAnchor.GetY(), geoAnchor.GetX())
        self.sphinx.SetSortMode(sphinxapi.SPH_SORT_EXTENDED, '@geodist ASC')

        geomFilter = '@geom_quadindex ' + self.quadindex + '*'
        self._add_feature_queries(geomFilter)
        temp = self.sphinx.RunQueries()
        return self._parse_feature_results(temp)

    def _query_fields(self, fields):
        sentence = ' '.join(self.searchText)
        searchText = ''
        counter = 1
        for text in self.searchText:
            if counter != len(self.searchText):
                searchText += '*' + text + '* & '
            else:
                searchText += '*' + text + '*'
            counter += 1
        # starts and ends with query words
        finalQuery = '%s "^%s$" | ' % (fields, sentence)
        # sentence search (the all sentence within the search field)
        # order matters
        finalQuery += '%s "%s" | ' % (fields, sentence)
        # words exact match
        finalQuery += '%s (%s) | ' % (fields, sentence)
        # full text search word per word
        finalQuery += '%s (%s)' % (fields, searchText)

        return finalQuery

    def _query_layers_detail(self, fields):
        searchText = ''
        counter = 1
        for text in self.searchText:
            if counter != len(self.searchText):
                searchText += fields + ' ' + text + ' & '
            else:
                searchText += fields + ' ' + text
            counter += 1
        return searchText

    def _add_feature_queries(self, queryText):
        for index in self.featureIndexes:
            self.sphinx.AddQuery(queryText, index=str(index))

    def _parse_feature_results(self, results):
        nb_match = 0
        for i in range(0, len(results)):
            if 'error' in results[i]:
                if results[i]['error'] != '':
                    raise exc.HTTPNotFound(results[i]['error'])
            if results[i] is not None:
                nb_match += len(results[i]['matches'])
                # Add results to the list
                self.results['results'] += results[i]['matches']
        return nb_match

    def _get_quad_index(self):
        try:
            quadindex = self.quadtree\
                .bbox_to_morton(
                    msk.BBox(self.bbox[0],
                             self.bbox[1],
                             self.bbox[2],
                             self.bbox[3]))
            self.quadindex = quadindex if quadindex != '' else None
        except ValueError:
            self.quadindex = None
