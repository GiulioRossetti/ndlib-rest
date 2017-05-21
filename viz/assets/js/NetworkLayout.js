function NetworkLayout(){
	
	
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
	
	function me (canvas){
		var boundaries = canvas.node().parentNode.getBoundingClientRect();
		console.log("dimensions", boundaries);
		width = boundaries.width;
		height = boundaries.height;
		graph = canvas.datum();
		canvas.node().width = width;
		
		context = canvas.node().getContext("2d");
		console.log(canvas.node())
		force.size([boundaries.width, boundaries.height]);
		
		graph.nodes.forEach(function(n){
			n.x = width/2+100*Math.random();
			n.y = height/2+100*Math.random();
		})
		
		force.nodes(graph.nodes)
			.links(graph.links)
		.start();
		
		
		// link = svg.append("g")
		// 	.classed("links",true)
		// 	.selectAll(".link")
		// 	.data(svg.datum().links)
		// 	.enter()
		// 	.append("line")
		// 	.classed("link", true)
		// .style("stroke-width", 1);
		//
		// node = svg.append("g")
		// 	.classed("nodes", true)
		// 	.selectAll(".node")
		// 	.data(svg.datum().nodes)
		// 	.enter()
		// 	.append("circle")
		// 	.classed("node", true)
		// .attr("r", 5);
		
		
		force.on("tick", tick);
		force.on("end", function(){console.log("end layout")});
		
	}
	
	function tick(){
		context.clearRect(0, 0, width, height);

		    // draw links
		    context.strokeStyle = "#ccc";
			context.globalCompositeOperation = 'overlay';
		    context.beginPath();
		    graph.links.forEach(function(d) {
		      context.moveTo(d.source.x, d.source.y);
		      context.lineTo(d.target.x, d.target.y);
		    });
		    context.stroke();

		    // draw nodes
		    context.fillStyle = "steelblue";
			context.globalCompositeOperation = 'multiply';
		    context.beginPath();
		    graph.nodes.forEach(function(d) {
		      context.moveTo(d.x, d.y);
		      context.arc(d.x, d.y, 4.5, 0, 2 * Math.PI);
		    });
		    context.fill();
	}
	
	return me;
	
}