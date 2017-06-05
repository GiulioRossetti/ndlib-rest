
function ModelView(){
	var panel;
	
	
	function me(row){
		console.log("model", row.datum());
		
		if(row.select("div.panel-deafult").empty()){
			panel = row.append("div")
				.attr({
					"class": "panel panel-default",
				});
			panel.append("div")
				.attr({
					"class": "panel-heading"
				});
			var body = panel.append("div")
				.attr("class","panel-body")
				.append("div")
				.text("model descriptor");
			panel.append("div")
			.attr("class","panel-body stats");
			;
			
			
			
			// d3.entries(row.datum().value).forEach(function(d,i){
// 				stats.append("h5")
// 					.classed("col-md-3",true)
// 				.classed(d.key,true);
// 			})
			
		}
		
		
		panel.select("div.panel-heading")
		.text("Network: " + row.datum().key);
		
		var stats = panel.select("div.stats")
			.selectAll("h5.stats")
		.data(d3.entries(row.datum().value));
			
		stats.enter()
			.append("h5")
			.classed("stats",true)
		.classed("col-md-3",true);
		
		stats.text(function(d){return d.key+":"+d.value});
		
		// d3.entries(row.datum().value).forEach(function(d,i){
// 			panel.select("h5."+d.key)
// 			.text(d.value);
// 		})
		
		//
		//
		//
		//
		// var divs = row.selectAll(".row.model")
		// .data(row.datum())
		// .enter()
		// .append("div")
		// .classed("row", true)
		// .classed("model", true);
		//
		//
		// divs.append("div")
		// 	.classed("col-xs-12", true)
		// 	.append("h5")
		// 	.text(function(d){return "Name: " + d.key} );
		//
		// var params = divs.selectAll("div.params")
		// .data(function(d){return d3.entries(d.value).filter(function(f){return f.key!="selected_initial_infected"})})
		// .enter()
		// .append("div")
		// 	.classed("col-xs-4", true)
		// 	.classed("params", true)
		// .classed("text-center", true);
		// params.append("h5")
		// .text(function(d){return d.key});
		// params.append("h4")
		// .text(function(d){return d.value});
		//
		//	

		
		
	}
	
	return me;
}