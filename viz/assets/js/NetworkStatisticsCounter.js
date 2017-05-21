
function NetworkStatisticsCounter(){
	
	function me(row){
		row.append("div")
			.classed("col-xs-12", true)
		
		.append("h5")
		.text("Name: " + row.datum().name );
		
		var divs = row.selectAll("div.params")
		.data(d3.entries(row.datum().params))
		.enter()
		.append("div")
			.classed("col-xs-4", true)
			.classed("params", true)
		.classed("text-center", true);
		divs.append("h5")
		.text(function(d){return d.key});
		divs.append("h4")
		.text(function(d){return d.value});
			
			

		
		
	}
	
	return me;
}