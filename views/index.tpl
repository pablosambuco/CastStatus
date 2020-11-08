<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Bottle web project template">
    <meta name="author" content="datamate">
    <link rel="icon" type="image/png" href="/images/favicon.png">        
    <title>Project</title>
    <link rel="stylesheet" type="text/css" href="/static/estilo.css">
    <script type="text/javascript" src="/static/volumen.js")"></script>
    <script src="https://kit.fontawesome.com/cea894e75c.js" crossorigin="anonymous"></script>    
</head>
<body>
<div class="mdl-layout mdl-js-layout mdl-color--grey-100">
    <main class="mdl-layout__content">
        <div class="mdl-grid">
            % for cast in data:
            <div class="mdl-card mdl-cell mdl-cell--6-col mdl-cell--4-col-tablet mdl-shadow--2dp">
                <div class="cast">{{cast}}</div>
                % for att in data[cast]:
                    % if(att == "imagen"):             
                        <a href="#">
                        <div class="mdl-card__media" style="background: url({{data[cast][att]}}) 50% 50%">
                        </div>
                        </a>
                    % elif(att == "cast"):
                        <div class="mdl-card__title">
                            <h1 class="mdl-card__title-text">{{cast}}</h1>
                        </div>
                  % end
               % end
               <div class="mdl-card__supporting-text">
               % for att in data[cast]:
                  % if(att == "volumen"): 
                  <div class="player">
                     <i class="fa fa-volume-down"></i>
                     <input type="range" min="1" max="100" class="slider" id="volume-{{cast}}" />
                     <i class="fa fa-volume-up"></i>
                  </div>                  
                  % end
               %end

               % for att in data[cast]:
                  % if(att == "titulo"):             
                     <span class="titulo">{{data[cast][att]}}</span><br />
                  % end
               %end
               % for att in data[cast]:
                  % if(att == "artista"):             
                     <span class="artista">{{data[cast][att]}}</span>
                  % end
               %end

               % for att in data[cast]:
                  % if(att == "volumen"): 
                     <i class="fas fa-step-backward" id="back-{{cast}}"></i>
                     <i class="fas fa-play-circle" id="play-{{cast}}"></i>                          
                     <i class="fas fa-pause-circle" id="pause-{{cast}}"></i>
                     <i class="fas fa-step-forward" id="forward-{{cast}}"></i>
                  % end
               %end

               </div>                
            </div> 
            % end
            <script>
            window.onload=function(){
               % for cast in data:
                  % for att in data[cast]:
                     % if(att == "volumen"): 
                        setVolume("{{cast}}",{{"{:.0f}".format(100*float(data[cast][att]))}});
                     %end
                  % end
               % end
            </script>   
        </div>
    </main>
</div>
    
</body>
</html>
