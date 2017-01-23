# Frontier Silicon
 - sudo apt-get install python3-lxml (works better than pip3 install lxml)
 - for platform discovery check does directories
  - components
  - netdisco
 - copy frontier_silicon.py in custom_components  
 - in configuration.yaml:
 
 ```yaml
media_player:
 - platform: frontier_silicon
   host: 192.168.10
   password: 1234
```

