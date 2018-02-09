var layer_url = document.currentScript.getAttribute('layer_url');
var selected_field = "";
var paleta = ['rgba(74,190,181,0.8)', 'rgba(24,138,156,0.8)', 'rgba(0,69,132,0.8)', 'rgba(0,30,123,0.8)', 'rgba(16,0,90,0.8)'];
var borde = 'rgba(255,255,255,0)';

function set_wf() {
    factor_progresion = $("#k_slider").slider("option", "value")
    webber_cuts = bojorquezSerrano(factor_progresion);
    layer.setStyle(style_5);
}


$(document).ready(function() {
  $( "#k_slider" ).slider({max: 3,
			     min: 1,
			     value: 1,
			     step: 0.1,
			     change: function( event, ui ) {
				 set_wf();
				 
			     }
			    });

});

function displayField(){
    var select = document.getElementById( 'fields' );
    selected_field = select.options[select.selectedIndex].value
    webber_cuts = bojorquezSerrano(2.0);
    layer.setStyle(style_5);
    //layer.redraw();

}

function bojorquezSerrano(fp) {
    var range = get_range(selected_field);
    var categories = 5,
	maximum = range['max'],
	minimum = range['min'],
	the_sum = 0;

    for (i=0; i<categories; i++) {
	the_sum += Math.pow(fp, i);
    }

    var bit = (maximum - minimum) / the_sum;
    var cuts = new Array();
    cuts.push(minimum)
    for (i=0; i<categories; i++) {
	prev = cuts[i];
	cut = prev + Math.pow(fp, i) * bit;
	cuts.push(cut);
    }

    return cuts;
}

function get_features(url) {
    var data_layer = {};

    $.ajax({
	url: url,
	async: false,
	dataType: 'json',
	success: function(data) {
	    data_layer = data;
	}
    });
    var format_data_layer = new ol.format.GeoJSON();
    var features = format_data_layer.readFeatures(data_layer,
						  {dataProjection: 'EPSG:4326',
						   featureProjection: 'EPSG:3857'});

    return features;
}
//linear color scale 
var colorscale = d3.scale.linear()
.domain([0,1])
.range(["pink", "purple"])
.interpolate(d3.interpolateLab);

function hexToRGB(hex, alpha) {
    var r = parseInt(hex.slice(1, 3), 16),
        g = parseInt(hex.slice(3, 5), 16),
        b = parseInt(hex.slice(5, 7), 16);
    return "rgba(" + r + ", " + g + ", " + b + ", " + alpha + ")";   
}	
var polygon_style2 = new ol.style.Style({
	  fill: new ol.style.Fill({color: hexToRGB(colorscale(0.9),0.65)}),
	  stroke: new ol.style.Stroke({color: hexToRGB(colorscale(0.9),1),width: 1}),
	  text: new ol.style.Text({
		  	font: '12px Calibri,sans-serif',
		  	fill: new ol.style.Fill({color: 'rgba(250,163,1,1)'}),
	        stroke: new ol.style.Stroke({
	        		color: 'rgba(100,100,100,1)',
	        		width: 3
	        })
	  })
});

var point_style2 =  new ol.style.Style({
  image: new ol.style.Circle({radius: 6.0 + size,
      stroke: new ol.style.Stroke({color: hexToRGB(colorscale(0.9),1), lineDash: null, lineCap: 'butt', lineJoin: 'miter', width: 0}), fill: new ol.style.Fill({color: hexToRGB(colorscale(0.9),0.65)})})
});


var map
var vectorSource = new ol.source.Vector({projection: 'EPSG:4326'});
var miVector = new ol.layer.Vector({
    	source: vectorSource
}); 
var layer = new ol.layer.Vector();
jsonSource_data_layer = new ol.source.Vector();
jsonSource_data_layer.addFeatures(get_features(layer_url));

var todos = jsonSource_data_layer.getFeatures();
var geometry_type = todos[0].getGeometry().getType();
layer = new ol.layer.Vector({
    source: jsonSource_data_layer,
	opacity: 0.65
});
function get_range(field) {
    var max = -100000000, min = 100000000;    
    jsonSource_data_layer.getFeatures().forEach(function(feature){
	max = Math.max(max, feature.get(field));
	min = Math.min(min, feature.get(field));	
    });
    return {'max': max,
	    'min': min}
}
var fields = Object.keys(jsonSource_data_layer.getFeatures()[0].getProperties());
var select = document.getElementById( 'fields' );

for( field in fields ) {
    if (fields[field] != "geometry"){
        select.add( new Option( fields[field] ) );
    }
    
    
};

if ((geometry_type == "Polygon") || (geometry_type == "MultiPolygon")){
	layer.setStyle(polygon_style);
	miVector.setStyle(polygon_style2);
}
	
if (geometry_type == "Point" || geometry_type == "MultiPoint"){
	layer.setStyle(point_style);
	miVector.setStyle(point_style2);
}
	
       


    
var stamenLayer = new ol.layer.Tile({
	source: new ol.source.Stamen({layer: 'terrain'})
});

 


map = new ol.Map({
    projection:"EPSG:4326",
    layers: [stamenLayer, layer, miVector],
    target: 'map'
});

var extent = layer.getSource().getExtent();
map.getView().fit(extent, map.getSize());
//map.getView().setZoom(map.getView().getZoom() + 1);


var stats_div = document.getElementById('statistics');


var highlightStyleCache = {};
var highlight;

var displayFeatureInfo = function (pixel) {

	var feature = map.forEachFeatureAtPixel(pixel, function (feature) {
		    return feature;
	});

	if (feature) {
		
		stats_div.innerHTML = "selected: 1";
	}else{
		vectorSource.clear();
	    
	    
	    //stats_div.innerHTML = "selected: "+ ageb_ids.length;
	    
	}

	if (feature !== highlight) {
		vectorSource.clear();
		//if (highlight) {
			//featureOverlay.getSource().removeFeature(highlight);
		//	vectorSource.removeFeature(highlight);
		//}
	    	if (feature) {
			vectorSource.addFeature(feature);
		}
		highlight = feature;
	}

};
map.on('pointermove', function(evt) {
    if (evt.dragging) {
      return;
    }
    var pixel = map.getEventPixel(evt.originalEvent);
    displayFeatureInfo(pixel);
  });
map.on('click', function(evt) {
  displayFeatureInfo(evt.pixel);
});
map.getViewport().addEventListener('mouseout', function(evt){
	vectorSource.clear();
    
    
    //stats_div.innerHTML = "selected: "+ ageb_ids.length;
}, false);





	
function pre_color(col,dimension){
	var slice = _(col).pluck(dimension).map(parseFloat);
	var normalize = d3.scale.linear()
	.domain([_.min(slice),_.max(slice)])
	.range([0,1]);
	return function(d) { return colorscale(normalize(d[dimension])) }
}

