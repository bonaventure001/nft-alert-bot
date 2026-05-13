import discord
import requests
import time
from datetime import datetime, timedelta

# ============================================
# CONFIGURATION - ADD YOUR DETAILS HERE
# ============================================

DISCORD_TOKEN = "1504004941772095568"  # Replace with your bot token
ETHERSCAN_API_KEY = "WCZT8R2Q51X3AT78UUNFMKTVXQU1P4BN2J"  # Replace with your API key
DISCORD_CHANNEL_NAME = "nft-alerts"  # Name of your Discord channel (without #)

# Alert settings
HOT_CONTRACT_THRESHOLD = 50  # Number of transactions to consider "hot"
TIME_WINDOW_MINUTES = 15  # Check transactions in last 15 minutes
CHECK_INTERVAL = 15  # How often to check (in seconds)

# ============================================
# BOT SETUP
# ============================================

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Keep track of contracts we've already alerted on
alerted_contracts = set()

# ============================================
# ETHERSCAN FUNCTIONS
# ============================================

def get_recent_contracts():
    """Fetch recently created contracts from Etherscan"""
    try:
        url = "https://api.etherscan.io/api"
        params = {
            "module": "account",
            "action": "txlistinternal",
            "address": "0x0000000000000000000000000000000000000000",
            "page": 1,
            "offset": 100,
            "sort": "desc",
            "apikey": ETHERSCAN_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data["status"] == "1":
            return data["result"]
        return []
    except Exception as e:
        print(f"Error fetching contracts: {e}")
        return []

def count_transactions(contract_address, minutes=15):
    """Count transactions for a contract in the last X minutes"""
    try:
        url = "https://api.etherscan.io/api"
        params = {
            "module": "account",
            "action": "txlist",
            "address": contract_address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 10000,
            "sort": "desc",
            "apikey": ETHERSCAN_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data["status"] != "1":
            return 0
        
        # Count transactions in the last X minutes
        cutoff_time = time.time() - (minutes * 60)
        transaction_count = 0
        
        for tx in data["result"]:
            tx_time = int(tx.get("timeStamp", 0))
            if tx_time > cutoff_time:
                transaction_count += 1
            else:
                break  # Since sorted by time, stop counting
        
        return transaction_count
    except Exception as e:
        print(f"Error counting transactions for {contract_address}: {e}")
        return 0

# ============================================
# DISCORD FUNCTIONS
# ============================================

async def send_alert(contract_address, tx_count, etherscan_url):
    """Send alert to Discord channel"""
    try:
        # Find the channel
        channel = discord.utils.get(client.get_all_channels(), name=DISCORD_CHANNEL_NAME)
        
        if channel is None:
            print(f"ERROR: Could not find channel #{DISCORD_CHANNEL_NAME}")
            return
        
        # Create a nice embed message
        embed = discord.Embed(
            title="🔥 HOT NFT MINT DETECTED!",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Contract Address", value=f"`{contract_address}`", inline=False)
        embed.add_field(name="Transactions (15 min)", value=f"**{tx_count}** transactions 🚀", inline=False)
        embed.add_field(name="View on Etherscan", value=f"[Click here]({etherscan_url})", inline=False)
        embed.set_footer(text="NFT Mint Alert Bot")
        
        await channel.send(embed=embed)
        print(f"✅ Alert sent for contract {contract_address}")
    except Exception as e:
        print(f"Error sending Discord alert: {e}")

# ============================================
# MAIN BOT LOGIC
# ============================================

@client.event
async def on_ready():
    """Called when bot connects to Discord"""
    print(f"✅ Bot logged in as {client.user}")
    print(f"📍 Monitoring channel: #{DISCORD_CHANNEL_NAME}")
    print(f"⏱️  Checking every {CHECK_INTERVAL} seconds")
    print(f"🎯 Hot contract threshold: {HOT_CONTRACT_THRESHOLD}+ transactions\n")
    
    # Start the monitoring loop
    await monitor_contracts()

async def monitor_contracts():
    """Main monitoring loop"""
    await client.wait_until_ready()
    
    while True:
        try:
            contracts = get_recent_contracts()
            
            for contract in contracts:
                contract_address = contract.get("contractAddress", "")
                
                # Skip if empty or already alerted
                if not contract_address or contract_address in alerted_contracts:
                    continue
                
                # Count transactions in last 15 minutes
                tx_count = count_transactions(contract_address, TIME_WINDOW_MINUTES)
                
                # If hot, send alert
                if tx_count >= HOT_CONTRACT_THRESHOLD:
                    etherscan_url = f"https://etherscan.io/address/{contract_address}"
                    await send_alert(contract_address, tx_count, etherscan_url)
                    alerted_contracts.add(contract_address)
                    
                    # Keep the set from getting too large
                    if len(alerted_contracts) > 1000:
                        alerted_contracts.clear()
            
            # Wait before checking again
            await asyncio.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            await asyncio.sleep(CHECK_INTERVAL)

# ============================================
# RUN THE BOT
# ============================================

if __name__ == "__main__":
    import asyncio
    
    print("🚀 Starting NFT Mint Alert Bot...\n")
    
    # Validate tokens are set
    if DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("❌ ERROR: You need to add your Discord token!")
        print("   Replace 'YOUR_DISCORD_BOT_TOKEN_HERE' with your actual token")
        exit()
    
    if ETHERSCAN_API_KEY == "YOUR_ETHERSCAN_API_KEY_HERE":
        print("❌ ERROR: You need to add your Etherscan API key!")
        print("   Replace 'YOUR_ETHERSCAN_API_KEY_HERE' with your actual key")
        exit()
    
    try:
        client.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        print("Make sure your Discord token is correct!")
