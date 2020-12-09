RaspberryIP = ""
Controller_ServerURL =""
Console_ServerURL =""

function getRaspberryIP()
{
	//http://127.0.0.1:8000/index?pii=192.168.11.3
	url = window.location.href;
	url = url.split("pii=")[1];
	RaspberryIP = url;
	Controller_ServerURL = "http://" + RaspberryIP + ":8001"
	Console_ServerURL = "http://" + RaspberryIP + ":8000"
	console.log(url);
}

function ReadAllSensor() {
	$.get(Console_ServerURL + "/ReadLux",
		function(data) {
		   var LuxTable = document.getElementById("LuxTable");
		   var indexnum = 1
		   LuxTable.innerHTML=''
		   for (const [key, value] of Object.entries(data)) {
			console.log(key, value);
				if (key!= '時間')
				{
					LuxTable.innerHTML+='<tr><th scope="row">'+indexnum+'</th> <td>'+key+'</td><td>'+value+'</td></tr>'
					indexnum +=1
				}
				else
				{
					document.getElementById("lastUpdateTime").innerText = "最後更新時間 : " + value
				}
			}
		}
	);

	$.get(Console_ServerURL + "/ReadPH",
		function(data) {
		   var PH_Table = document.getElementById("PH_Table");
		   var indexnum = 1
		   PH_Table.innerHTML=''
		   for (const [key, value] of Object.entries(data)) {
			console.log(key, value);
			PH_Table.innerHTML+='<tr><th scope="row">'+indexnum+'</th> <td>'+key+'</td><td>'+value+'</td></tr>'
			indexnum +=1
			}
		}
	);

	$.get(Console_ServerURL + "/ReadEC",
		function(data) {
		   var EC_Table = document.getElementById("EC_Table");
		   var indexnum = 1
		   EC_Table.innerHTML=''
		   for (const [key, value] of Object.entries(data)) {
			console.log(key, value);
			EC_Table.innerHTML+='<tr><th scope="row">'+indexnum+'</th> <td>'+key+'</td><td>'+value+'</td></tr>'
			indexnum +=1
			}
		}
	);
}

 
//儲存馬達控制指令
function saveMotorCommand()
{
	//馬達要到達的地點座標 X
	MotorPositionX = document.getElementById("MotorPositionX").value;

	//馬達要到達的地點座標 X
	MotorPositionY = document.getElementById("MotorPositionY").value;
	
	document.getElementById("saveCommandRunResult").innerText = "運行結果 : 上傳中..."
	//XY兩顆馬達有各自的運行時間，所以在編排前也要先設定好
	$.get(Console_ServerURL + "/saveMotorCommand",
		{
			PositionX:MotorPositionX,
			PositionY:MotorPositionY,
		},
		function(data)
		{
			document.getElementById("saveCommandRunResult").innerText = "運行結果 : " + data;
			showCommandList();
		}
	);
}

 
//儲存Jetson nano 的IP
function saveJetsonNanoIP()
{
	//馬達要到達的地點座標 X
	JetsonNanoIP = document.getElementById("JetsonNanoIP").value;
	$.get(Console_ServerURL + "/UpdateJetsonIP",
	{IP : JetsonNanoIP},
	function(data) {
		if (data == "OK")
		{
			alert("儲存成功");
		}
		else
		{
			alert(data);
		}
	}
	);

}

 
//取得JetsonNano 的IP
function getJetsonNanoIP()
{
	$.get(Console_ServerURL + "/GetJetsonIP",
	function(data) {
		document.getElementById("JetsonNanoIP").value = data;
	}
	);
}
//刪除已選擇的指令
function deleteCommandList()
{
	var Selections = $('#commandTable').bootstrapTable('getSelections');
	document.getElementById("saveCommandRunResult").innerText = "運行結果 : 刪除指令中..."
	Selections.forEach(element => {
		console.log(element.id);
		$.get(Console_ServerURL + "/deleteMotorCommand",
			{id : element.id},
			function(data) {
				document.getElementById("saveCommandRunResult").innerText = "運行結果 : OK !"
				showCommandList();
				
			}
		);

	});
}

