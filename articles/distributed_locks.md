Distributed locks are very crucial when you want to have different processes working with a shared resources in a mutually exclusive way. Locks as we know are very crucial to have a synchronization between different processes.

Let's understand this with an example. Suppose there's a queue and multiple clients (consumers) are trying to read the messages from it. In order to ensure that one message is consumed by only one client at a time, clients would require to take a lock on the queue, process the message and then release the lock. We do locking for the purpose of `efficiency and correctness`

If this were to be same execution environment, we could have used mutex and semaphores. But since it's a distributed setting, we need to a central registry where clients know which one of them has the locks. 

## Requirements

Think what all things we would need in order to synchronize different clients for the queue. A database to hold `<key, value>` pair that will hold who owns the lock at that point of time. A way to release the locks? Some type of `TTL` that would expire the `<key, value>` pair if a client process crashes. And we would need that the transactions are atomic in nature.

We can use Redis, as we get all of these things out of the box. So we don't have to re-invent the wheel.

## Distributed locks implementation

Think how do we use mutex and semaphores to prevent critical section of our codes:

```go
    mutex.Lock()
        critical_section
    mutex.Unlock()
```

In order to do distributed locking, we can take a similar approach:

```go
    acquire_lock(resource_name)
        critical_section
    release_lock(resource_name)
```

<b>1. Acquire lock on the resource:</b>

To acquire the lock, we will use `setNX` in redis. This set key to hold string value if key does not exist. When key already holds a value, no operation is performed

An infinite loop because we want that clients (consumers) don't sit idle. They look to acquire the lock on the resource.

```go
func AcquireLock(resource_name, client_id string, ttl int) int {

	for {
        // set the resource_id as key, and client_id as the value, with ttl of 10 seconds
		res := client.SetNX(ctx, resource_name, client_id, time.Duration(time.Duration.Seconds(10)))
        // value is set in redis
		if res.Val() == true {
			fmt.Printf("Acquiring Lock :: %v\n", client_id)
			return 1
		} else {
            // someone has already acquired the lock so loop again
			continue
		}
	}
}
```


<b>2. Release the lock</b>

This is fairly simple. We need to find who currently holds the lock, and then delete it. 
`The only caveat is this should be wrapped in one transaction`. 
Redis LUA Scripts comes to rescue here.

```go
// Lua script
release_script = `
		if redis.call('get', KEYS[1]) == ARGV[1] then
			return redis.call('del', KEYS[1])
		else
			return 0
		end
	`

func ReleaseLock(resource_name, client_id string) bool {
	release_lock := redis.NewScript(release_script)
	key := []string{resource_name}
	fmt.Printf("Releasing Lock :: %v\n", client_id)
	_, err := release_lock.Run(ctx, client, key, client_id).Int()
	if err != nil {
		fmt.Printf("Can not release lock: %v\n", err)
	}
	return true
}
```

You can find the output of a small prototype that used distributed locks for synchronization of threads (consumers)

<details>
<summary>Output</summary>
<p align="center">
    <img src="https://user-images.githubusercontent.com/12581295/199495861-7f24ee9b-a7cf-4b9a-ba45-f071c17dc6bf.png"
    alt="distributed-locks-output"/>
</p>
</details>

## Improvements

We are using a single redis instance, that can become a SPoF. In order to avoid that, we can use multiple instances. You can read more about it in [Redlock Algorithm](https://redis.io/docs/reference/patterns/distributed-locks/#the-redlock-algorithm:~:text=have%20such%20guarantees.-,The%20Redlock%20Algorithm,-In%20the%20distributed)

You can find the problem statement [here](https://github.com/arpitbbhayani/system-design-questions/blob/master/queue-consumers.md).

You can find the source code [here](https://github.com/shivamsri07/distributed-locking).

## References
1. [Redlock Algorithm](https://redis.io/docs/manual/patterns/distributed-locks/)
2. [Lua Scripts](https://redis.io/docs/manual/programmability/eval-intro/#interacting-with-redis-from-a-script)
3. [How to do distributed locking - Martin Kleppmann](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)

