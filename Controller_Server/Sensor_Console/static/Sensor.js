Controller_ServerURL = "http://192.168.11.3:8001"
function ReadAllSensor() {
	$.get("/ReadLux",
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

	$.get("/ReadPH",
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

	$.get("/ReadEC",
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
	//取得馬達類型
	MotorType = document.getElementById("MotorType").innerText;

	//馬達旋轉方向
	MotorDirection = document.getElementById("MotorDirection").innerText;

	//馬達要到達的地點座標
	MotorPosition = document.getElementById("MotorPosition").value;

	//遇到光遮斷器要停止?
	ifGettingLightCutter = document.getElementById("ifGettingLightCutter").checked

	
	//要走多少距離需要幾秒
	RunningTime =  parseInt(MotorPosition) /  parseInt(document.getElementById("StepMotorRunMile").value)

	//持續時間 = (次數 / 頻率) * 要運行距離是參考距離的幾倍
	Duration = parseFloat(parseInt(document.getElementById("StepMotorPulseTimes").value) / parseInt(document.getElementById("StepMotorPulseFrequency").value)) * RunningTime
	
	document.getElementById("saveCommandRunResult").innerText = "運行結果 : 上傳中..."
	$.get("/saveMotorCommand",
		{
			Direction:MotorDirection,
			Duration:Duration,
			Position:MotorPosition,
			Setting_type:MotorType,
			LightCutter:ifGettingLightCutter,
		},
		function(data)
		{
			document.getElementById("saveCommandRunResult").innerText = "運行結果 : " + data;
			showCommandList();
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
			field: 'Action',
			title: '指令',
			align:'center'
		}, 
		{
			field: 'Direction',
			title: '方向',
			align:'center'
	   	}, 
		{
			field: 'Position',
			title: '座標位置',
			align:'center'
	   	}, 
		{
			field: 'LightCutter',
			title: '遇光遮斷器停止',
			align:'center'
		}, 
		{
			field: 'DateTime',
			title: '創建時間',
			align:'center'
		}
	];

	$('#commandTable').bootstrapTable('destroy')
	//bootstrap table初始化数据
	$('#commandTable').bootstrapTable({  
			toolbar:"#toolbar",  
			columns: columns, 
			uniqueId:'Id',
			checkbox:"true",
			pagination:false
			
	});

	$.get("/queryCommandList",
		function(data) {
	
			var indexnum = 1
			var commandList = JSON.parse(data);
			commandList.forEach(element => {
				command = JSON.parse(element);
				
				Direction = command["Direction"];
				if (Direction==0)
				{
					command["Direction"] = "反轉";
				}
				else
				{
					command["Direction"] = "正轉";
				}

				LightCutter = command["LightCutter"];
				if (LightCutter==0)
				{
					command["LightCutter"] = "否";
				}
				else
				{
					command["LightCutter"] = "是";
				}
				command['Id'] = indexnum.toString()
				$('#commandTable').bootstrapTable('append', command);
				indexnum += 1;
			});
		}
	);
}



//顯示距離與馬達運行時間比例
function showDistanceOfTimeProportion()
{
	$.get("/queryDistanceOfTimeProportion",
		function(data) {
			var StepMotor_config = data["StepMotor_DistanceOfTimeProportion"];
			var BrushlessMotor_config = data["BrushlessMotor_DistanceOfTimeProportion"];
			//脈衝寬度
			document.getElementById("StepMotorPulseWidth").value = (StepMotor_config.split(":")[0].replace("width=",""));
			
			//脈衝頻率
			document.getElementById("StepMotorPulseFrequency").value = (StepMotor_config.split(":")[1].replace("Frequency=",""));
			
			//脈衝次數
			document.getElementById("StepMotorPulseTimes").value = (StepMotor_config.split(":")[2].replace("Count=",""));
			
			//脈衝距離
			document.getElementById("StepMotorRunMile").value = (StepMotor_config.split(":")[3].replace("cm=",""));
			
			document.getElementById("BrushlessMotorRunMile").value = (BrushlessMotor_config.split(":")[0].replace("cm",""));
			document.getElementById("BrushlessMotorRunSecond").value = (BrushlessMotor_config.split(":")[1].replace("s",""));
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
	_value = ""
	
	//脈衝寬度
	StepMotorPulseWidth = document.getElementById("StepMotorPulseWidth_" + _SettingMotorNumber).value
		
	//脈衝頻率
	StepMotorPulseFrequency = document.getElementById("StepMotorPulseFrequency_" + _SettingMotorNumber).value
	
	//脈衝次數
	StepMotorPulseTimes = document.getElementById("StepMotorPulseTimes_" + _SettingMotorNumber).value
	
	//脈衝距離
	StepMotorRunMile = document.getElementById("StepMotorRunMile_" + _SettingMotorNumber).value

	//width=10:Frequency=10:Count=28:cm=10
	_value ="width=" +StepMotorPulseWidth+ ":" +
			"Frequency=" + StepMotorPulseFrequency + ":" +
			"Count=" + StepMotorPulseTimes+ ":" +
			"cm=" + StepMotorRunMile
		
	$.get("/UpdateDistanceOfTimeProportion",
		{ Setting_type: _SettingMotorNumber, value : _value},
		function(data) {
			console.log(data);
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
	socket = io.connect();
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

	showCommandList();

});