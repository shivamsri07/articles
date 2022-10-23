import cv2
import numpy as np
from scipy import spatial

image = ['/content/edited.png', '/content/original.png']

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
  print(dct_block)
  # caclulate mean of dct block excluding first term i.e, dct(0, 0)
  dct_average = (dct_block.mean() * dct_block.size - dct_block[0, 0]) / (dct_block.size - 1)
  # convert dct block to binary values based on dct_average
  print(dct_average,)
  dct_block[dct_block < dct_average] = 0.0
  dct_block[dct_block != 0] = 1.0
  # store hash value
  print(dct_block, '\n')
  image_hash_dict[name] = hash_array_to_hash_hex(dct_block.flatten())


'''
IMAGE :: /content/edited.png
DCT_BLOCK :: [[ 4058.5938    -585.73267  -3107.709      472.493      -62.369965
    239.6018    -218.52315    178.97751 ]
 [-2074.5068     349.7873    1130.3625    -243.15646    715.48157
    -91.693405    25.04708   -270.88965 ]
 [ -571.2353     196.2815     335.6319    -124.529434   347.04153
   -228.5278    -397.54498     59.019917]
 [  251.54463    -25.603592    -5.897129  -185.9877     -78.21804
    143.77985   -287.6312     306.4981  ]
 [  339.6827    -109.78092   -208.28578    169.1611    -408.341
    136.69104    491.82584   -226.0434  ]
 [   66.3553     -63.01365     68.441635   154.92307   -271.65195
   -163.02634    302.49902     16.425886]
 [ -498.1264      -7.771104   321.98944     38.622704   168.67267
    -22.38166   -116.94272    -75.36159 ]
 [ -163.07031     98.15242    138.92715   -124.6272      99.55658
    -38.301792  -250.01192     77.59943 ]]

DCT_AVG :: -61.355868384951634

UPDATED_DCT_BLOCK :: [[1. 0. 0. 1. 0. 1. 0. 1.]
 [0. 1. 1. 0. 1. 0. 1. 0.]
 [0. 1. 1. 0. 1. 0. 0. 1.]
 [1. 1. 1. 0. 0. 1. 0. 1.]
 [1. 0. 0. 1. 0. 1. 1. 0.]
 [1. 0. 1. 1. 0. 0. 1. 1.]
 [0. 1. 1. 1. 1. 1. 0. 0.]
 [0. 1. 1. 0. 1. 1. 0. 1.]] 

-------------------------------------------

IMAGE :: /content/original.png
DCT_BLOCK :: [[ 1.43720469e+04  1.43470657e+02  2.28976685e+03 -1.27029190e+02
  -1.49693799e+03  2.47372704e+01  6.69355164e+02  5.63741684e+01]
 [ 1.78264221e+02 -2.70461151e+02  1.00373497e+01  3.70773438e+02
  -1.35487595e+02 -3.05458069e+02  1.41361496e+02  2.23229111e+02]
 [ 5.23792114e+02  1.52518509e+02 -7.86987244e+02 -7.55312576e+01
   4.05524872e+02 -6.82418137e+01  1.39228027e+02  1.13239288e+02]
 [-2.55880356e+02 -5.18598824e+01  5.59570801e+02 -1.23979256e+02
  -5.91817322e+02  2.06352020e+02  4.81105927e+02 -5.36144066e+01]
 [ 1.36266144e+02 -1.59700985e+01 -3.22413025e+02  2.53929138e+02
   2.58963989e+02 -3.36629395e+02 -8.39051590e+01  1.51064926e+02]
 [ 5.80471802e+01 -2.96642723e+01 -6.75570536e+00 -8.83268280e+01
   1.07296577e+02  1.20012810e+02 -2.50861298e+02  1.58539200e+01]
 [-1.81686478e+02  5.82787018e+01  1.52642670e+02 -3.05134964e+01
  -9.40486069e+01  1.58320379e+01  4.91617012e+01 -7.26040649e+01]
 [-1.64838272e+02 -3.07389660e+01  2.50290649e+02  1.14199562e+01
  -1.79881256e+02  9.16206932e+00  7.78299561e+01 -2.40081096e+00]]

DCT_AVG :: 34.60683283730159

UPDATED_DCT_BLOCK :: [[1. 1. 1. 0. 0. 0. 1. 1.]
 [1. 0. 0. 1. 0. 0. 1. 1.]
 [1. 1. 0. 0. 1. 0. 1. 1.]
 [0. 0. 1. 0. 0. 1. 1. 0.]
 [1. 0. 0. 1. 1. 0. 0. 1.]
 [1. 0. 0. 0. 1. 1. 0. 0.]
 [0. 1. 1. 0. 0. 0. 1. 0.]
 [0. 0. 1. 0. 0. 0. 1. 0.]] 
'''

print(image_hash_dict)

'''
{
    '/content/edited.png': '0x956a69e596b37c6d', 
    '/content/original.png': '0xe393cb26998c6222'
}
'''
for image_name in image_hash_dict.keys():
  print(f'{image_name} :: {hash_hex_to_hash_array(image_hash_dict[image_name])}')
  distance = spatial.distance.hamming(
    hash_hex_to_hash_array(image_hash_dict[image_name]), 
    hash_hex_to_hash_array(image_hash_dict['/content/edited.png'])
  )
  print("{0:<10} {1}".format(image_name, distance), '\n')

'''
/content/edited.png Hash Array :: [1. 0. 0. 1. 0. 1. 0. 1. 0. 1. 1. 0. 1. 0. 1. 0. 0. 1. 1. 0. 1. 0. 0. 1.
 1. 1. 1. 0. 0. 1. 0. 1. 1. 0. 0. 1. 0. 1. 1. 0. 1. 0. 1. 1. 0. 0. 1. 1.
 0. 1. 1. 1. 1. 1. 0. 0. 0. 1. 1. 0. 1. 1. 0. 1.]
/content/edited.png Hamming Distance 0.0 

/content/original.png Hash Array :: [1. 1. 1. 0. 0. 0. 1. 1. 1. 0. 0. 1. 0. 0. 1. 1. 1. 1. 0. 0. 1. 0. 1. 1.
 0. 0. 1. 0. 0. 1. 1. 0. 1. 0. 0. 1. 1. 0. 0. 1. 1. 0. 0. 0. 1. 1. 0. 0.
 0. 1. 1. 0. 0. 0. 1. 0. 0. 0. 1. 0. 0. 0. 1. 0.]
/content/original.png Hamming Distance 0.578125 

'''