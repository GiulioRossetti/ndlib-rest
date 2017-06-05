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

		d3.keys(data).forEach(function(model){
			var numIterations = data[model].length;
			var modelName = model.split("_")[0];
			var modelDescriptor  = app.modelDescriptor[modelName];
			console.log(modelDescriptor);
			var sums = {};
			d3.keys(modelDescriptor["state_labels"]).forEach(function(s){
				sums[s] = d3.range(numIterations).map(function(){return 0})
			});
			console.log("sums+___",sums);
			network.nodes.filter(function(n,i){return true})
			.forEach(function(n,i){
				n.events[model].forEach(function(e,j){
					var nextPos = (j<n.events[model].length-1 ? n.events[model][j+1].i:numIterations);
					var segnode = d3.range(e.i, nextPos);
					// console.log(e.s,segnode);
					segnode.forEach(function(p){
						sums[e.s][p]++;
					})
				})
			})
			var mv = app.modelViewers[model];
			mv.trendData(sums);
			
		})
		
			

})


dispatch.on("loadedNetwork.network", function(network){

	d3.select("#network-viz")
	.datum(network)
	.call(netviz);
})