<!DOCTYPE html>
<html>

<head>
    <title>Cast Status</title>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Cast Status">
    <meta name="author" content="Pablo Sambuco">
    <link rel="icon" type="image/png" href="/images/favicon.png">
    <link rel="stylesheet" type="text/css" href="/static/estilo.css">
    <script type="text/javascript" src="/static/funciones.js" )"></script>
    <script src="https://kit.fontawesome.com/cea894e75c.js" crossorigin="anonymous"></script>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>

    <script type="text/javascript">
        var ws = "";
        var timer = "";

        function init() {
            timer = window.setInterval(actualizar, 1000);            
        };
        
        function actualizar() {
            ws.send("update");
        };
    
        window.onload = function() {
            var full = window.location.hostname+(window.location.port ? ':' + window.location.port:'');
            ws = new WebSocket("ws://" + full + "/websocket");

            ws.onopen = function () {
                console.log("WebSocket abierto");
                init();
            };
            
            ws.onmessage = function (evt) {
                atender(evt);
            };
            
            ws.onclose = function () {
                console.log("WebSocket cerrado");
                while(timer) {
                    window.clearInterval(timer--);
                };
            };
                        
        };
    </script>
</head>

<body>
    <div id="demo"></div>
    <div class="mdl-layout mdl-js-layout mdl-color--grey-100">
        <main class="mdl-layout__content">
            <div class="mdl-grid" id="grid"></div>
        </main>
    </div>
</body>

</html>
