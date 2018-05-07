Python interface with the squeezebox server using json-rpc

```
from lms import find_server
server = find_server()
print(server)

192.168.0.81:9000 (7.9.0)
 - Livingroom (Squeezebox Boom:192.168.0.147:28468:80%)
 - Kitchen (Squeezebox Radio:192.168.0.15:44194:75%)
```

```
# Play Spotify url
> ./lms livingroom play https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC

# Play Spotify url (alternate format)
> ./lms livingroom play spotify:track:4uLU6hMCjMI75M1A2tKUQC

# Display status
> ./lms status
192.168.1.174:9000 (7.9.1)
- Kitchen    Squeezebox Radio 192.168.1.15    📶  80% stopped            Sveriges R   0%      /      
- Bathroom   Squeezebox Radio 192.168.1.213   📶 100% stopped Magnus Ugg Joey Kille   4% 00.11/04.30 
- Livingroom Squeezebox Radio 192.168.1.139   📶  33% playing Rick Astle Never Gonn   0%      /03.33 
```

Initially somewhat influenced by the [Home Assistant](https://home-assistant.io/) implementation of [squeezebox.py](https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/media_player/squeezebox.py).
