# Sangheili
Custom SOCKS proxy for redteam. Each outgoing connection gets a random ip address.


## Setup
No libraries are needed to run the tool

```
python3 sangheili.py
```


## Client Usage
It is recommended to set the porxy information in an environment variable
```
export SOCKS_SERVER=192.168.22.3
export SOCKS_PORT=1080
```
### HTTP
```
export http_proxy="socks5://$SOCKS_SERVER:$SOCKS_PORT"
export https_proxy=$http_proxy
export HTTP_PROXY=$http_proxy
export HTTPS_PROXY=$http_proxy
```

### SSH
To proxy SSH traffic, make sure you have your environment variables installed.

For a permanant configuration, update your SSH client config with the following lines
```bash
#Host *  # Match all hosts
Host 10.*.*.*  # Match certain IPs
    ProxyCommand ncat --proxy $SOCKS_SERVER:$SOCKS_PORT --proxy-type socks5 %h %p
```
Then you may call SSH as normal.

For a one-time usage:
```
ssh -o ProxyCommand="ncat -x $SOCKS_SERVER:$SOCKS_PORT %h %p" root@10.80.100.1
```