function runCommandList()
{
	document.getElementById("saveCommandRunResult").innerText = "運行結果 : 正在運行動作列表..."
	$.get(Controller_ServerURL + "/runCommandList",
			function(data) {
				document.getElementById("saveCommandRunResult").innerText = "運行結果 : OK !"
			}
	);
	$.get(Controller_ServerURL + "/updateMotorJob",
			function(data) {
				console.log("updateMotorJob OK");
			}
	);
	
}

//顯示運行指令
function showCommandList()
{	
	var columns = [
		{ 
			field:"Id",  
			title: '#',
			align:'center'
	 	}, 
		{
			field: 'PositionX',
			title: 'X座標',
			align:'center'
		}, 
		{
			field: 'PositionY',
			title: 'Z座標',
			align:'center'
	   	}, 
	];

	$('#commandTable').bootstrapTable('destroy')
	$('#commandTable').bootstrapTable({  
			toolbar:"#toolbar",  
			columns: columns, 
			uniqueId:'Id',
			checkbox:"true",
			pagination:false
			
	});
	var rows = []
	for (var i = 0; i < 10; i++) {
		rows.push({
		  Id: i,
		  PositionX: 'test' + (i),
		  PositionY: '$' + (i),
		  _data:({
			"toggle":"collapse",
			"parent": "#commandTable",
			"target": "#GPIO_Status",
			"href":"#GPIO_Status",
			})

		})
	  }
	$('#commandTable').bootstrapTable('append', rows);
	

	$.get(Console_ServerURL + "/queryCommandList",
		function(data) {
			var indexnum = 1
			var commandList = JSON.parse(data);
			commandList.forEach(element => {
				command = JSON.parse(element);
				$('#commandTable').bootstrapTable('append', command);
				indexnum += 1;
			});
			
			//定時重複運行指令的table如果沒資料會過大，只好非同步去修改高度
			document.getElementsByClassName('fixed-table-body')[0].style.height = "33%";
		}
	);
	
}

//顯示定時運行指令
function showPlanList()
{	
	var columns = [
		{ 
			field:"Id",  
			title: '#',
			align:'center'
	 	}, 
		{
			field: 'Time',
			title: '時間',
			align:'center'
		}, 
	];
	

	$('#Schedule_table').bootstrapTable('destroy')
	$('#Schedule_table').bootstrapTable({  
			toolbar:"#toolbar",  
			columns: columns, 
			uniqueId:'Id',
			checkbox:"true",
			pagination:false
	});

	var rows = []
	for (var i = 0; i < 10; i++) {
		rows.push({
		  Id: i,
		  Time: 'testTime:' + (i),
		})
	  }
	$('#Schedule_table').bootstrapTable('append', rows);

	$.get(Console_ServerURL + "/queryPlanList",
		function(data) {
			var commandList = JSON.parse(data);
			commandList.forEach(element => {
				command = JSON.parse(element);
				$('#Schedule_table').bootstrapTable('append', command);
			});
		}
	);
	$.get(Controller_ServerURL + "/updateMotorJob",
			function(data) {
				console.log("updateMotorJob OK");
			}
	);

}

