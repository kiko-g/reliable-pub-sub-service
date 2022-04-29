# Reliable Pub Sub Service

## Documentation

This section is the README inside the [docs](docs) folder.

## Requirements

- `ZeroMQ`
- `Python3.9.6`

```sh
pip install pyzmq   # make sure pip corresponds to your python installation
```

## Execution

### Standard executions

```bash
cd src/scripts
bash linux.sh <server_amount> <client_amount>
```

```bat
cd src/scripts
./windows.bat <server_amount> <client_amount>
```

### Custom executions

#### Format

```sh
# open a shell for each command below
python src/proxy.py
python src/server.py <id>
python src/client.py <id> (<bool_spawn_errors> <xpub_port> <rep_proxy_port>)

# you may want to spawn multiple servers and clients
# make sure server/client IDs are not repeated
```

#### Example

```sh
# open a shell for each command below
python src/proxy.py
python src/server.py 1
python src/client.py 1
python src/client.py 2
python src/client.py 3
python src/client.py 4
```

## Description

Project guide [here](https://web.fe.up.pt/~pfs/aulas/sdle2021/projs/proj1.html)


## Team

1. [Francisco Goncalves](https.github.com/kiko-g)
2. [Inês Quarteu](https.github.com/InesQuarteu)
3. [Jéssica Nascimento](https.github.com/)
4. [Rúben Almeida](https.github.com/arubenruben)
