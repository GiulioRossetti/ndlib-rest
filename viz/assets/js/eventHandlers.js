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
		d3.select("#network-viz").select("canvas")
		.datum(data)
		.call(netviz);
	})
})


dispatch.on("createdExperiment.experiment", function(){
	d3.json("assets/data/experiment.json", function(error, data){
		console.log("experiment", data);
		
		var div = d3.select("#models-viz")
			// .append("div")
// 			.classed("row",true);
		// div.classed("container", true);
		
		var h3 = div.append("h3");
		h3.append("span")
		.text(" Statistics");
		h3.insert("span",":first-child")
		.classed("glyphicon glyphicon-signal", true);
		div.append("hr");

		
		div.append("h4")
		.text("Network");
		
		div.append("div")
			.classed("row",true)
			.datum(data.Network)
			.call(NetworkStatisticsCounter());
		
		// div.append("div")
		// 	.classed("row",true)
		div.append("h4")
		.text("Models");
		
		div.append("div")
			.classed("row", true)
			.datum(d3.entries(data.Models))
		.call(ModelStatisticsCounter());
		
	})
})