//設定定時運行排程
function SetMovePlan()
{
	var _Time = document.getElementById("datetimepicker").childNodes[1].value;
	document.getElementById("savePlanRunResult").innerText = "運行結果 : 上傳中..."
	
	$.get(Console_ServerURL + "/savePlanRunning",
		{Time : _Time},
		function(data) {
			document.getElementById("savePlanRunResult").innerText = "運行結果 : OK !"
			showPlanList();
		}
	);
}
function GetHistory() {
	//要下載的歷史資料時間
	var From = document.getElementById("datetimepicker_from").childNodes[1].value;
	var End = document.getElementById("datetimepicker_end").childNodes[1].value;
	document.getElementById("ExcelHistoryLoader").style.display="block"
	$.get(Console_ServerURL + "/getSensorHistory",
			{
				From : From,
				End : End
			},
			function(data) {
				document.getElementById("ExcelHistoryLoader").style.display="none";
				if (data!="OK")
				{
					alert("此日期區間內無資料");
					return;
				}
				var a = document.createElement("a");
				a.href = "http://" + RaspberryIP + ":8000" + "/static/ec.xlsx";
				a.download = 'ec.xlsx';
				a.click();

				var a = document.createElement("a");
				a.href = "http://" + RaspberryIP + ":8000" + "/static/lux.xlsx";
				a.download = 'lux.xlsx';
				a.click();

				var a = document.createElement("a");
				a.href = "http://" + RaspberryIP + ":8000" + "/static/ph.xlsx";
				a.download = 'ph.xlsx';
				a.click();
				console.log(data);
			}
		);
}

//刪除已選擇的指令
function deleteTimeCommand()
{
	var Selections = $('#Schedule_table').bootstrapTable('getSelections');
	document.getElementById("savePlanRunResult").innerText = "運行結果 : 刪除指令中..."
	Selections.forEach(element => {
		console.log(element.id);
		$.get(Console_ServerURL + "/deleteTimeCommand",
			{id : element.id},
			function(data) {
				document.getElementById("savePlanRunResult").innerText = "運行結果 : OK !"
				showPlanList();
			}
		);
	});
}


//顯示距離與馬達運行時間比例
function showDistanceOfTimeProportion()
{
	$.get(Console_ServerURL + "/queryDistanceOfTimeProportion",
		function(data) {
			var StepMotor_config_A = data["StepMotor_DistanceOfTimeProport_A"];
			var StepMotor_config_B = data["StepMotor_DistanceOfTimeProport_B"];
			
			//準備show資料的寄存器
			var ShowValue;
			if (document.getElementById("SetConfigStepMotorNumber").innerText == "A")
			{
				ShowValue = StepMotor_config_A;
			}
			else
			{
				ShowValue = StepMotor_config_B;
			}
			//脈衝寬度
			document.getElementById("StepMotorPulseWidth").value = ShowValue.width;

			//脈衝頻率
			document.getElementById("StepMotorPulseFrequency").value = ShowValue.frequency;
			
			//脈衝次數
			document.getElementById("StepMotorPulseTimes").value = ShowValue.count;
			
			//脈衝距離
			document.getElementById("StepMotorRunMile").value = ShowValue.distance
		}
	);
}

//測試步進馬達
function TestRunStep()
{
	//脈衝寬度
	_PulseWidth = document.getElementById("PulseWidth").value;

	//脈衝頻率
	_PulseFrequency = document.getElementById("PulseFrequency").value;
	
	//脈衝次數
	_Pulse_Count = document.getElementById("Pulse_Count").value;

	_StepMotorNumber = document.getElementById("StepMotorNumber").innerText;
	//步進馬達旋轉方向 = 順時針轉為1,逆時鐘轉為0
	if (document.getElementById("dropdownStepMotor").innerText == "正轉")
	{
		_direction = 1;
	}
	else
	{
		_direction = 0;
	}

	document.getElementById("StepRunResult").innerText = "運行結果 : 運行中 ...";
	$.get(Controller_ServerURL + "/Stepping_Motor",
		{   Pulse_Width  : _PulseWidth,  
			PulseFrequency : _PulseFrequency , 
			Pulse_Count  : _Pulse_Count , 
			direction :_direction,
			StepMotorNumber : _StepMotorNumber
		},
		function(data) {
			document.getElementById("StepRunResult").innerText = "運行結果 :" + data;
		}
	);
}

