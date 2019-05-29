import os
import time
import uuid
import hashlib
from random import random


def make_uid(entropy_srcs=None, prefix='2.25.'):
    """Generate a DICOM UID value.
    Follows the advice given at:
    http://www.dclunie.com/medical-image-faq/html/part2.html#UID
    Parameters
    ----------
    entropy_srcs : list of str or None
        List of strings providing the entropy used to generate the UID. If
        None these will be collected from a combination of HW address, time,
        process ID, and randomness.
    prefix : prefix
    """
    # Combine all the entropy sources with a hashing algorithm
    if entropy_srcs is None:
        entropy_srcs = [str(uuid.uuid1()),  # 128-bit from MAC/time/randomness
                        str(os.getpid()),  # Current process ID
                        random().hex()  # 64-bit randomness
                        ]

    #   hash_val = hashlib.sha256(''.join(entropy_srcs))
    entropy_srcs_val = ''.join(entropy_srcs)
    hash_val = hashlib.sha256(str(entropy_srcs_val).encode('utf-8')).hexdigest()
    # Convert this to an int with the maximum available digits
    avail_digits = 64 - len(prefix)
    int_val = int(hash_val, 16) % (10 ** avail_digits)

    return prefix + str(int_val)
