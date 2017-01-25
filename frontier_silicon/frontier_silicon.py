"""
Support for functionality to interact with Frontier Silicon Devices (Medion, Hama, Auna,...) devices.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/media_player.frontier_silicon/
"""
import logging

import asyncio
import requests
import voluptuous as vol

import requests
from lxml import objectify
from urllib.parse import urlparse

from homeassistant.components.media_player import (SUPPORT_NEXT_TRACK, SUPPORT_PAUSE, SUPPORT_PREVIOUS_TRACK, SUPPORT_SEEK,
    SUPPORT_PLAY_MEDIA, SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET, SUPPORT_VOLUME_STEP, SUPPORT_STOP, SUPPORT_TURN_OFF, SUPPORT_TURN_ON,
    SUPPORT_PLAY, SUPPORT_SELECT_SOURCE, MediaPlayerDevice, PLATFORM_SCHEMA )
from homeassistant.const import (
    STATE_OFF, STATE_PLAYING, STATE_PAUSED, STATE_UNKNOWN, CONF_HOST, CONF_PORT, CONF_NAME, CONF_PASSWORD)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

SUPPORT_FRONTIER_SILICON = SUPPORT_PAUSE | SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE |  SUPPORT_VOLUME_STEP | \
    SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK | SUPPORT_SEEK | \
    SUPPORT_PLAY_MEDIA | SUPPORT_PLAY | SUPPORT_STOP | SUPPORT_TURN_ON | SUPPORT_TURN_OFF | SUPPORT_SELECT_SOURCE

DEFAULT_HOST = '192.168.1.11'
DEFAULT_PORT = 80
DEFAULT_PASSWORD = '1234'
DEVICE_URL = 'http://{0}:{1}/device'

FRONTIER_SILICON_CONFIG_FILE = 'frontier_silicon.conf'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): cv.string,
})


