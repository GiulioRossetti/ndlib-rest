
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
		}
		
		
		panel.select("div.panel-heading")
			.text("Model: " + row.datum().key);
		
		var stats = panel.select("div.stats")
			.selectAll("h5.stats")
		.data(d3.entries(row.datum().value));
			
		stats.enter()
			.append("h5")
			.classed("stats",true)
		.classed("col-md-3",true);
		
		stats.text(function(d){return d.key+":"+d.value});
	}
	
	return me;
}