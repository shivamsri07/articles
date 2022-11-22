Discord handles 4 billion messages per day. At such a huge scale they need to support a high frequencies of queries from a million of users. 
<hr>

## Problems
The main problem they faced was the disk latency. Disk I/Os were taking few milliseconds. Why was it happening?Below a certain query rate, disk latency is not noticeable as storage engine does a great job at handling requests in parallel. But there is a `threshold to number of requests that can be handled in parallel`. Beyond that, certain disk operations will have to wait before the outstanding operations complete. 

At such a high scale, this could lead to issues; one of them being the increase in latency, another one being that `pending disk operations queue can experience backpressure` leading to the requests being timed-out.

## Storage Architecture
Discord uses [Persistent disk](https://cloud.google.com/persistent-disk#documentation) offered by GCP, which can be attached/detached from the servers on the fly, can be resized without downtime, offers replication etc. They are realiable, but they are disks that are not attached directly to the server and are connected over the network. This could add up to the latency by a few milliseconds.

GCP also offers Local SSDs which are directly attached to the servers, but have few problems of there own; If there is an issue with the disk, all the data is gone forever. With local SSDs, we can't take point-in-time snapshot. So for reliability, their primary storage was persistent disks.

## Requirements
Discords system is read heavy, and they were not looking to optimise on the write latency. They have the following requirements:

1. Stay in the GCP ecosystem
2. Point-in-time snapshots for data backup
3. Low latency on the disk reads
4. Database uptime guarantees

One way to acheive this is serve reads from the local SSDs which are directly attached to servers and write to persistent disks. This is a simple caching to serve reads. But how do we handle read operations that fails due to bad sectors on the disk? If there is a bad sector, the database will crash-

```
storage_service - Shutting down communications due to I/O errors until operator intervention
storage_service - Disk error: std::system_error (error system:61, No data available)
```

How to fix the bad sector reads?

## RAID

RAID stands for `Redundant Array of Independent Disks` which creates large reliable data stores from general purpose computer disks. There are different type of RAID configurations, let's look two of the most commonly used configurations-
1. `RAID 0`: RAID 0 splits data evenly across two or more disks. They don't provide any fault tolerance, redundancy and failure of one disk will lead to the failure of whole array of disks. RAID 0 is primarily used in applications that require high performance and are able to tolerate lower reliability.

<p align="center">
    <img src="https://user-images.githubusercontent.com/12581295/203416545-74a16d38-66f6-42cb-b993-0a509c380476.png"
    alt="raid-0" height=480 width=480/>
</p>

2. `RAID 1`: RAID 1 mirrors (replicates) the data across two or more disks. This configuration is useful when read performance or reliability is more important than write performance. The array will continue to operate so long as at least one member drive is operational.

<p align="center">
    <img src="https://user-images.githubusercontent.com/12581295/203416539-cdc06a35-bb9d-43c9-9157-8180818422b2.png"
    alt="raid-1" height=480 width=480/>
</p>

## Using RAID Configuration

Discord run ubuntu on their database server. Linux kernel provides `md` configuration that allows Linux to create software RAID arrays, turning multiple disks into one array. Using RAID1 config between Local SSDs and Persistent Disk won't solve the problem because half of the read requests would still go to persistent disks.

One of the properties that linux provides with md is marking individual devices as `write mostly` which will be `excluded from the normal read balancing and will only be read from when there is no other option`. This can be useful for devices `connected over a slow link`.

So a RAID 1 configuration between Local SSDs and Persistent Disk with Persistent Disk set as write mostly will solve the issue. But in RAID 1, the array can only be as big as the smallest member disk and local SSDs provided by GCP is 375 GB in size, we need multiple Local SSDs attached to the server. 

But these disks need to be converted into one large disk, this is where RAID 0 config comes into action. Having RAID 0 config over the pool of Local SSDs will do the job.

<p align="center">
    <img src="https://user-images.githubusercontent.com/12581295/203416533-7da9ea3f-9421-4f45-8c4b-cd9f75b26f99.png"
    alt="disk-config" height=480 width=480/>
</p>


## Performance Improvement

Having a RAID 0 configuration over Local SSDs and a RAID 1 configuration between Local SSDs and Persistent Disk on the top of it the databases no longer started queueing up disk operations. There was less time spent on I/O operations and the latency is low as the Local SSDs are attached to the host. These performance improvement let them squeeze more and more queries on the same database server, and this helped them optimised the cost as well.


## References
1. [How Discord supercharges network disks for low latency](https://discord.com/blog/how-discord-supercharges-network-disks-for-extreme-low-latency)
2. [RAID Levels](https://en.wikipedia.org/wiki/Standard_RAID_levels)
3. [Write-Mostly RAID 1 Configuration](https://raid.wiki.kernel.org/index.php/Write-mostly)