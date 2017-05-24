function EndPointForm(){
	
	var type = "network";
	var parameters = {};
	
	function me(selection){
		
		
		var cmb = selection.select(".cmb-"+type+"-selection");
		cmb.classed("dropdown", true)
		cmb.append("button")
			.attr({
				class:"btn btn-default dropdown-toggle",
				type:"button",
				id:"drp"+type,
				"data-toggle":"dropdown",
				"aria-haspopup":true,
				"aria-expanded":true
			})
			.text("Select a "+type)
			.append("span").classed("caret",true);
		cmb.append("ul")
			.attr({
				"class":"dropdown-menu",
				"aria-labelledby": "drp"+type
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
				var params = selection.select("."+type+"-parameters");
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
					.text("Create " + type)
					.on("click", me.submit)
			});
		
		
	}
	
	me.type = function(_){
		if(!arguments.length) return type;
		type = _;
		
		return me;
	}
	
	me.parameters = function(){
		return parameters;
	}
	
	me.submit = function(e){
	}
	
	
	return me;
}