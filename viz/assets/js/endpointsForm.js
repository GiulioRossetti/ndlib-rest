function EndPointForm(){
	
	
	function me(selection){
		var parameters = {};
		
		var cmb = selection.select(".cmb-network-selection");
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
			.data(selection.datum().endpoints)
			.enter()
			.append("li")
			.append("a").attr("href","#")
			.text(function(d){return d.name})
			.on("click", function(d){
				console.log("selected", d);
				parameters = {generators:d};
				var params = selection.select(".network-parameters");
				params.selectAll("button.create").remove();
				params.selectAll("div.form-group").remove();
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
					.on("change", function(e){
						parameters[e.key] = this.value;
					});
				divGroup.select("p.help-block")
					.text(function(p){return p.value});
					
				params.append("button")
					.attr({
						type:"button",
						class:"btn btn-default create"
					})
					.text("Create network")
					.on("click", function(e){
						app.experiment.createExperiment(function(data){
							// experiment created
							dispatch.createdExperiment();
							app.experiment.createNetwork(parameters.generators.name,parameters, function(d){
								app.experiment.getGraph(function(n){
									dispatch.loadedNetwork(n);
								})
								
							})
							
						});
					})
			});
		
		
	}
	
	
	return me;
}