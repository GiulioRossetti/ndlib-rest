

function App(){
	
	function me(selection){
		console.log("Main APP");
		console.log("API Server", API_HOST);
		
		formCreateExperiment(selection);
	}
	
	formCreateExperiment =  function(selection){
		var form = selection.select("#pnl-create-experiment")
		var q = d3.queue();
		
		q
		.defer(d3.json, API_HOST+"/api/Generators")
		.defer(d3.json, API_HOST+"/api/Networks")
		.await(function(error, generators, networks){
			if(error) console.log(error);
			console.log("generators", generators);
			console.log("networks", networks);
			
			var cmb = form.select(".cmb-network-selection");
			cmb.classed("dropdown", true)
			cmb.append("button")
				.attr({
					class:"btn btn-default dropdown-toggle",
					type:"button",
					id:"drpNetwors",
					"data-toggle":"dropdown",
					"aria-haspopup":true,
					"aria-expanded":true
				})
				.text("Select a network")
				.append("span").classed("caret",true);
			cmb.append("ul")
				.attr({
					"class":"dropdown-menu",
					"aria-labelledby": "drpNetwors"
				})
				.selectAll("li")
				.data(generators.endpoints)
				.enter()
				.append("li")
				.append("a").attr("href","#")
				.text(function(d){return d.name})
				.on("click", function(d){
					console.log("selected", d);
					var params = form.select(".network-parameters");
					// params.selectAll("*").remove();
					
					var divs = params.selectAll("div.form-group")
						.data(d3.entries(d.params)
							.filter(function(p){return p.key!="token"}),
					function(d){return d.key}
						);
					divs.exit().remove();
					// enter
					var divGroup = divs.enter().append("div").classed("form-group",true);
					divGroup.append("label");
					divGroup.append("input")
						.attr({
							class:"form-control",
							type:"text"
						});
					divGroup.append("p")
						.classed("help-block", true)
						
					// update
					divGroup.selectAll("label")
						.text(function(p){return p.key})
						.attr("for", function(p){return d.name+"-"+p.key});
					divGroup.select("input")
						.attr("id", function(p){return d.name+"-"+p.key})
						.on("click", function(e){console.log(e)})
					divGroup.select("p.help-block")
						.text(function(p){return p.value});
					
				});
			
		})
		
	}
	
	return me;
}

var app = App();

	d3.select("body")
	.call(app);

