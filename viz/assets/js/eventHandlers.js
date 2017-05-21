var dispatch = d3.dispatch("createdExperiment");



dispatch.on("createdExperiment.form",function(){
	console.log("Create experiment");
	
	// hide form to create experiment
	d3.select("#pnl-create-experiment")
	.style("display", "none");
	
	// get token
})


dispatch.on("createdExperiment.network", function(){
	
	d3.json("assets/data/network.json", function(error, data){
		if(error) console.log(error);
		
		console.log("network", data);
		
		var netviz = NetworkLayout();
		d3.select("#network-viz").select("svg")
		.datum(data)
		.call(netviz);
	})
})