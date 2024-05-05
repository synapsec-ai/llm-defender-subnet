import bittensor as bt
import argparse

parser = argparse.ArgumentParser()

subtensor = bt.subtensor(network="test")

metagraph = subtensor.metagraph(netuid=38)
bt.logging(debug=True)

bt.logging.info("test")

metagraph.sync()
