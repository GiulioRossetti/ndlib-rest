
function ModelView(){
	var panel;
	var trendData = {};
	
	
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
			// toolbar
			var body = panel.append("div")
				.attr("class","panel-body")
				.append("div")
				.text("model descriptor");
				
			// charts	
			var charts = panel.append("div")
				.classed("panel-body",true)
				.classed("charts",true);
				
			charts.append("div")
				.classed("line-chart",true)
				.classed("col-md-6",true)
				.append("svg")
				.attr("width","100%")
				.attr("height",400);
				
			
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
	
	
	
	
	me.trendData = function(_){
		if(!arguments.length) return trendData;
		trendData = _;
		
		console.log("sums", trendData);

		var chart = nv.models.lineChart();
		panel.select("div.charts .line-chart svg")
		.datum(d3.entries(trendData).map(function(d){
			return {
				key: d.key,
				values: d.value.map(function(v,i){
					return {x:i, y:v}
				}),
				// color: nodeColor(d.key)
			}
		}))
		.call(chart);
			
		
		return me;
	}
	
	return me;
}