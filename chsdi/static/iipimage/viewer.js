function init() {
  
  // Get URL parameters
  var params = {};
  var encodedUrl = encodeURI(document.location.search.substr(1,document.location.search.length));
  if (encodedUrl != '') {
    gArr = encodedUrl.split('&');
    for (var i = 0, ii = gArr.length; i < ii; ++i) {
      var v = '';
      var vArr = gArr[i].split('=');
      if (vArr.length > 1) {
        v = vArr[1];
      }
      params[unescape(vArr[0])] = unescape(v);
    }
  }

  // Set titles
  var title = params.layer;
  if (params.datenherr) {
    title +=' (' + params.datenherr + ')'; 
  }
  title += ': ' + params.title + ': ' + params.bildnummer;
  document.getElementById("pageTitle").innerHTML = decodeURI(params.title + ': ' + params.bildnummer);
  document.getElementById("title").innerHTML = decodeURI(title);


  // Create the map
  var imgWidth = parseInt(params.width);
  var imgHeight = parseInt(params.height);
  var url = "http://web-iipimage.prod.bgdi.ch/iipimage/iipsrv.fcgi?Zoomify=" + params.image + "/";
 
  var proj = new ol.proj.Projection({
    code: 'ZOOMIFY',
    units: ol.proj.Units.PIXELS,
    extent: [0, 0, imgWidth, imgHeight]
  });
 
  var source = new ol.source.Zoomify({
    url: url,
    size: [imgWidth, imgHeight]
  });
 
  var map = new ol.Map({
    layers: [
      new ol.layer.Tile({
        source: source
      })
    ],
    renderer: ol.RendererHint.CANVAS,
    target: 'map',
    view: new ol.View2D({
      projection: proj,
      center:  [imgWidth / 2, - imgHeight / 2],
      zoom: 0
    })
  });
}

