var dispatch = d3.dispatch("createdExperiment","loadedNetwork", "createdModel");



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


// dispatch.on("createdExperiment.network", function(){
//
// 	d3.json("assets/data/network.json", function(error, data){
// 		if(error) console.log(error);
//
// 		console.log("network", data);
//
// 		dispatch.loadedNetwork(data);
// 	})
//
//
//
//
// })


dispatch.on("createdModel.experiment", function(){
	app.experiment.describe(function(data){
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
		
	});
	

})



// dispatch.on("loadedNetwork.timeline", function(network){
//
// 	d3.json("assets/data/iteration.json", function(error, data){
// 		console.log("iterations",data);
//
// 		// for each model
// 		d3.entries(data).forEach(function(m){
// 			var modelName = m.key;
// 			// for each iteration
// 			m.value.forEach(function(i){
// 				var ts = i.iteration;
// 				d3.entries(i.status).forEach(function(j){
// 					var node = network.nodes[j.key];
// 					var evtModel = node.events || (node.events = {});
// 					var evt = evtModel[modelName] || (evtModel[modelName]=[]);
// 					evt.push({i:ts, s: j.value})
// 				})
// 			})
// 		});
//
//
// 		// var model = "SIR_0";
// // 		// create data model for chart
// 		// var numIterations = data[model].length;
// // 		var values = d3.range(numIterations).map(function(){return 0});
// // 		network.nodes.filter(function(n,i){return i < 10})
// // 		.forEach(function(n,i){
// // 			var mater = n.events[model].map(function(e,j){
// // 				var currentStatus = e.s;
// // 				var currPos = e.i;
// // 				var nextPos = (j<n.events[model].length-1 ? n.events[model][j+1].i:numIterations);
// // 				return d3.range(nextPos-currPos).map(function(s){return e.s});
// // 			});
// // 			mater = d3.merge(mater);
// // 			var sum = values.map(function(v,k){
// // 				return v + mater[k];
// // 			})
// // 			values = sum;
// // 			console.log(n,values);
// //
// // 		})
//
// 		var model = "SIR_0";
// 		var numIterations = data[model].length;
// 		var nodeColor = d3.scale.ordinal()
// 			.domain([0,1,2])
// 		.range(colorbrewer['RdYlBu'][3]);
//
// 		var sums = {};
// 		nodeColor.domain().forEach(function(s){
// 			sums[s] = d3.range(numIterations).map(function(){return 0})
// 		});
//
// 		network.nodes//.filter(function(n,i){return i < 10})
// 		.forEach(function(n,i){
// 			n.events[model].forEach(function(e,j){
// 				var nextPos = (j<n.events[model].length-1 ? n.events[model][j+1].i:numIterations);
// 				d3.range(e.i, nextPos).forEach(function(c,k){
// 					sums[e.s][k]++;
// 				})
// 			})
// 		})
//
//
// 		nv.addGraph(function(){
// 			var chart = nv.models.stackedAreaChart()
// 				// .x(function(d,i){return i})
// // 			.y(function(d,i){return d});
//
//
//
// 		d3.select("#chart svg")
// 			.datum(d3.entries(sums).map(function(d){
// 				return {
// 					key: d.key,
// 					values: d.value.map(function(v,i){
// 						return {x:i, y:v}
// 					}),
// 					color: nodeColor(d.key)
// 				}
// 			}));
//
//
//
//
//
// 			console.log(d3.select("#chart svg").datum());
//
//
// 			d3.select("#chart svg").call(chart);
//
// 			return chart;
//
//
// 		})
//
//
// 		console.log("sums",sums);
// 	})
// })


dispatch.on("loadedNetwork.network", function(network){
	var netviz = NetworkLayout();
	d3.select("#network-viz").select("canvas")
	.datum(network)
	.call(netviz);
})