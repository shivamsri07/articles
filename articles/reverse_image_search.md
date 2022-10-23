Canva has a huge media database. And as the files grow in number, there comes a need to tackle the problem of moderation and deduplication at scale. Let's see how they built a content matching system that has two very fundamental yet very important concept at the core:

1. Hashing
2. Hamming Distance

<hr>

## Hashing
Every image has certain set of raw bytes. Hashing provides us with a way to generate a `unique key` that can identify a media file. 

Hashing algorithms like `MD5, SHA` generate a unique hash key. Even if the two images are virtually similar, they can never return the same hash as even the `slightest change of pixel can change the output`.

With the above mentioned hash algorithm, there is a chance of collision, and that may result in a `false matching`.

Above algorithms can only work if the images are a perfect copy of each other.

### Can we leverage a property of image that is common among all?

Think about `pixels`. All images are made up of pixels. If we can do the hashing based on pixels rather than the raw bytes, we might be able to `increase the true positives`.

<hr>

## Perceptual Hashing or pHash:

[Perceptual hashing](https://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html) is a image hashing technique that generate hashes based on the features of the image. It uses the low frequency features (that describes the overall structure of the image) and does a [Discrete Cosine Transformation](https://en.wikipedia.org/wiki/Discrete_cosine_transform)

When we have pHashes of two image we can find the similarity using some threshold. Enters, `Hamming Distances`. We can decide a threshold value of `Hamming Distance Score` and then use it to find visually similar images.

Let's get hands-on. I am going to use two images here:

1. Original Tom N' Jerry Image
![https://user-images.githubusercontent.com/12581295/197401433-bdc908c8-dcd6-4a0f-b929-db500cb45787.png](https://user-images.githubusercontent.com/12581295/197401433-bdc908c8-dcd6-4a0f-b929-db500cb45787.png)

2. Edited Tom N' Jerry Image (Just added one caption)
![https://user-images.githubusercontent.com/12581295/197401423-aad546c6-711e-4ebf-9afa-a819faeedfe7.png](https://user-images.githubusercontent.com/12581295/197401423-aad546c6-711e-4ebf-9afa-a819faeedfe7.png)

Let's see how two algorithms perform:
<hr>

```python
image = ['/content/original_tom_n_jerry.png', '/content/edited_tom_n_jerry.png']

# Using MD5 Hashing Algorithm
from PIL import Image
import hashlib
for name in image:
  md5hash = hashlib.md5(Image.open(name).tobytes())
  print(md5hash.hexdigest())

'''
/content/original_tom_n_jerry.png e8f5674cbb98468d917816065799ee1d
/content/edited_tom_n_jerry.png 9ed7aa4d6123fdac0d9c7850b34e1ef3
'''

# Using Perceptual Hashing Alogrithm
# Refer this for implementation :: https://medium.com/analytics-vidhya/image-search-engine-using-image-hashing-technique-in-python-e6749dacc8f7
import cv2
import numpy as np
from scipy import spatial


def hash_array_to_hash_hex(hash_array):
  # convert hash array of 0 or 1 to hash string in hex
  hash_array = np.array(hash_array, dtype = np.uint8)
  hash_str = ''.join(str(i) for i in 1 * hash_array.flatten())
  return (hex(int(hash_str, 2)))

def hash_hex_to_hash_array(hash_hex):
  # convert hash string in hex to hash values of 0 or 1
  hash_str = int(hash_hex, 16)
  array_str = bin(hash_str)[2:]
  return np.array([i for i in array_str], dtype = np.float32)

image_hash_dict = {}

# for every image calcuate PHash value
for name in image:
  print(f'IMAGE :: {name}')
  img = cv2.imread(name)

  # resize image and convert to gray scale
  img = cv2.resize(img, (64, 64))
  img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  img = np.array(img, dtype = np.float32)

  # calculate dct of image 
  discrete_cosine_transform = cv2.dct(img)

  # to reduce hash length take only 8*8 top-left block 
  # as this block has more information than the rest
  dct_block = discrete_cosine_transform[:8, : 8]
  print(f'DCT_BLOCK :: {dct_block}')

  # caclulate mean of dct block excluding first term i.e, dct(0, 0)
  dct_average = (dct_block.mean() * dct_block.size - dct_block[0, 0]) / (dct_block.size - 1)

  # convert dct block to binary values based on dct_average
  print(f'DCT_AVG :: {dct_average}',)
  dct_block[dct_block < dct_average] = 0.0
  dct_block[dct_block != 0] = 1.0

  # store hash value
  print(f'UPDATED_DCT_BLOCK :: {dct_block}', '\n')
  image_hash_dict[name] = hash_array_to_hash_hex(dct_block.flatten())

'''
>> IMAGE :: /content/original_tom_n_jerry.png
DCT_BLOCK :: [[ 1.29692344e+04  1.40461499e+03  3.99981262e+02 -2.42549255e+02
   1.06066406e+03 -3.67240234e+02  1.48269730e+02 -3.13680237e+02]
 [ 7.48587952e+02  1.30641327e+02  2.73384888e+02 -6.47182739e+02
  -3.12571564e+02  1.63975082e+02 -9.58401966e+00  5.04885292e+01]
 [ 5.08714081e+02 -2.07494965e+02 -5.44520020e+02  3.74523376e+02
  -2.39382874e+02 -3.58026123e+01  2.35321770e+01  1.10725830e+02]
 [ 6.75657288e+02 -4.95788879e+02 -3.47913971e+02  4.34586670e+02
   4.26520538e+02 -6.77895355e+01  2.83852844e+01 -1.55653351e+02]
 [ 4.01443085e+02  2.23502625e+02 -2.60381042e+02 -3.15573090e+02
  -2.92770294e+02  1.76831497e+02  7.99414682e+00 -3.10230865e+02]
 [-8.15359039e+01 -8.74169235e+01  7.93431549e+01  4.54406189e+02
  -3.91858917e+02 -1.22717430e+02  3.36040649e+02 -5.47030525e+01]
 [-3.26222595e+02 -2.66791046e+02  3.07147217e+02  1.84807083e+02
  -1.19918411e+02 -1.47101639e+02  4.78893852e+00 -1.01411613e+02]
 [ 2.31577789e+02 -2.56568503e+00  1.05423012e+02  1.43106308e+02
   9.55043888e+00 -2.05274918e+02 -1.11117554e+02  1.06220924e+02]]
DCT_AVG :: 40.48714967757937
UPDATED_DCT_BLOCK :: [[1. 1. 1. 0. 1. 0. 1. 0.]
 [1. 1. 1. 0. 0. 1. 0. 1.]
 [1. 0. 0. 1. 0. 0. 0. 1.]
 [1. 0. 0. 1. 1. 0. 0. 0.]
 [1. 1. 0. 0. 0. 1. 0. 0.]
 [0. 0. 1. 1. 0. 0. 1. 0.]
 [0. 0. 1. 1. 0. 0. 0. 0.]
 [1. 0. 1. 1. 0. 0. 0. 1.]] 

>> IMAGE :: /content/edited_tom_n_jerry.png
DCT_BLOCK :: [[ 1.3867453e+04  7.3583435e+02  5.3682471e+02 -4.7707205e+02
   8.9776465e+02 -1.4240540e+02  2.3666966e+02 -2.5654938e+02]
 [ 4.1499265e+02 -2.2394464e+00  2.6475357e+02 -1.7258113e+02
  -4.6867651e+02  4.5258617e+01 -1.5776544e+01  3.3063247e+00]
 [ 1.4025417e+03 -2.5115355e+02 -5.3722406e+02  3.4367365e+02
  -3.9801938e+02 -3.4816422e+01 -8.1801651e+01  1.5816457e+02]
 [-1.2673072e+02 -3.5775760e+02 -2.6946167e+02  3.0736111e+02
   3.9261386e+02  8.2609329e+01  9.1250526e+01 -3.8809078e+01]
 [ 4.4361240e+02 -1.5657190e+01  2.6389163e+02 -1.0455832e+02
  -5.2298163e+02  8.3169754e+01  1.9485940e+00 -9.7062744e+01]
 [-6.8474518e+02  1.7028603e+02  2.3999489e+02  1.3067067e+02
  -6.5934593e+01 -2.3454993e+02  1.8872412e-01  7.2629944e+01]
 [-1.9108728e+02 -4.1267911e+02  1.6142911e+02  8.7537346e+01
   1.6713728e+02  1.4015883e+02 -1.5853391e+02  1.6303723e+02]
 [ 2.5254871e+02  3.7318933e+02 -7.6174408e+01 -4.3435345e+02
   1.5744434e+02  2.5112665e+02 -1.7132718e+02  2.4001232e+01]]
DCT_AVG :: 36.45878286210318
UPDATED_DCT_BLOCK :: [[1. 1. 1. 0. 1. 0. 1. 0.]
 [1. 0. 1. 0. 0. 1. 0. 0.]
 [1. 0. 0. 1. 0. 0. 0. 1.]
 [0. 0. 0. 1. 1. 1. 1. 0.]
 [1. 0. 1. 0. 0. 1. 0. 0.]
 [0. 1. 1. 1. 0. 0. 0. 1.]
 [0. 0. 1. 1. 1. 1. 0. 1.]
 [1. 1. 0. 0. 1. 1. 0. 0.]] 
'''

print(image_hash_dict)

'''
{
    '/content/original_tom_n_jerry.png': '0xeae59198c43230b1', 
    '/content/edited_tom_n_jerry.png': '0xeaa4911ea4713dcc'
}

'''

for image_name in image_hash_dict.keys():
  print(f'{image_name} Hash Array :: {hash_hex_to_hash_array(image_hash_dict[image_name])}')
  distance = spatial.distance.hamming(
    hash_hex_to_hash_array(image_hash_dict[image_name]), 
    hash_hex_to_hash_array(image_hash_dict['/content/edited_tom_n_jerry.png'])
  )
  print(f'{image_name} Hamming Distance {distance}', '\n')


'''
/content/original_tom_n_jerry.png Hash Array :: [1. 1. 1. 0. 1. 0. 1. 0. 1. 1. 1. 0. 0. 1. 0. 1. 1. 0. 0. 1. 0. 0. 0. 1. 1. 0. 0. 1. 1. 0. 0. 0. 1. 1. 0. 0. 0. 1. 0. 0. 0. 0. 1. 1. 0. 0. 1. 0. 0. 0. 1. 1. 0. 0. 0. 0. 1. 0. 1. 1. 0. 0. 0. 1.]
/content/original_tom_n_jerry.png Hamming Distance 0.296875 

/content/edited_tom_n_jerry.png Hash Array :: [1. 1. 1. 0. 1. 0. 1. 0. 1. 0. 1. 0. 0. 1. 0. 0. 1. 0. 0. 1. 0. 0. 0. 1. 0. 0. 0. 1. 1. 1. 1. 0. 1. 0. 1. 0. 0. 1. 0. 0. 0. 1. 1. 1. 0. 0. 0. 1. 0. 0. 1. 1. 1. 1. 0. 1. 1. 1. 0. 0. 1. 1. 0. 0.]
/content/edited_tom_n_jerry.png Hamming Distance 0.0 
'''
```

Using md5 algorithm produces two very different hash, while using `perceptual hashes` we get a hamming distance score of `0.29` which is very close to zero, and hence we can safely say that images are similar.

Now that we know how the algorithm works, let's get started with designing the system, which uses another amazing data structure. 

<hr>

## Design Decision

We know we can get the similar images by computing hamming distances of two perceptual hash. But how do we know which are the suitable candidates for that comparison.

We know that we can't do a full text search as pHash of images are different. Let's consider the pHash we got from our example. User uploads the `edited_tom_n_jerry` image and we need to know weather we have a similar image or not.
Let's take the p_hash we got from the example,

```
original_image: eae59198c43230b1
edited_image: eaa4911ea4713dcc
```

Can we find some similarity? Let's try to find similar substring in these hashes.

```
similar = ['ea', '91'] 
```

If we can split the hash in parts of two, and store the hash of original image in a way that allow us to fetch it's `image_id`, we can calculate the hamming distance and return the results i.e image is similar or not.

Suppose we have N images in our system, so we need a data structure that will allow us to fetch the `image_id` of M images that may or may not be similar to the uploaded image, but are a candidate.

For this use case, we can use [Multi-Index Hashing](https://www.cs.toronto.edu/~norouzi/research/papers/multi_index_hashing.pdf).

We can prove this by [pegion-hole principle](https://math.hmc.edu/funfacts/pigeonhole-principle/), that if there are n slots that the hash is split into, and n — 1 character changes to distribute, it is guaranteed that at least one of the slots has no characters changed.

In the above example, we had 8 slots, and 6 modifications to distribute, so using the pegionhole principal we can safely say that 2 slots are not changed.

```
Deciding the split factor and how to filter out the candidate image depends upon 
the type of hash and type of images uploaded. For simplicity, let us assume that the split factor is 2 
and if we get a single match, we say that the image is a candidate image.
```

## Storing the data, and query

Canva used DynamoDB to leverage the `partition key` and `sort key` property. Here, the partion key is the hash of the image and the image_id is the sort key. Let's store the original image hash in database. So our data looks something like-

![https://user-images.githubusercontent.com/12581295/197405543-8d308808-4ed5-430d-989c-3e4a2a5fda52.png](https://user-images.githubusercontent.com/12581295/197405543-8d308808-4ed5-430d-989c-3e4a2a5fda52.png)


Suppose a user uploads edited image, then a `DynamoDB GetItem` query is fired, which is equal to the number of splits of the p_hash, the result is then consolidated `that involves filtering of results, and removing images with hamming distance higher than the threshold`, and the final result is returned. Let's query the edited image hash, so the flow will look something like-

![https://user-images.githubusercontent.com/12581295/197406267-2ee78bc6-74ab-4bfd-9f01-2150aa4dd81a.png](https://user-images.githubusercontent.com/12581295/197406267-2ee78bc6-74ab-4bfd-9f01-2150aa4dd81a.png)

<hr>

## Summary

So this is how canva scaled their content matching system, using `perceptual hash, hamming distance and multi-index hashing`. They did several iterations to figure out the best possible hash split ratio and hamming distance threshold. You can check for further reading materials in the reference section. 


## Reference

1. [Canva-Scale Reverse Image Search](https://canvatechblog.com/simple-fast-and-scalable-reverse-image-search-using-perceptual-hashes-and-dynamodb-df3007d19934)
2. [Perceptual Hash](https://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html)
3. [Multi-Index Hashing](http://www.cs.toronto.edu/~norouzi/research/papers/multi_index_hashing.pdf)
<hr>