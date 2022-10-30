Load Balancers are one of the most critical part of any system that has a huge amount of incoming traffic. It works like a 'traffic cop' and directs the request from client to a backend server.

They have the responsibility to keep a track of healthy backend servers and forward requests to them in order to ensure the availability of your service. 

<hr>

## How do LBs forward the requests?

There are several algorithms that Load Balancer uses to chose which server the request should go to-
1. Round-Robin
2. Least-Connection
3. Weighted Round-Robin
4. Least-Response Time

LBs are generally categorized into 2 parts:
1. Layer-7
2. Layer-4

It is done so because of the level they act upon the data found in the `OSI Model`.
Layer-7 is the application layer (HTTP) and Layer-4 is the networking layer (TCP, UDP etc.)

## Implementation

Let's look at the implementation of a toy load balancer, written in Go.

1. Every time a requests come from the client, Load Balancer has to accept it.

```golang
func (lb *Lb) Run() {
    // Run the load balancer at port :8000
	lb_server, err := net.Listen("tcp", ":8000")

	if err != nil {
		fmt.Println(err.Error())
	}
	fmt.Println("Load Balancer is listening on port 8000")
	defer lb_server.Close()
    // Accept every request coming from the client
	for {
		source_connection, err := lb_server.Accept()
		if err != nil {
			fmt.Println("Error connecting to the client", '\n')
		}

        // Forwarding an Incoming Request; sourceConn is the client connection
		go lb.Forward(IncomingReq{
			sourceConn: source_connection,
			timestamp:  time.Time.Unix(time.Now()),
		})
	}
}
```

2. To forward the request, load balancer selects the available backend server (Round Robin in this case), it first tries to connect with it and then forwards the request
```golang
func (lb *Lb) Forward(req IncomingReq) {
    // Get a backend server
	backend := lb.Strategy.GetBackend()

	backendConn, err := net.Dial("tcp", fmt.Sprintf("%s:%s", backend.Ip, backend.Port))
	if err != nil {
		fmt.Printf("Error connecting to backend server at port :: %s\n", backend.Port)
		healthStatus := backend.GetHealthStatus()
		if healthStatus == true {
			backend.SetHealthStatus(false)
		}
		req.sourceConn.Write([]byte("Server is down"))
		req.sourceConn.Close()
		return
	}

	fmt.Printf("Request routed to :: %s:%s\n", backend.Ip, backend.Port)

	if backendConn != nil && backend.GetHealthStatus() != true {
		backend.SetHealthStatus(true)
	}

	backend.IncNumReq()

    // copy from source (client) to the backend
	go io.Copy(backendConn, req.sourceConn)

    // forward request from backend to source (client)
	go io.Copy(req.sourceConn, backendConn)
}
```
3. Health Checks are done every 1 mins and the status of the backend is updated accordingly

```golang
func (b *Backend) IsAlive() bool {
	timeout := 5 * time.Second
	conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%s", b.Ip, b.Port), timeout)
	if err != nil {
		return false
	}

	defer conn.Close()
	return true
}

// This is run as a goroutine
func Heartbeat() {
    // Health check every 1 min
	time := time.NewTicker(time.Minute * 1)
	for {
		select {
		case <-time.C:
			fmt.Println("Starting health checks...")
			for _, v := range lb.Backends {
				if v.IsAlive() == true && v.IsHealthy != true {
					v.SetHealthStatus(true)
				} else if v.IsAlive() == false && v.IsHealthy == true {
					v.SetHealthStatus(false)
				}
			}
			ShowBackendStatus()
			fmt.Println("Finishing health checks...")
		}
	}

}
```

<details>
<summary>Load Balancer in Go</summary>

