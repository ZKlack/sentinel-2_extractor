from sentinelhub import SHConfig #set config for sentinelhub
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

config = SHConfig()
config.instance_id = os.getenv('INSTANCE_ID')
config.sh_client_id = os.getenv('SH_CLIENT_ID')
config.sh_client_secret = os.getenv('SH_CLIENT_SECRET')

print(config)