# pylint: disable=unused-argument
#def setup_platform(hass, config, add_devices, discovery_info=None):
@asyncio.coroutine
def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the Frontier Silicon platform."""
    
    if discovery_info is not None:
         yield from async_add_entities([FrontierSiliconDevice(discovery_info, DEFAULT_PASSWORD)])
         return True

    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    password = config.get(CONF_PASSWORD)

    try:
        if host and port and password :
            yield from async_add_entities([FrontierSiliconDevice(DEVICE_URL.format(host, port), password)])
            _LOGGER.info('Frontier Silicon device %s:%s -> %s', host, port, password)
            return True
        else:
            _LOGGER.warning('Frontier Silicon device missing config parameter %s:%s -> %s', host, port, password)
    except requests.exceptions.RequestException:
        _LOGGER.error('Could not connect to Frontier Silicon device at %s:%s -> %s', host, port, password)


class FrontierSiliconDevice(MediaPlayerDevice):
    """Representation of a Frontier Silicon device on the network."""

    def __init__(self, device_url, password):
        """Initialize the Frontier Silicon API device."""
        
        self._device_url = device_url
        self._password = password
        self._state = STATE_UNKNOWN
        
        self._name = FSAPI(self._device_url, self._password).friendly_name
        self._title = None
        self._mute = None
        self._source = None
        self._source_list = None
        self._media_image_url = None
        self._volume_steps = None

    def get_fs(self):
        return FSAPI(self._device_url, self._password)

    ##################################  properties ##########################
    @property
    def should_poll(self):
        """Device should be polled."""
        return True

    @property
    def name(self):
        """Return the device name."""
        return self._name

    @property
    def media_title(self):
        """Title of current playing media."""
        return self._title

    @property
    def supported_media_commands(self):
        """Flag of media commands that are supported."""
        return SUPPORT_FRONTIER_SILICON

    @property
    def state(self):
        """Return the state of the player."""
        return self._state

    # source
    @property
    def source_list(self):
        """List of available input sources."""
        return self._source_list

    @property
    def source(self):
        """Name of the current input source."""
        return self._source

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        return self._media_image_url

    ############################### async actions ########################################
    @asyncio.coroutine
    def __title(self):
        title = ''
        artist = self.get_fs().play_info_artist
        album = self.get_fs().play_info_album
        info_name = self.get_fs().play_info_name
        info_text = self.get_fs().play_info_text
        
        if artist:
           title += artist
        if album:
           title += ' ('+album+')'
        if info_name:
           if title:
              title += ' - '
           title += info_name
        if info_text:
           title += ': ' + info_text
        
        return title

    @asyncio.coroutine
    def __state(self):
        status = self.get_fs().play_status
        return {
            'playing': STATE_PLAYING,
            'paused': STATE_PAUSED,
            'stopped': STATE_OFF,
            'unknown': STATE_UNKNOWN,
            None: STATE_OFF,
        }.get(status, STATE_UNKNOWN)

    @asyncio.coroutine
    def __source(self):
        return str(self.get_fs().mode)

    @asyncio.coroutine
    def __media_image_url(self):
        return self.get_fs().play_info_graphics

    #@asyncio.coroutine
    #def __volume_steps(self):
    #    return self.get_fs().volume_steps

    @asyncio.coroutine
    def __mute(self):
        return self.get_fs().mute

    @asyncio.coroutine
    def __name(self):
        return self.get_fs().friendly_name

    @asyncio.coroutine
    def __source_list(self):
        return self.get_fs().mode_list

    @asyncio.coroutine
    def async_update(self):
        """Get the latest date and update device state."""

        if not self._name:
           self._name = yield from self.__name()
       
        if not self._source_list:
           self._source_list = yield from self.__source_list()
        
        #if not self._volume_steps:
        #   self._volume_steps = yield from self.__volume_steps()

        self._title = yield from self.__title()
        self._state = yield from self.__state()
        self._source = yield from self.__source()
        self._mute = yield from self.__mute()
        self._media_image_url = yield from self.__media_image_url()

    #################### actions #####################

    # power control
    @asyncio.coroutine
    def async_turn_on(self):
        """Turn on the device."""
        self.get_fs().power = True

    @asyncio.coroutine
    def async_turn_off(self):
        """Turn off the device."""
        self.get_fs().power = False
    
    @asyncio.coroutine
    def async_media_play(self):
        """Send play command."""
        yield from self.get_fs().play()

    @asyncio.coroutine
    def async_media_pause(self):
        """Send pause command."""
        yield from self.get_fs().pause()

    @asyncio.coroutine
    def async_media_play_pause(self):
        """Send play/pause command."""
        yield from self.get_fs().play()

    @asyncio.coroutine
    def async_media_stop(self):
        """Send play/pause command."""
        yield from self.get_fs().pause()

    @asyncio.coroutine
    def async_media_previous_track(self):
        """Send previous track command (results in rewind)."""
        yield from self.get_fs().prev()

    @asyncio.coroutine
    def async_media_next_track(self):
        """Send next track command (results in fast-forward)."""
        yield from self.get_fs().next()
    
    # mute
    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._mute
    
    @asyncio.coroutine
    def async_mute_volume(self, mute):
        """Send mute command."""
        self.get_fs().mute = mute

    # volume
    @asyncio.coroutine
    def async_volume_up(self):
        """Send volume up command."""
        currentVolume = self.get_fs().volume
        self.get_fs().volume = (currentVolume + 1)

    @asyncio.coroutine
    def async_volume_down(self):
        """Send volume down command."""
        currentVolume = self.get_fs().volume
        self.get_fs().volume = (currentVolume - 1)

    @asyncio.coroutine
    def async_set_volume_level(self, volume):
        """Set volume command."""
        self.get_fs().volume = volume

    def select_source(self, source):
        """Select input source."""
        self.get_fs().mode = source


################################ FSAPI ####################################
class FSAPI(object):

    PLAY_STATES = {
        0: 'stopped',
        1: 'unknown',
        2: 'playing',
        3: 'paused',
    }

    def __init__(self, fsapi_device_url, pin):
        self.pin = pin
        self.sid = None
        self.webfsapi = None
        self.fsapi_device_url = fsapi_device_url

        self.webfsapi = self.get_fsapi_endpoint()
        self.sid = self.create_session()

    def get_fsapi_endpoint(self):
        r = requests.get(self.fsapi_device_url)
        doc = objectify.fromstring(r.content)
        return doc.webfsapi.text

    def create_session(self):
        doc = self.call('CREATE_SESSION')
        return doc.sessionId.text

    def call(self, path, extra=None):
        if not self.webfsapi:
            raise Exception('No server found')

        if type(extra) is not dict:
            extra = dict()

        params = dict(
            pin=self.pin,
            sid=self.sid,
        )

        params.update(**extra)

        r = requests.get('%s/%s' % (self.webfsapi, path), params=params)
        if r.status_code == 404:
           return None 

        return objectify.fromstring(r.content)
 
    def __del__(self):
        self.call('DELETE_SESSION')

    ####################### handlers #########################################

    def handle_get(self, item):
        return self.call('GET/{}'.format(item))

    def handle_set(self, item, value):
        doc = self.call('SET/{}'.format(item), dict(value=value))
        if doc is None:
           return None
        
        return doc.status == 'FS_OK'

    def handle_text(self, item):
        doc = self.handle_get(item)
        if doc is None:
           return None

        return doc.value.c8_array.text or None

    def handle_int(self, item):
        doc = self.handle_get(item)
        if doc is None:
           return None

        return int(doc.value.u8.text) or None

    # returns an int, assuming the value does not exceed 8 bits
    def handle_long(self, item):
        doc = self.handle_get(item)
        if doc is None:
           return None

        return int(doc.value.u32.text) or None

    def handle_list(self, item):
        doc = self.call('LIST_GET_NEXT/'+item+'/-1', dict(
            maxItems=100,
        ))

        if doc is None:
           return []

        if not doc.status == 'FS_OK':
            return []

        ret = list()
        for index, item in enumerate(list(doc.iterchildren('item'))):
            temp = dict(band=index)
            for field in list(item.iterchildren()):
                temp[field.get('name')] = list(field.iterchildren()).pop()
            ret.append(temp)

        return ret

    def collect_labels(self, items):
        if items is None:
           return []
   	
        return [ str(item['label']) for item in items if item['label'] ]

    ###########################################

    @property
    def play_status(self):
        status = self.handle_int('netRemote.play.status')
        return self.PLAY_STATES.get(status)

    @property
    def play_info_name(self):
        return self.handle_text('netRemote.play.info.name')

    @property
    def play_info_text(self):
        return self.handle_text('netRemote.play.info.text')

    @property
    def play_info_artist(self):
        return self.handle_text('netRemote.play.info.artist')

    @property
    def play_info_album(self):
        return self.handle_text('netRemote.play.info.album')

    @property
    def play_info_graphics(self):
        return self.handle_text('netRemote.play.info.graphicUri')

    @property
    def volume_steps(self):
        return self.handle_int('netRemote.sys.caps.volumeSteps')

    # Read-write ##################################################################################

    #1=Play; 2=Pause; 3=Next (song/station); 4=Previous (song/station)
    def play_control(self, value):
        return self.handle_set('netRemote.play.control', value)
    
    def play():
        return play_control(1)

    def pause():
        return play_control(2)

    def next():
        return play_control(3)

    def prev():
        return play_control(4)

    # Volume
    def get_volume(self):
        return self.handle_int('netRemote.sys.audio.volume')

    def set_volume(self, value):
        return self.handle_set('netRemote.sys.audio.volume', value)

    volume = property(get_volume, set_volume)

    # Frienldy name
    def get_friendly_name(self):
        return self.handle_text('netRemote.sys.info.friendlyName')

    def set_friendly_name(self, value):
        return self.handle_set('netRemote.sys.info.friendlyName', value)

    friendly_name = property(get_friendly_name, set_friendly_name)

    # Mute
    def get_mute(self):
        return bool(self.handle_int('netRemote.sys.audio.mute'))

    def set_mute(self, value=False):
        return self.handle_set('netRemote.sys.audio.mute', int(value))  

    mute = property(get_mute, set_mute)

    # Power
    def get_power(self):
        return bool(self.handle_int('netRemote.sys.power'))

    def set_power(self, value=False):
        return self.handle_set('netRemote.sys.power', int(value))

    power = property(get_power, set_power)

    # Modes
    @property
    def modes(self):
        return self.handle_list('netRemote.sys.caps.validModes')

    @property
    def mode_list(self):
        return self.collect_labels(self.modes)

    def get_mode(self):
        m = None
        intMode = self.handle_long('netRemote.sys.mode')
        for mo in self.modes:
          if mo['band'] == intMode:
            m = mo['label']
        return m

    def set_mode(self, value):
        m = -1
        for mo in self.modes:
          if mo['label'] == value:
            m = mo['band']
        
        self.handle_set('netRemote.sys.mode', m)      

    mode = property(get_mode, set_mode)

    @property
    def duration(self):
        return self.handle_long('netRemote.play.info.duration')

