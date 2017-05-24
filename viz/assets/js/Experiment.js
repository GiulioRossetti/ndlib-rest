

function Experiment(){
	var token;
	var network;
	var models = [];
	
	
	function me(){
		
	}
	
	me.token = function(){
		return token;
	}
	
	me.createExperiment = function(_){
		send(API_HOST+"/api/Experiment", "GET", null, _)
	}
	
	me.describe = function(_){
		console.log(""+token);
		var params = {
			token: ""+token
		}
		send(API_HOST+"/api/ExperimentStatus", "POST", params, _)
	}
	
	me.destroy = function(_){
		send(API_HOST+"/api/Experiment","DELETE",{token:token}, _)
	}
	
	me.getGenerators = function(_){
		send(API_HOST+"/api/Generators", "GET", null, _)
	}
	
	me.getNetworks = function(_){
		send(API_HOST+"/api/Networks", "GET", null, _)
	}
	
	me.getModels = function(_){
		send(API_HOST+"/api/Models", "GET", null, _)
	}
	
	me.createNetwork = function(name, params, _){
		params.token = token;
		send(API_HOST+"/api/Generators/"+name, "put",params, _)
	}
	
	me.getGraph = function(_){
		send(API_HOST+"/api/GetGraph","post",{token:token},_);
	}
	
	me.createModel = function(name, params, _){
		params.token = token;
		send(API_HOST+"/api/"+name, "put",params, _)
	}
	
	me.iterationBunch = function(num, _){
		send(API_HOST+"/api/IterationBunch", "post",{token:token, bunch:num, models:""}, _)
	}
	
	function send(url, method, parameters, callback){
		$.when(
			$.ajax({method : method,
				url : url,
				crossDomain : true,
				data: parameters,
				cache : false
			}).fail(function(error){console.log(error)})
		)
		.done(function(data){
			console.log(data);
			if(data.token) token = data.token;
			if(callback) 
				callback(data);
						
		});
	}
	
	return me;
}