```golang
package main

import (
	"fmt"
	"io"
	"net"
	"sync"
	"time"
)

type Backend struct {
	Ip        string
	Port      string
	NumReq    int
	IsHealthy bool
	mu        sync.RWMutex
}

type Lb struct {
	Backends []*Backend
	Strategy RoundRobin
}

type IncomingReq struct {
	sourceConn net.Conn
	timestamp  int64
}

type RoundRobin struct {
	Backends []*Backend
	Index    int
}

func InitRR(b []*Backend) {

	strategy = &RoundRobin{
		Backends: b,
		Index:    0,
	}

	lb.Strategy = *strategy
}

func InitLb() {
	backends := []*Backend{
		&Backend{Ip: "localhost", Port: "8080", NumReq: 0, IsHealthy: true},
		&Backend{Ip: "localhost", Port: "8081", NumReq: 0, IsHealthy: true},
		&Backend{Ip: "localhost", Port: "8082", NumReq: 0, IsHealthy: true},
		&Backend{Ip: "localhost", Port: "8083", NumReq: 0, IsHealthy: true},
	}

	lb = &Lb{
		Backends: backends,
	}

	InitRR(backends)
}

func (b *Backend) SetHealthStatus(status bool) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.IsHealthy = status
}

func (b *Backend) IncNumReq() {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.NumReq++
}

func (b *Backend) GetHealthStatus() bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.IsHealthy
}

func (b *Backend) IsAlive() bool {
	timeout := 5 * time.Second
	conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%s", b.Ip, b.Port), timeout)
	if err != nil {
		return false
	}

	defer conn.Close()
	return true
}

func ShowBackendStatus() {
	for _, v := range lb.Backends {
		fmt.Println("===================")
		fmt.Printf("Hostname:%s | Port:%s | NumRequest:%d | Alive:%v\n", v.Ip, v.Port, v.NumReq, v.IsHealthy)
		fmt.Println("===================")
	}
}

func Heartbeat() {
	time := time.NewTicker(time.Minute * 1)
	for {
		select {
		case <-time.C:
			fmt.Println("Starting health checks...")
			for _, v := range lb.Backends {
				if v.IsAlive() == true && v.IsHealthy != true {
					v.SetHealthStatus(true)
				} else if v.IsAlive() == false && v.IsHealthy == true {
					v.SetHealthStatus(false)
				}
			}
			ShowBackendStatus()
			fmt.Println("Finishing health checks...")
		}
	}

}

func (strategy *RoundRobin) GetBackend() *Backend {
	strategy.Index = (strategy.Index + 1) % len(strategy.Backends)
	return strategy.Backends[strategy.Index]
}

func (lb *Lb) Run() {
	lb_server, err := net.Listen("tcp", ":8000")

	if err != nil {
		fmt.Println(err.Error())
	}
	fmt.Println("Load Balancer is listening on port 8000")
	defer lb_server.Close()
	for {
		source_connection, err := lb_server.Accept()
		if err != nil {
			fmt.Println("Error connecting to the client", '\n')
		}

		go lb.Forward(IncomingReq{
			sourceConn: source_connection,
			timestamp:  time.Time.Unix(time.Now()),
		})
	}
}

func (lb *Lb) Forward(req IncomingReq) {
	backend := lb.Strategy.GetBackend()

	if backend.GetHealthStatus() != true {
		fmt.Printf("Server is down :: %s\n", backend.Port)
	}

	backendConn, err := net.Dial("tcp", fmt.Sprintf("%s:%s", backend.Ip, backend.Port))
	if err != nil {
		fmt.Printf("Error connecting to backend server at port :: %s\n", backend.Port)
		healthStatus := backend.GetHealthStatus()
		if healthStatus == true {
			backend.SetHealthStatus(false)
		}
		req.sourceConn.Write([]byte("Server is down"))
		req.sourceConn.Close()
		return
	}

	fmt.Printf("Request routed to :: %s:%s\n", backend.Ip, backend.Port)

	if backendConn != nil && backend.GetHealthStatus() != true {
		backend.SetHealthStatus(true)
	}

	backend.IncNumReq()

	go io.Copy(backendConn, req.sourceConn)
	go io.Copy(req.sourceConn, backendConn)
}

var lb *Lb
var strategy *RoundRobin

func main() {
	InitLb()
	go Heartbeat()
	lb.Run()
}
```
</details>

## Working
Consider a scenario-<br>
4 servers running locally on port: 8080, 8081, 8082, 8083.
Healthchecks done every 1 minute.
`localhost:8083` goes down.

Load balancer gets a request through netcat.
Run `nc 127.0.0.1 8000` on the terminal after the load balancer is up and running.

1. Health Checks
<p align="center">
    <img src="https://user-images.githubusercontent.com/12581295/198895757-a0c0c4d7-cb54-4aad-ac07-57cdbba32133.png"
    alt="query-flow" height=480 width=480/>
</p>

2. Request routing when `localhost:8083` is down
<p align="center">
    <img src="https://user-images.githubusercontent.com/12581295/198895658-9d3c7450-8df7-434a-ba32-9cf565bc82b9.png"
    alt="query-flow" height=480 width=480/>
</p>

3. Health check when `localhost:8083` is down
<p align="center">
    <img src="https://user-images.githubusercontent.com/12581295/198895670-f7880465-337a-432e-b27e-08c480000741.png"
    alt="query-flow" height=480 width=480/>
</p>


You can find the github repo [here](https://github.com/shivamsri07/loadbalancer).

## Reference

1. [Nginx: Load Balancing](https://www.nginx.com/resources/glossary/load-balancing/)
2. [Load Balancing Algorithm](https://www.cloudflare.com/learning/performance/types-of-load-balancing-algorithms/)
<hr>