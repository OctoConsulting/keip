# IntegrationRoute Webhook Server Benchmark

### Results

A simple load test of the `sync` endpoint exposed by the IntegrationRoute lambda web
server. The benchmark was performed
using the [Apache Bench](https://httpd.apache.org/docs/2.4/programs/ab.html) tool, configured to
send
1000 requests by 10 concurrent connections (far exceeding the expected production load).

```text
Server Software:        uvicorn
Server Hostname:        192.168.39.239
Server Port:            30700

Document Path:          /sync
Document Length:        1729 bytes

Concurrency Level:      10
Time taken for tests:   1.018 seconds
Complete requests:      1000
Failed requests:        0
Total transferred:      1856000 bytes
Total body sent:        1657000
HTML transferred:       1729000 bytes
Requests per second:    981.95 [#/sec] (mean)
Time per request:       10.184 [ms] (mean)
Time per request:       1.018 [ms] (mean, across all concurrent requests)
Transfer rate:          1779.78 [Kbytes/sec] received
                        1588.95 kb/s sent
                        3368.73 kb/s total

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       1
Processing:     1   10  22.4      2      82
Waiting:        1    8  20.3      2      82
Total:          1   10  22.4      2      82

Percentage of the requests served within a certain time (ms)
  50%      2
  66%      2
  75%      3
  80%      5
  90%      9
  95%     79
  98%     81
  99%     82
 100%     82 (longest request)
```

The web server was running in a single kubernetes pod with the following resource requests:

```yaml
  resources:
    requests:
      memory: "64Mi"
      cpu: "100m"
    limits:
      memory: "128Mi"
      cpu: "250m"
```

### Running the test

The following instructions show how to replicate the load test by exposing the k8s service
externally and running `ab` from the host. Alternatively, you could run `ab` from a pod deployed to
k8s.

1. Expose the endpoint outside the cluster by changing the `integrationroute-webhook` service to a
   NodePort.

```yaml
# core-controller.yaml
apiVersion: v1
kind: Service
metadata:
  name: integrationroute-webhook
  namespace: metacontroller
spec:
  type: NodePort
  selector:
    app: integrationroute-webhook
  ports:
    - port: 80
      targetPort: webhook-http 
```

2. Deploy the keip controller

```shell
cd keip/operator
make controller/deploy
```

3. Get the NodePort's proxy port (30700 in the example).

```shell
> kubectl -n metacontroller get svc
integrationroute-webhook   NodePort   10.99.50.111   <none>        80:30700/TCP   21m
```

4. Run the benchmark (Make sure `ab` is installed before this step)

```shell
ab -n 1000 -c 10 -T 'application/json' -p ../json/full-iroute-request.json http://<node-ip>:<node-port>/sync
```