# -*- coding: utf-8 -*-

from chsdi.tests.integration import TestsBase


class TestSearchServiceView(TestsBase):

    def test_search_layers(self):
        resp = self.testapp.get('/rest/services/inspire/SearchServer', params={'searchText': 'wand', 'type': 'layers'}, status=200)
        self.failUnless(resp.content_type == 'application/json')
        self.failUnless(resp.json['results'][0]['attrs']['lang'] == 'de')

    def test_search_layers_with_cb(self):
        resp = self.testapp.get('/rest/services/inspire/SearchServer', params={'searchText': 'wand', 'type': 'layers', 'callback': 'cb'}, status=200)
        self.failUnless(resp.content_type == 'application/javascript')

    def test_search_layers_all_langs(self):
        langs = ('de', 'fr', 'it', 'en', 'rm')
        for lang in langs:
            resp = self.testapp.get('/rest/services/inspire/SearchServer', params={'searchText': 'wand', 'type': 'layers', 'lang': lang}, status=200)
            self.failUnless(resp.content_type == 'application/json')
            self.failUnless(resp.json['results'][0]['attrs']['lang'] == lang)

    def test_search_layers_for_one_layer(self):
        resp = self.testapp.get('/rest/services/blw/SearchServer', params={'searchText': 'ch.blw.klimaeignung-spezialkulturen', 'type': 'layers'}, status=200)
        self.failUnless(resp.content_type == 'application/json')
        self.failUnless(len(resp.json['results']) == 1)

    def test_search_layers_accents(self):
        resp = self.testapp.get('/rest/services/ech/SearchServer', params={'searchText': '*%+&/()=?!üäöéà$@i£$', 'type': 'layers'}, status=200)
        self.failUnless(resp.content_type == 'application/json')
        self.failUnless(len(resp.json['results']) == 0)

    def test_search_locations(self):
        resp = self.testapp.get('/rest/services/inspire/SearchServer', params={'searchText': 'rue des berges', 'type': 'locations', 'bbox': '551306.5625,167918.328125,551754.125,168514.625'}, status=200)
        self.failUnless(resp.content_type == 'application/json')

    def test_search_loactions_with_cb(self):
        resp = self.testapp.get('/rest/services/inspire/SearchServer', params={'searchText': 'rue des berges', 'type': 'locations', 'bbox': '551306.5625,167918.328125,551754.125,168514.625', 'callback': 'cb'}, status=200)
        self.failUnless(resp.content_type == 'application/javascript')

    def test_search_locations_all_langs(self):
        # even if not lang dependent
        langs = ('de', 'fr', 'it', 'en', 'rm')
        for lang in langs:
            resp = self.testapp.get('/rest/services/inspire/SearchServer', params={'searchText': 'mont d\'or', 'type': 'locations', 'bbox': '551306.5625,167918.328125,551754.125,168514.625', 'lang': lang}, status=200)
            self.failUnless(resp.content_type == 'application/json')

    def test_search_loactions_and_features(self):
        resp = self.testapp.get('/rest/services/inspire/SearchServer', params={'searchText': 'vd 446', 'type': 'locations', 'bbox': '551306.5625,167918.328125,551754.125,168514.625', 'features': 'ch.astra.ivs-reg_loc'}, status=200)
        self.failUnless(resp.content_type == 'application/json')

    def test_search_wrong_layername(self):
        resp = self.testapp.get('/rest/services/inspire/SearchServer', params={'searchText': 'vd 446', 'type': 'locations', 'bbox': '551306.5625,167918.328125,551754.125,168514.625', 'features': 'lol'}, status=404)

    def test_search_wrong_topic(self):
        resp = self.testapp.get('/rest/services/toto/SearchServer', params={'searchText': 'vd 446', 'type': 'locations', 'bbox': '551306.5625,167918.328125,551754.125,168514.625'}, status=400)

    def test_search_lausanne(self):
        resp = self.testapp.get('/rest/services/ech/SearchServer', params={'searchText': 'lausanne', 'type': 'locations'}, status=200)
        self.failUnless(resp.content_type == 'application/json')
        self.failUnless(resp.json['results'][0]['attrs']['detail'] == 'lausanne _vd_')

    def test_search_wil(self):
        resp = self.testapp.get('/rest/services/ech/SearchServer', params={'searchText': 'wil', 'type': 'locations'}, status=200)
        self.failUnless(resp.content_type == 'application/json')
        self.failUnless(resp.json['results'][0]['attrs']['detail'][:3] == 'wil')

    def test_search_fontenay(self):
        resp = self.testapp.get('/rest/services/ech/SearchServer', params={'searchText': 'fontenay 10 lausanne', 'type': 'locations'}, status=200)
        self.failUnless(resp.content_type == 'application/json')
        self.failUnless(resp.json['results'][0]['attrs']['detail'] == '886311 chemin de fontenay 10 1007 lausanne 5586 lausanne ch vd')

    def test_wilenstrasse_wil(self):
        resp = self.testapp.get('/rest/services/ech/SearchServer', params={'searchText': 'wilenstrasse wil', 'type': 'locations'}, status=200)
        self.failUnless(resp.content_type == 'application/json')
        self.failUnless('wilenstrasse' in resp.json['results'][0]['attrs']['detail'])
        self.failUnless('wil' in resp.json['results'][0]['attrs']['detail'])

    def test_search_max_address(self):
        resp = self.testapp.get('/rest/services/ech/SearchServer', params={'searchText': 'seftigenstrasse', 'type': 'locations'}, status=200)
        self.failUnless(resp.content_type == 'application/json')
        self.failUnless(len(resp.json['results']) <= 20)

    def test_searchtext_apostrophe(self):
        resp = self.testapp.get('/rest/services/ech/SearchServer', params={'searchText': 'av mont d\'or', 'type': 'locations'}, status=200)
        self.failUnless(resp.content_type == 'application/json')
        self.failUnless(resp.json['results'][0]['attrs']['detail'] == '886380 avenue du mont-d\'or 1 1007 lausanne 5586 lausanne ch vd')
        self.failUnless(resp.json['results'][0]['attrs']['num'] == 1)

    def test_address_order(self):
        resp = self.testapp.get('/rest/services/ech/SearchServer', params={'searchText': 'isabelle de montolieu', 'type': 'locations'}, status=200)
        self.failUnless(resp.content_type == 'application/json')
        self.failUnless(resp.json['results'][0]['attrs']['detail'] == '880819 chemin isabelle-de-montolieu 1 1010 lausanne 5586 lausanne ch vd')
        self.failUnless(resp.json['results'][0]['attrs']['num'] == 1)

    def test_features_bbox(self):
        resp = self.testapp.get('/rest/services/ech/SearchServer', params={'features': 'ch.astra.ivs-reg_loc', 'type': 'featureidentify', 'bbox': '551306.5625,167918.328125,551754.125,168514.625'}, status=200)
        self.failUnless(resp.content_type == 'application/json')
        self.failUnless(resp.json['results'][0]['attrs']['origin'] == 'feature')
        self.failUnless(resp.json['results'][0]['attrs']['feature_id'] == '43543')

    def test_features_time(self):
        resp = self.testapp.get('/rest/services/ech/SearchServer', params={'searchText': '9990044', 'features': 'ch.swisstopo.lubis-luftbilder', 'type': 'locations', 'bbox': '551306.5625,167918.328125,551754.125,168514.625', 'timeInstant': '1952'}, status=200)
        self.failUnless(resp.content_type == 'application/json')
        self.failUnless(resp.json['results'][0]['attrs']['origin'] == 'feature')

    def test_features_wrong_time(self):
        resp = self.testapp.get('/rest/services/ech/SearchServer', params={'searchText': '9990044', 'features': 'ch.swisstopo.lubis-luftbilder', 'type': 'locations', 'bbox': '551306.5625,167918.328125,551754.125,168514.625', 'timeInstant': '19522'}, status=400)

    def test_features_wrong_time_2(self):
        resp = self.testapp.get('/rest/services/ech/SearchServer', params={'searchText': '9990044', 'features': 'ch.swisstopo.lubis-luftbilder', 'type': 'locations', 'bbox': '551306.5625,167918.328125,551754.125,168514.625', 'timeInstant': '1952.00'}, status=400)
