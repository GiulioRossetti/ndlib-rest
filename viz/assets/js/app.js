function App(){
	
	me.experiment = Experiment();
	
	function me(selection){
		console.log("Main APP");
		console.log("API Server", API_HOST);
		
		formCreateExperiment(selection);
	}
	
	formCreateExperiment =  function(selection){
		var form = selection.select("#pnl-create-network")
		var q = d3.queue();
		
		q
		.defer(d3.json, API_HOST+"/api/Generators")
		.defer(d3.json, API_HOST+"/api/Networks")
		.defer(d3.json, API_HOST+"/api/Models")
		.await(function(error, generators, networks, models){
			if(error) console.log(error);
			console.log("generators", generators);
			console.log("networks", networks);
			console.log("models", models)
			
			form.datum(generators)
			.call(EndPointForm());
		})
		
	}
	
	return me;
}

var app = App();

	d3.select("body")
	.call(app);

	var exp = Experiment();
