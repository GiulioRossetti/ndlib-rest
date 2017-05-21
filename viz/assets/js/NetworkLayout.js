function NetworkLayout(){
	
	
	var force = d3.layout.force()
		.gravity(0.1)
		.charge(-250)
	.linkDistance(150);
	
	var link;
	var node;
	
	function me (svg){
		var boundaries = svg.node().getBoundingClientRect();
		console.log("dimensions", boundaries);
		
		force.size([boundaries.width, boundaries.height]);
		
		force.nodes(svg.datum().nodes)
			.links(svg.datum().links)
		.start();
		
		
		link = svg.append("g")
			.classed("links",true)
			.selectAll(".link")
			.data(svg.datum().links)
			.enter()
			.append("line")
			.classed("link", true)
		.style("stroke-width", 1);
		
		node = svg.append("g")
			.classed("nodes", true)
			.selectAll(".node")
			.data(svg.datum().nodes)
			.enter()
			.append("circle")
			.classed("node", true)
		.attr("r", 5);
		
		
		force.on("tick", tick);
		force.on("end", function(){console.log("end layout")});
		
	}
	
	function tick(){
		link.attr("x1", function(d) { return d.source.x; })
			.attr("y1", function(d) { return d.source.y; })
			.attr("x2", function(d) { return d.target.x; })
			.attr("y2", function(d) { return d.target.y; });

		node.attr("cx", function(d) { return d.x; })
			.attr("cy", function(d) { return d.y; });
	}
	
	return me;
	
}