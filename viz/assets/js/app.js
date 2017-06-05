function App(){
	var descriptor = {};
	
	me.experiment = Experiment();
	
	function me(selection){
		console.log("Main APP");
		console.log("API Server", API_HOST);
		
		formCreateExperiment(selection);
	}
	
	formCreateExperiment =  function(selection){
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
			
			var epNetwork = EndPointForm();			
			selection.select("#modal-create-network").datum(generators)
			.call(epNetwork);
			
			epNetwork.submit = function(e){
				app.experiment.createExperiment(function(data){
					// experiment created
					dispatch.createdExperiment();
					var parameters = epNetwork.parameters();
					app.experiment.createNetwork(parameters.generators.uri,parameters, function(d){
						app.experiment.getGraph(function(n){
							dispatch.loadedNetwork(n);
							
							var epModel = EndPointForm().type("model");
							selection.select("#modal-create-model").datum(models)
							.call(epModel);
							epModel.submit = function(e){
								console.log(epModel.parameters());
								var mparameters = epModel.parameters();
								app.experiment.createModel(mparameters.generators.uri, mparameters,function(g){
									console.log(g);
									dispatch.createdModel();
									// app.experiment.iterationBunch(100,function(iterations){
//										dispatch.executedIterations(iterations);
//									})
								})
							}
						})
					})
				});
			}
		})
	}
	
	me.descriptor = function(_){
		if(!arguments.length) return descriptor;
		descriptor = _;
		
		return me;
	}
	
	
	return me;
}

var app = App();

	d3.select("body")
	.call(app);
