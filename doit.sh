#!/bin/bash

read -p "Hit enter to generate runs (or CTRL-C to exit) if you have updated the variables in this script to match the evaluation round, and that you have supplied the new query variations in ./trec-covid/doc-topics.trec"

TOPICS_COUNT=35
UQVS_PER_TOPIC=10

# Useful Tip: You can list all of the past releases here
# https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/

DATASET_DATE="2020-05-01"

COMM_USE_DATASET="https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/${DATASET_DATE}/comm_use_subset.tar.gz"
NON_COMM_USE_DATASET="https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/${DATASET_DATE}/noncomm_use_subset.tar.gz"
CUSTOM_LICENSE_DATASET="https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/${DATASET_DATE}/custom_license.tar.gz"
BIORXIV_DATASET="https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/${DATASET_DATE}/biorxiv_medrxiv.tar.gz"
ARXIV_DATASET="https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/${DATASET_DATE}/arxiv_medrxiv.tar.gz"
METADATA="https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/${DATASET_DATE}/metadata.csv"

# Using data from https://ir.nist.gov/covidSubmit/data.html
# This list gets used to make sure we only bother indexing documents likely to be assessed
TREC_DOCIDS="https://ir.nist.gov/covidSubmit/data/docids-rnd2.txt"

echo "Downloading corpora and dependencies..."
date

# Download the TREC docids
wget -O docids.txt $TREC_DOCIDS

# Download python libraries with pip
#pip install nested-lookup


TERRIER_LATEST="https://github.com/terrier-org/terrier-core/releases/download/v5.2/terrier-project-5.2-bin.tar.gz"

# Download and untar all corpus and the Terrier tool

wget $METADATA

for file in $COMM_USE_DATASET $NON_COMM_USE_DATASET $CUSTOM_LICENSE_DATASET $BIORXIV_DATASET $ARXIV_DATASET $TERRIER_LATEST
do
    wget $file
    bname=$(basename $file)
    tar xvf $bname
done

echo "Parsing corpus (slowest part)"
date

# Walk the metadata file and convert into TREC text format, prefering PMC instead of PDF
# and ensuring the document will actually be assessed by TREC
# Parser errors involve document ids that are allowed to be assessed, but no PDF or PMC parse exists
# Generates ./trec-covid/doc-text.trec
python parse_corpora.py > parse_errors.txt

# Generate temporal data for each of the documents
# The metadata.csv file is not the cleanest parse, but we will assume it is and unfortunately
# for the relevant documents without a clean parse, they will be punished by assuming they were
# published on 1st of Jan 2020
python gen_days_since.py 

cp generate_runs.py ./terrier-project-5.2/

mkdir -p submission

# We have a collection that can be indexed now, so let's setup Terrier to index the collection 

cp terrier.properties ./terrier-project-5.2/etc
cp collection.spec ./terrier-project-5.2/etc

cd ./terrier-project-5.2/

echo "Indexing the collection"
date

# Index the collection
TERRIER_HEAP_MEM=2500M bin/terrier batchindexing

SYSTEMS_COUNT=16

echo "Generating runs with all of the query variations"
date

# Generate all runs that will be used for double fusion
for m in BB2 BM25 DFR_BM25 DLH DLH13 DPH DFRee Hiemstra_LM IFB2 In_expB2 In_expC2 InL2 LemurTF_IDF LGD PL2 TF_IDF
do
	bin/terrier batchretrieve -w "$m" -s
done

echo "Fuse and apply temporal penalties for old docs, generating submission"
date

python generate_runs.py $TOPICS_COUNT $SYSTEMS_COUNT $UQVS_PER_TOPIC 
cp RMITBFuseM2 ../submission/RMITBFuseM1 
