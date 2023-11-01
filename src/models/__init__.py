from src.connect import mongo_client

balance_collection = mongo_client.collection("balance")
nft_collection = mongo_client.collection("nft")
