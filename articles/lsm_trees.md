Ever wondered how Cassandra, RocksDB offer such high write throughput, or how systems with high ingestion rates are powered through?

Systems that guarantee high write throughput, have LSM Trees implemented at their core.

### What are LSM Trees?

LSM Trees are append-only logs, in which newer entries are appended to a log file.

There are a few important components of LSM Trees:

1. Memtable
2. WAL
3. SSTable (Sorted String Table)
4. Indexing
5. Compaction
6. Bloom Filters

We will go over them and see how beautifully everything fits in the entire scheme of things.

## Memtable

We know disk writes are expensive. So, how do we achieve high write throughput? How about storing all the writes in the memory and then asynchronously updating the writes to the disk?

Memtable is an in-memory structure. For the sake of simplicity, let us assume that it is similar to a binary search tree, which makes all the data available in sorted order.

So for every write request, the data is stored in the memory, and a successful response is returned to the client.

## WAL

Storing the data in memory is fast, but not durable. If the server crashes, all the data will be lost. So how do we provide durability? WAL or Write Ahead Logs are used to provide durability.

So any request coming is first logged down in the WAL and then updated in the Memtable. This helps the system recover from crashes.

## SSTable (String Sorted Tables)

We only have limited RAM, so we need to store the data on the disk. To do that the data is stored in sorted arrays of key-value pairs on the disk.

Data in memory is sorted, and so on the disk hence making it easier to search the keys efficiently.

Depending upon the size of each log file the filesystem allows, there can be multiple log files at a given point of time. And you guessed it right, it can contain duplicate entries.

## Indexing

How do we speed up the reads? Most of the time the answer is proper indexes on your data. In case of LSM Trees, an index is used to locate the key in an SSTable. One way to index the data is directly point to the offset of the value for their respective key. Anytime the value is changed, we can just update the pointer to keep the indexes in-sync with the changes.

To search any key, its intuitive that we begin the search in the reverse order, i.e from the newly created log file.

## Compaction

As the number of log files keep on growing, there is a need of compaction process that will Merge the different log files into one, remove the duplicate key and keep its latest entry, delete the keys and create a new, merged log file.

This job runs in the background and is also responsible for updating the indexes that helps us locate the key in its corresponding SSTable.

Since we are using append only mode, we can easily bloat up the size of the SSTable, the number of entries could be in millions. We do have a compaction task that’s running in the background, but that also take time considering there is a huge amount of data that needs to be merged, serving a read request must be optimised that does not eat up your system resources.

One optimisation is if we could know beforehand, whether or not a key is present on the disk.

## Bloom Filters

A Bloom filter is a probabilistic data structure, which at a high level helps you check if a key is present or not in the system with O(1) complexity in memory.

Presence of bloom filters optimise the read for the keys not present in the table, but for the keys that are present, serving reads for them is still going to be expensive.

## Summary

All the designs has their own fair share of trade-offs. In LSM Trees we take a hit on serving reads but we get very high write throughput. Below is the flow chart showing how the read and write requests are served.
