ServerURL = "http://127.0.0.1:8001"
function ReadAllSensor() {
    $.get(ServerURL + "/ReadLUX",
        function(data) {
           var LuxTable = document.getElementById("LuxTable");
           var indexnum = 1
           LuxTable.innerHTML=''
           for (const [key, value] of Object.entries(data)) {
            console.log(key, value);
            LuxTable.innerHTML+='<tr><th scope="row">'+indexnum+'</th> <td>'+key+'</td><td>'+value+'</td></tr>'
            indexnum +=1
            }
        }
    );

    $.get(ServerURL + "/ReadPH",
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

    $.get(ServerURL + "/ReadEC",
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

 

//增加運行指令
function showCommandList()
{
    Command_table.innerHTML=''
    $.get("/queryCommandList",
        function(data) {
           var Command_table = document.getElementById("Command_table");
           var indexnum = 1
           
            var commandList = JSON.parse(data);
            commandList.forEach(element => {
                command = JSON.parse(element)
                Action = command["Action"];
                Duration = command["Duration"];
                Direction = command["Direction"];
                Position = command["Position"];
                if (Direction==0)
                {
                    Direction = "反轉";
                }
                else
                {
                    Direction = "正轉";
                }
                Command_table.innerHTML+='<tr><th scope="row">'+indexnum+'</th> <td>'+Action+'</td><td>'+Direction+'</td><td>'+Position+'</td><td>' + Duration+'秒</td></tr>'
                indexnum += 1;
            });
        }
    );
}


//顯示距離與馬達運行時間比例
function showDistanceOfTimeProportion()
{
    Command_table.innerHTML=''
    $.get("/queryDistanceOfTimeProportion",
        function(data) {
           var Command_table = document.getElementById("Command_table");
           var indexnum = 1
           
            var commandList = JSON.parse(data);
            commandList.forEach(element => {
                command = JSON.parse(element)
                Action = command["Action"];
                Duration = command["Duration"];
                Direction = command["Direction"];
                Position = command["Position"];
                if (Direction==0)
                {
                    Direction = "反轉";
                }
                else
                {
                    Direction = "正轉";
                }
                Command_table.innerHTML+='<tr><th scope="row">'+indexnum+'</th> <td>'+Action+'</td><td>'+Direction+'</td><td>'+Position+'</td><td>' + Duration+'秒</td></tr>'
                indexnum += 1;
            });
        }
    );
}

function updateSelectionItem(selectID,replaceValue)
{
    var DropdownString = ""
    document.getElementById(selectID).firstChild.data = replaceValue;
}

function TestTakePic()
{
    $.get("http://192.168.11.7:8000/Pic",
        function(data) {
            document.getElementById("PicFilePath").firstChild.data = "拍照檔名 :" + data;
        }
);

}