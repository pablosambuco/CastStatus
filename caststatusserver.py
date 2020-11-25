# -*- coding: utf-8 -*-
"""Modulo conteniendo las clases necesarias para el manejo de chromecasts
"""

# pylint: disable=line-too-long,too-few-public-methods,fixme

import time
import datetime
import logging
import json
import zeroconf
from geventwebsocket import WebSocketError
import pychromecast


class CastStatusServer:
    """Clase con funcionalidades de busqueda y control de
    Chromecasts en una red local

    Esta clase contiene una instancia de tipo CastStatusSingleton.

    Todos los metodos son derivados a esa instancia unica que atiende todos
    los pedidos.
    """

    instance = None

    def __new__(cls):
        if not CastStatusServer.instance:
            CastStatusServer.instance = CastStatusServer.CastStatusSingleton()
        return CastStatusServer.instance

    def __getattr__(self, name):
        """Singleton getattr"""
        return getattr(self.instance, name)

    def __setattr__(self, name, value):
        """Singleton setattr"""
        return setattr(self.instance, name, value)

    class CastStatusSingleton:
        """Singleton (?)"""

        def __init__(self):
            self.casts = {}
            self.status = {}

            listener = pychromecast.CastListener()
            zconf = zeroconf.Zeroconf()
            browser = pychromecast.discovery.start_discovery(listener, zconf)
            time.sleep(1)
            for _, service in listener.services.items():
                cast = pychromecast.get_chromecast_from_service(service, zconf)
                if service[2] == "Chromecast":
                    if service[3] not in self.casts:
                        cast.wait()
                        slist = StatusListener(self, cast)
                        cast.register_status_listener(slist)
                        mlist = StatusMediaListener(self, cast)
                        cast.media_controller.register_status_listener(mlist)
                        self.casts[service[3]] = cast

            pychromecast.stop_discovery(browser)

        def __str__(self):
            return str(self.casts)

        def init(self):
            """Devuelve el listado de nombres de chromecasts

            Returns:
                list listado de nombres de chromecasts
            """
            return self.casts

        def update(self):
            """Devuelve el listado de nombres de chromecasts

            Returns:
                list listado de nombres de chromecasts
            """

            lista = []
            for key in self.status:
                aux = {}
                aux["cast"] = key
                aux["contenido"] = self.status[key]
                lista.append(aux)
            respuesta = {}
            respuesta["chromecasts"] = lista

            return respuesta

        def update_status(self, listener, status):
            """Actualiza el diccionario de estados

            Args:
                listener (Listener): objeto listener que llama a este metodo
                status (MediaStatus): respuesta del cast con el cambio de estado
            """
            # TODO Deal with too-many-branches
            # labels mejora

            cast = str(listener.cast.device.friendly_name)
            aux_list = listener.__class__.__name__

            # si no existe la clave la creo como un diccionario vacio
            self.status[cast] = self.status.get("cast",{})
            #if cast not in self.status:
            #    self.status[cast] = {}

            try:
                status_image = status.images[0].url
            except AttributeError:
                status_image = None
            except KeyError:
                status_image = None

            # TODO Tener en cuenta el metadataType (https://developers.google.com/cast/docs/reference/messages#MediaStatus)
            #  con este dato se puede decidir què atributos buscar y simplificar el diccionario de estados
            #  Tambien estaria muy bien determinar que comandos estan permitidos (atributo supportedMediaCommands) para enviar al frontend que botones deben estar disponibles
            #  0: GenericMediaMetadata: title, subtitle, images
            #  1: MovieMediaMetadata: title, subtitle, images, studio
            #  2: TvShowMediaMetadata: seriesTitle, subtitle, season, episode, images
            #  3: MusicTrackMediaMetadata: title, albumName, artist, images
            #  4: PhotoMediaMetadata: title, artist, location
            #
            #  MediaStatus: playerState, supportedMediaCommands, volume
            if aux_list == "StatusMediaListener":
                attr_lookup = {
                    "volume_level": "{:.2f}".format(status.volume_level),
                    "title": status.title,
                    "subtitle": status.media_metadata.get("subtitle"),
                    "series_title": status.series_title,
                    "season": status.season,
                    "episode": status.episode,
                    "artist": status.artist,
                    "album_name": status.album_name,
                    "player_state": status.player_state,
                    "track": status.track,
                    "images": status_image,
                }
            else:  # StatusListener
                attr_lookup = {
                    "volume_level": "{:.2f}".format(status.volume_level),
                    "volume_muted": status.volume_muted,
                    "status_text": status.status_text,
                    "icon_url": status.icon_url,
                }

            key_lookup = {
                "volume_level": "volume",
                "title": "title",
                "subtitle": "subtitle",
                "series_title": "series",
                "season": "season",
                "episode": "episode",
                "artist": "artist",
                "album_name": "album",
                "track": "track",
                "images": "image",
                "player_state": "state",
                "volume_muted": "mute",
                "status_text": "text",
                "icon_url": "icon",
            }

            for attr in attr_lookup:
                if hasattr(status, attr) and attr_lookup[attr] is not None:
                    self.status[cast][key_lookup[attr]] = attr_lookup[attr]

            subs_lookup = {
                "image": "icon",
                "title": "text",
                "subtitle": "series",
                "artist": "subtitle",
            }
            # Completo datos con sus reemplazos
            for cast in self.status:
                for orig in subs_lookup:
                    subs = subs_lookup[orig]
                    if subs in self.status[cast]:
                        if orig not in self.status[cast]:
                            self.status[cast][orig] = self.status[cast][subs]
                        elif (
                            self.status[cast][orig] != self.status[cast][subs]
                        ):
                            del self.status[cast][subs]

            state_lookup = {
                "IDLE": "REMOVE",
                "PLAYING": "PLAYING",
                "BUFFERING": "PLAYING",
                "PAUSED": "PAUSED",
            }

            # Ajusto el estado a uno de los valores que maneja el frontend
            self.status[cast]["state"] = state_lookup[
                self.status[cast].get("state", "PAUSED")
            ]

            now = datetime.datetime.now()
            self.status[cast]["timestamp"] = now.strftime("%Y-%m-%d %H:%M:%S")

            #  Si el reproductor esta en un estado desconocido, lo marco
            if listener.cast.media_controller.status.player_state == "UNKNOWN":
                self.status[cast]["state"] = "REMOVE"

        def atender(self, wsock):
            """Funcion para atender los mensajes del WebSocket

            Args:
                wsock (WebSocket): objeto donde se recibiran los mensajes

            Raises:
                exc: Si ocurre una excepcion de WebSocket se envia
            """
            logger = logging.getLogger()
            try:
                message = wsock.receive()

                if message == "update":
                    log = message + " recibido"
                    logger.info("%s. Enviando listado de estados.", log)
                    respuesta = json.dumps(self.update())
                    wsock.send(respuesta)
                elif message:
                    log = message + " recibido"
                    comando = message.split(",")
                    if len(comando) == 2 and comando[0] == "play":
                        self.play(cast=comando[1])
                    elif comando[0] == "pause":
                        self.pause(cast=comando[1])
                    elif comando[0] == "back":
                        self.back(cast=comando[1])
                    elif comando[0] == "forward":
                        self.forward(cast=comando[1])
                    elif comando[0] == "volume":
                        self.volume(cast=comando[1], value=comando[2])
                    else:
                        logger.info("%s", log)
            except WebSocketError as exc:
                raise exc

        def back(self, cast):
            """Back

            Args:
                cast (Chromecast): Cast en el que se aplica el back
            """
            try:
                self.casts[cast].media_controller.rewind()
                self.casts[cast].media_controller.queue_prev()
            except AttributeError:
                pass

        def play(self, cast):
            """Play

            Args:
                cast (Chromecast): Cast en el que se aplica el play
            """
            try:
                self.casts[cast].media_controller.play()
            except AttributeError:
                pass
            except KeyError:
                pass

        def pause(self, cast):
            """Pause

            Args:
                cast (Chromecast): Cast en el que se aplica el pause
            """
            try:
                self.casts[cast].media_controller.pause()
            except AttributeError:
                pass
            except KeyError:
                pass

        def forward(self, cast):
            """Forward

            Args:
                cast (Chromecast): Cast en el que se aplica el forward
            """
            try:
                # self.casts[cast].media_controller.skip()
                # TODO Arreglar el forward
                #  esto tendria que ser seek al final (hoy va a -5 segundos del final)
                #  la propiedad es status.duration
                #  https://developers.google.com/cast/docs/reference/messages#MediaComm
                #  Seek: Sets the current position in the stream. Triggers a
                #   STATUS event notification to all sender applications.
                #   If the position provided is outside the range of valid
                #   positions for the current content, then the player should
                #   pick a valid position as close to the requested position as
                #   possible.
                self.casts[cast].media_controller.queue_next()
            except AttributeError:
                pass
            except KeyError:
                pass

        def volume(self, cast, value):
            """Cambio de Volumen

            Args:
                cast (Chromecast): Cast en el que se aplica el volumen
                value (int): Valor de 0 a 100 para aplicar
            """
            try:
                self.casts[cast].set_volume(float(value) / 100)
            except AttributeError:
                pass
            except KeyError:
                pass


class StatusListener:
    """Clase listener para cambios de estado"""

    def __init__(self, server, cast):
        self.server = server
        self.cast = cast

    def new_cast_status(self, status):
        """Metodo para enviar nuevos estados

        Args:
            status (Response): Estado que se envia al diccionario de estados
        """
        self.server.update_status(self, status)


class StatusMediaListener:
    """Clase listener para cambios de contenido multimedia"""

    def __init__(self, server, cast):
        self.server = server
        self.cast = cast

    def new_media_status(self, status):
        """Metodo para enviar nuevos estados

        Args:
            status (Response): Estado que se envia al diccionario de estados
        """
        self.server.update_status(self, status)
