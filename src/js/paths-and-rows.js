L.mapbox.accessToken = 'pk.eyJ1IjoiamFjcXVlcyIsImEiOiJuRm9TWGYwIn0.ndryRT8IT0U94pHV6o0yng';

var map = L.mapbox.map('paths-and-rows', 'jacques.k7coee6a', {
	minZoom: 3,
	maxZoom: 7
}).setView([40, -74.50], 6);

map.scrollWheelZoom.disable();

