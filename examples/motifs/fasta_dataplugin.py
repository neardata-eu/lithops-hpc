import random
import lithops
import argparse

from dataplug.fileobject import CloudObject
from dataplug.util import setup_logging
from dataplug.formats.genomics.fasta import FASTA, partition_chunks_strategy

FASTA.debug()
co = CloudObject.new_from_file(FASTA, "/home/abenavid/Documents/lithops-hpc-examples/motifs/data/", "testing.fasta",override=False)

parallel_config = {"verbose": 10}
co.preprocess(parallel_config=parallel_config)
print("this is co:",co)
data_slices = co.partition(partition_chunks_strategy, num_chunks=8)
#data_slices = co.partition(partition_chunks_strategy, num_chunks=2)

