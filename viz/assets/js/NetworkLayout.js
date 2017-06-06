function NetworkLayout(){
	var canvas;
	
	var force = d3.layout.force()
		// .gravity(0.1)
		.charge(-400)
	.linkDistance(200);
	
	var link;
	var node;
	var context;
	var width;
	var height;
	var graph;

	
	function me(selection){

		
		var boundaries = selection.node().getBoundingClientRect();
		console.log("dimensions", boundaries);
		width = boundaries.width;
		height = 600
		graph = selection.datum();
		
		
		if(!canvas){
			var panel = selection.append("div")
				.attr({
					"class": "panel panel-default",
				});
			panel.append("div")
				.attr({
					"class": "panel-heading"
				})
				.text("Network");
			canvas = panel.append("div")
				.attr("class","panel-body")
				.append("canvas")
				.attr("width", width)
			.attr("height", height);
			var stats = panel.append("div")
			.attr("class","panel-body");
			;
			
			stats.append("h5")
			.attr("class","col-md-4 graph-name");
			
			stats.append("h5")
			.attr("class","col-md-4 graph-num-nodes");
			
			stats.append("h5")
			.attr("class","col-md-4 graph-num-links");
			
		}
		
		
		selection.select(".graph-num-nodes")
			.text(function(d){return "# nodes: " + d.nodes.length});
			
		selection.select(".graph-name")
			.text(function(d){return d.graph.name});
			
		selection.select(".graph-num-links")
			.text(function(d){return "# links: " + d.links.length});
		
		context = canvas.node().getContext("2d");
		console.log(canvas)
		force.size([width, height]);
		
		graph.nodes.forEach(function(n){
			n.x = width/2+100*Math.random();
			n.y = height/2+100*Math.random();
		})
		
		force.nodes(graph.nodes)
			.links(graph.links)
		.start();
		
		force.on("tick", tick);
		force.on("end", function(){
			console.log("end layout")
			//updateIteration(3);
		});
		
	}
	
	function tick(){
		// updateIteration(0);
		context.clearRect(0, 0, width, height);

		// draw links
		context.strokeStyle = "#ccc";
		// context.globalCompositeOperation = 'overlay';
		context.globalAlpha = 0.2;
		context.beginPath();
		graph.links.forEach(function(d) {
			context.moveTo(d.source.x, d.source.y);
			context.lineTo(d.target.x, d.target.y);
		});
		context.stroke();

		// draw nodes
		context.fillStyle = "steelblue";
		// context.globalCompositeOperation	 = 'multiply';
		context.globalAlpha= 1.0;
		context.beginPath();
		graph.nodes.forEach(function(d) {
			context.moveTo(d.x, d.y);
			context.arc(d.x, d.y, 4.5, 0, 2 * Math.PI);
		});
		context.fill();
	}
	
	me.updateIteration = function(i, nodeColor, model){
		context.clearRect(0, 0, width, height);

		// draw links
		context.strokeStyle = "#ccc";
		// context.globalCompositeOperation = 'overlay';
		context.globalAlpha = 0.2;
		context.beginPath();
		graph.links.forEach(function(d) {
			context.moveTo(d.source.x, d.source.y);
			context.lineTo(d.target.x, d.target.y);
		});
		context.stroke();

		// draw nodes
		context.globalAlpha= 1.0;
		nodeColor.domain().forEach(function(c){
			context.fillStyle = nodeColor(c);
			
			context.beginPath();
			var selected = graph.nodes
			.filter(function(n){
				return  getNodeStatusAtIteration(n,i, model.key)== c
			});
			// console.log("Selected " + c, selected.length);
			selected.forEach(function(d) {
				context.moveTo(d.x, d.y);
				context.arc(d.x, d.y, 4.5, 0, 2 * Math.PI);
			});
			context.fill();
		})
	}
	
	function getNodeStatusAtIteration(n,i, model){
		return n.events[model]
				.filter(function(e){
					return e.i <= i
				}).slice(-1)[0].s
	}
	
	
	me.graph = function(){
		return graph;
	}
	
	return me;
	
}