//儲存距離與馬達運行時間比例的修改結果
function UpdateDistanceOfTimeProportion(_SettingMotorNumber)
{
	//脈衝寬度
	StepMotorPulseWidth = document.getElementById("StepMotorPulseWidth").value
		
	//脈衝頻率
	StepMotorPulseFrequency = document.getElementById("StepMotorPulseFrequency").value
	
	//脈衝次數
	StepMotorPulseTimes = document.getElementById("StepMotorPulseTimes").value
	
	//每個脈衝能推動馬達走多少距離
	StepMotorRunMile = document.getElementById("StepMotorRunMile").value

	//步進馬達設定檔
	StepMotroConfig = {
			"width" : StepMotorPulseWidth,
			"Frequency" : StepMotorPulseFrequency,
			"Count" : StepMotorPulseTimes,
			"distance" : StepMotorRunMile,
			}

	document.getElementById("saveDistanceOfTimeProportionResult").innerText = "運行結果 : 儲存中..."
	$.get(Console_ServerURL + "/UpdateDistanceOfTimeProportion",
		{ SettingMotorNumber: _SettingMotorNumber, value : StepMotroConfig},
		function(data) {
			console.log(data);
			document.getElementById("saveDistanceOfTimeProportionResult").innerText = "運行結果 : OK !"
		}
	);
}

function updateSelectionItem(selectID,replaceValue)
{
	var DropdownString = ""
	document.getElementById(selectID).firstChild.data = replaceValue;
}

function TakePic()
{
	document.getElementById("PicFilePath").firstChild.data = "拍照檔名 : 拍照中...";
	document.getElementById("PicFileUploadResult").firstChild.data = "上傳狀態 : ";
	document.getElementById("PicFilePathLoader").style.display = "block";
	document.getElementById("ShowPic").src = "https://3.blog.xuite.net/3/a/2/7/238328267/blog_3441985/txt/200984010/0.jpg";
	
	socket.emit('TakePic_event', {data: 'Take Pic!'});
}

function UploadPic(filename)
{
	document.getElementById("PicFileUploadResult").firstChild.data = "上傳狀態 : 上傳中...";
	document.getElementById("PicFilePathLoader").style.display = "none";
	document.getElementById("PicFileUploadResultLoader").style.display = "block";
	socket.emit('TakePic_event', {data: 'Upload :'+filename});
}

var socket;
$(document).ready(function(){
	//更新樹梅派IP
	getRaspberryIP();
	socket = io.connect("http://" + RaspberryIP + ":8000" , {path: '/socket.io'});
	socket.on('server_response', function(msg) {
		if (msg["data"].match('TakePic :')!=null)
		{
			document.getElementById("PicFilePath").firstChild.data = "拍照檔名 : " + msg.data.replace("TakePic :","");
			UploadPic(msg.data.replace("TakePic :",""));
		}
		if (msg["data"].match('upload Pic result')!=null)
		{
			document.getElementById("PicFileUploadResult").firstChild.data = "上傳狀態 : " + msg.data.replace("upload Pic result :","");
			document.getElementById("PicFilePathLoader").style.display = "none";
			document.getElementById("PicFileUploadResultLoader").style.display = "none";
		}
		
	});
	socket.on('ImageStream', function(msg) {
		document.getElementById("ShowPic").src = 'data:image/png;base64,' + msg["data"];
	});
	socket.on('connect', function() {
		socket.emit('TakePic_event', {data: 'connected!'});
	});

	$('#datetimepicker').datetimepicker({
		format: 'HH:mm',
		locale: moment.locale('zh-tw')
	});
	$('#datetimepicker_from').datetimepicker({
		format: 'YYYY-MM-DD',
		locale: moment.locale('zh-tw')
	});
	$('#datetimepicker_end').datetimepicker({
		format: 'YYYY-MM-DD',
		locale: moment.locale('zh-tw')
	});


	//顯示命令列表
	showCommandList();

	//顯示步進馬達移動比例
	showDistanceOfTimeProportion(); 

	//讀取所有Sensor
	ReadAllSensor(); 

	//顯示所有排程列表
	showPlanList();

	getJetsonNanoIP();
});