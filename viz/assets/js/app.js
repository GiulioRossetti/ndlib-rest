

function App(){
	
	function me(selection){
		console.log("Main APP");
		
	}
	
	return me;
}

var app = App();
d3.select("body")
.call(app);