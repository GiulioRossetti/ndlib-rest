
function ModelStatisticsCounter(){
	
	function me(row){
		
		
		var divs = row.selectAll(".row.model")
		.data(row.datum())
		.enter()
		.append("div")
		.classed("row", true)
		.classed("model", true);
		
		
		divs.append("div")
			.classed("col-xs-12", true)
			.append("h5")
			.text(function(d){return "Name: " + d.key} );
		
		var params = divs.selectAll("div.params")
		.data(function(d){return d3.entries(d.value).filter(function(f){return f.key!="selected_initial_infected"})})
		.enter()
		.append("div")
			.classed("col-xs-4", true)
			.classed("params", true)
		.classed("text-center", true);
		params.append("h5")
		.text(function(d){return d.key});
		params.append("h4")
		.text(function(d){return d.value});
			
			

		
		
	}
	
	return me;
}