import bittensor as bt


def determine_valid_axon_ips(axons):

    # Clear axons that do not have an IP
    axons_with_valid_ip = [axon for axon in axons if axon.ip != "0.0.0.0"]

    # Clear axons with duplicate IP/Port
    axon_ips = set()
    filtered_axons = [axon for axon in axons_with_valid_ip if axon.ip_str() not in axon_ips and not axon_ips.add(axon.ip_str())]

    bt.logging.info(f'Filtered out axons. Original list: {len(axons)}, filtered list: {len(filtered_axons)}')
    
    return filtered_axons

metagraph = bt.metagraph(netuid=14, network="finney")

all_axons = metagraph.axons

valid_axons = determine_valid_axon_ips(all_axons)
