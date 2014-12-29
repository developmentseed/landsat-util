L.mapbox.accessToken = 'pk.eyJ1IjoiamFjcXVlcyIsImEiOiJuRm9TWGYwIn0.ndryRT8IT0U94pHV6o0yng';
var map = L.mapbox.map('compare');
L.mapbox.tileLayer('jacques.new-orleans-i').addTo(map);

var overlay = L.mapbox.tileLayer('jacques.new-orleans-ii').addTo(map);
var range = document.getElementById('range');

function clip() {
	var nw = map.containerPointToLayerPoint([0, 0]),
	se = map.containerPointToLayerPoint(map.getSize()),
	clipX = nw.x + (se.x - nw.x) * range.value;

	overlay.getContainer().style.clip = 'rect(' + [nw.y, clipX, se.y, nw.x].join('px,') + 'px)';
}

range['oninput' in range ? 'oninput' : 'onchange'] = clip;
map.on('move', clip);

map.setView([30.4096,-90.1693], 11);
map.scrollWheelZoom.disable();

clip();
