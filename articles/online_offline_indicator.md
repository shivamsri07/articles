Any system that is designed can scale in multiple ways, and as with everything in the world, there is no free lunch. Each system is designed in such a way that caters to the problem at hand i.e there is no generalizing a system, but the core remains the same.

Let’s begin.

## Requirements:

Let’s assume that we have 1M users on a social media site. And at a time, we need to show any 10 online connections/friends/followers per user. That makes it 1M writes/min and 10M reads.

## Approach:

Let’s design things from the first principle. What we need is basically a way to store userId and the status.

Our schema will look something like userId | status

We can have two APIs:
```
GET /status/user/:userId
POST /status/user/:userId
There are a few chokepoints with the above APIs:
```

With the GET route, calling the API for every user will overwhelm our database. Instead, we could go for batching. We can send a batch of 10 userId and get the status.
We can ping the POST route every ‘X’ minutes, but how will we notify if the user goes offline? Let’s imagine a scenario where the app crashes, the user will be shown online for an infinite amount of time. So we need something that can autodelete the entry in our DB. Something like a Time To Live property…Redis?
So the above POST route can be updated to POST /status which can be called every ‘X’ min, which will SET the <Key, Value> pair as <userId, 1> where 1 is online with a TTL of 5 mins.

But there’s another caveat with this approach. What if a user goes offline? The entry in Redis will be there for 5 minutes, and for that period it will be shown online, which is not a good UX.

To make things real-time, we can opt for a different communication channel — Websockets. This will be covered in future blogs.

### Let’s change our requirements a bit:

Now we want to show ‘Last active X mins ago’ for an offline user. How do we do it?

We need to store the timestamp (heartbeats) against the userId, from which we can calculate the last seen of a particular user. We can opt for any database MySQL, Redis, etc.

And to handle the scale of 1Mn+ users, we can opt for sharding and horizontal scaling by creating a leader-follower setup for each shard, but that has its own complexity.

But before jumping on these distributed systems jargons, we need to leverage and squeeze the most out of what’s already on the table. One amazing property that every database provides is Connection Pooling.
```
Connection Pooling maintains a pool of connection from client to the database which avoids creating a new TCP connection with the database for every request. This has the following advantage-

1. We save time and resource of 3-way TCP handshake.

2. Cost of CPU reduces and your database does not get overwhelmed, because let’s be honest, creating and maintaing TCP connections is a very costly and intensive CPU operation.
```

Now that we have developed a system for online/offline indicators, if we just look at the system this can be extended to Failure Detection System, an Orchestrator System, etc.