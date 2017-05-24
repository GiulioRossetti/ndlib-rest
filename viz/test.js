d3.json(API_HOST+"/api/Experiment", function(e,d){
	console.log(d);
})






d3.json(API_HOST+"/api/Generators/BarabasiAlbertGraphww")
	.send("PUT", {n:200, m:5, token: "7851d8d3-e1a5-4fa5-ad68-92e5645d6e38"},function(e,d){console.log(d)})



$.ajax({method : "put",
	url : API_HOST+"/api/Generators/BarabasiAlbertGraph",
	crossDomain : true,
	data: {n:200, m:5, token: "7851d8d3-e1a5-4fa5-ad68-92e5645d6e38"},
	cache : false
}).done(function(result){
	console.log('Uploaded network, response:');
	console.log(result);
});