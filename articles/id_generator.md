IDs are very critical part in any system. There has to be a way to uniquely indentify an object be it a user, photos, comment etc. Most commonly used ids are auto-incrementing bigints, that are 64 bits and range from 
2 ^ (-63) to 2 ^ (63-1), which is a gigantic limit. 

But what if you are in a distributed setup, and you have a sharded database. Auto-incrementing integers won't work because that will lead to duplicate ids being assigned to different entities. How can we uniquely identify objects in our system in a distributed setup? This is the problem that instgram solved beautifully...

<hr>

## Requirements

Instagram reached at a point where they wanted to shard their data for quick response time and better indexing. They decided to stick to PostgreSQL as their primary data store, but before they decided to shard the data, they needed a way to figure out how to uniquely identify entities in their system. They came up with the following requirements:

1. Generated IDs should be sortable by time
2. IDs should be 64 bits so that they can easily fit in memory
3. System should not introduce more 'moving parts' and should be cost efficient [simple system scale :)]

They tried various options like Snowflake which is twitters in-house id generation service, and Flickr's DB Ticket Service, but both of them added complexities which were not adhering to requirement #3.

They also looked at UUIDs, but they require more space (around 96 bits or higher) and aren't naturally sorted.

### Epoch Timestamps

To make the ids sortable by time, it is intuitive to use the epoch timestamps in the id. They used this to populate the first 41 bits (which gave them 41 years of ids with custom epoch).
    `id |= (now_millis - our_epoch) << (64-41)`

Here, `our_epoch` is the custom epoch equal to `1293820200` ( Jan 1st, 2011 )

### Shard id

They have created many logical shards within a single database server i.e [postgres schema](https://hasura.io/learn/database/postgresql/core-concepts/1-postgresql-schema/#:~:text=Schema%20is%20a%20collection%20of,different%20features%20into%20different%20schemas.). They populate the next 13 bits with this. Suppose a user with id 31341 inserts a photo, and there are 2000 logical shards. We populate the next 13 bits with 31341 % 2000 = 1341
    `id |= 1341 << (64 - 41 - 13)`

### Auto-incrementing sequence

Now the remaining 10 bits is filled with an auto-incrementing sequence, by taking the modulus with 1024 (2 ^10). Let's say there are 5000 ids already generated, so the next one will be-
    `id |= 5001 % 10`

### PL/SQL

Combining everything, we get a PL script that will return an id that whenever an insert happens-

```sql

CREATE OR REPLACE FUNCTION "user_id_1-500".next_id(OUT result bigint)
 RETURNS bigint
 LANGUAGE plpgsql
AS $function$
DECLARE
    our_epoch bigint := 1314220021721;
    seq_id bigint;
    now_millis bigint;
    shard_id int := 5;
BEGIN
    SELECT nextval('"table_id_seq"') % 1024::BIGINT INTO seq_id;
    SELECT FLOOR(EXTRACT(EPOCH FROM clock_timestamp()) * 1000) INTO now_millis;
    result := (now_millis - our_epoch) << 23;
    result := result | (shard_id <<10);
    result := result | (seq_id);
END;
    $function$
```

If we want to create a `photos` table, we use the above script as follow-

```sql

CREATE TABLE IF NOT EXISTS "user_id_1-500".photos (
    "id" bigint NOT NULL DEFAULT insta5.next_id(),
    "userid" bigint NOT NULL,
    ...rest of table schema...
  )
```

Now we know that indexes in SQL are sorted by default. If we create an index on `userid and id`, we can leverage range queries for a particular user to get the photos and those queries will be very optimised. On top of it we can introduce caching to optimise the /GET calls further. 

## Output

Here's an example of how the ids look like:
<p align="center">
    <img src="https://user-images.githubusercontent.com/12581295/205492187-4ef1700d-1823-4f10-a9e3-24bdd6b535b8.png"
    alt="id-generator" height=480 width=480/>
</p>

You can find the code repo [here.](https://github.com/shivamsri07/id-generation/tree/main)

Refrences:
1. [Sharding and IDs](https://instagram-engineering.com/sharding-ids-at-instagram-1cf5a71e5a5c)
2. [Twitter's Snowflake](https://blog.twitter.com/engineering/en_us/a/2010/announcing-snowflake)
3. [Flickr's DB Ticket Server](https://code.flickr.net/2010/02/08/ticket-servers-distributed-unique-primary-keys-on-the-cheap/)
