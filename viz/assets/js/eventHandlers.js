var dispatch = d3.dispatch("createdExperiment","loadedNetwork", "createdModel", "executedIterations");
var netviz = NetworkLayout();


dispatch.on("createdExperiment.form",function(){
	console.log("Create experiment");
	
	// hide form to create experiment
	d3.select("#pnl-create-network")
	.style("display", "none");
	
	// get token
})

dispatch.on("createdModel.form", function(){
	d3.select("#pnl-create-model")
	.style("display", "none");
})

dispatch.on("createdModel.experiment", function(){
	app.experiment.describe(function(data){
		console.log("experiment", data);
		
		app.descriptor(data);
		// update models list
		var modelPanels = d3.select("#models-viz")
			.selectAll("div.model-panel")
		.data(d3.entries(data.Models), function(d){return d.key});
		
		modelPanels.enter()
			.append("div")
		.attr("class","model-panel");
		
		d3.keys(data.Models).forEach(function(d,i){
			d.viewer = app.modelViewers[d] || (app.modelViewers[d] = ModelView());
		})
		
		modelPanels.each(function(d){
			console.log("mp",d);
			d3.select(this).call(app.modelViewers[d.key]);
		})
		
		
		// modelPanels.call(ModelView());
		// modelPanels.call(function(d){return app.modelViewers[d.key]});
	});
})

dispatch.on("executedIterations.timeline", function(data){

		console.log("iterations",data);
		var network = netviz.graph();
		console.log("network", network);
		// for each model
		d3.entries(data).forEach(function(m){
			var modelName = m.key;
			// for each iteration
			m.value.forEach(function(i){
				var ts = i.iteration;
				d3.entries(i.status).forEach(function(j){
					var node = network.nodes[j.key];
					var evtModel = node.events || (node.events = {});
					var evt = evtModel[modelName] || (evtModel[modelName]=[]);
					evt.push({i:ts, s: j.value})
				})
			})
		});

		var model = "SIR_0";
		d3.keys(data).forEach(function(model){
			var numIterations = data[model].length;
			var nodeColor = d3.scale.ordinal()
				.domain([0,1,2])
			.range(colorbrewer['RdYlBu'][3]);

			var sums = {};
			nodeColor.domain().forEach(function(s){
				sums[s] = d3.range(numIterations).map(function(){return 0})
			});

			network.nodes.filter(function(n,i){return true})
			.forEach(function(n,i){
				n.events[model].forEach(function(e,j){
					var nextPos = (j<n.events[model].length-1 ? n.events[model][j+1].i:numIterations);
					var segnode = d3.range(e.i, nextPos);
					console.log(e.s,segnode);
					segnode.forEach(function(p){
						sums[e.s][p]++;
					})
				})
			})


			// nv.addGraph(function(){
// 				var chart = nv.models.lineChart()
// 					// .x(function(d,i){return i})
// 	// 			.y(function(d,i){return d});
//
// 			d3.select("#chart svg")
// 				.datum(d3.entries(sums).map(function(d){
// 					return {
// 						key: d.key,
// 						values: d.value.map(function(v,i){
// 							return {x:i, y:v}
// 						}),
// 						color: nodeColor(d.key)
// 					}
// 				}));
//
// 				console.log(d3.select("#chart svg").datum());
// 				d3.select("#chart svg").call(chart);
// 				return chart;
// 			})
//

			console.log("sums",sums);
		})
		
			

})


dispatch.on("loadedNetwork.network", function(network){

	d3.select("#network-viz")
	.datum(network)
	.call(netviz);
})